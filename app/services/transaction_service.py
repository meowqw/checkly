"""Сервис транзакций."""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.dates import now_local, to_storage_datetime
from app.core.enums import Currency, TransactionSource, TransactionType
from app.core.exceptions import ExternalServiceError, ForbiddenError, NotFoundError
from app.core.uuid_utils import new_uid
from app.database.models import (
    Account,
    Category,
    Merchant,
    Product,
    ProductAlias,
    Receipt,
    Transaction,
    TransactionItem,
)
from app.dto.accounts import SuccessResponseDTO
from app.dto.receipts import (
    NormalizedItemDTO,
    NormalizerInputItemDTO,
    ProductNormalizerInputDTO,
    ReceiptItemDTO,
    ReceiptProviderInputDTO,
)
from app.dto.transactions import (
    CreateManualTransactionDTO,
    CreateTransactionFromReceiptDTO,
    MerchantBriefDTO,
    TransactionDetailDTO,
    TransactionFilterDTO,
    TransactionItemBriefDTO,
    TransactionResponseDTO,
    TransactionsListResponseDTO,
    UpdateTransactionDTO,
    UpdateTransactionItemDTO,
)
from app.implementations.product_normalizer_factory import get_product_normalizer
from app.implementations.proverkacheka_receipt_provider import ProverkachekaReceiptProvider
from app.interfaces.product_normalizer import ProductNormalizerInterface
from app.interfaces.receipt_provider import ReceiptProviderInterface
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.receipt_repository import ReceiptRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_product_override_repository import UserProductCategoryOverrideRepository
from app.services.category_service import CategoryService
from app.services.product_matching_service import ProductMatchingService
from app.services.transaction_mapper import map_item_to_brief, map_transaction_to_list_item
from app.services.transaction_queries import (
    list_transactions_for_filters,
    resolve_transaction_filters,
)

logger = logging.getLogger(__name__)

# Верхняя граница page size для GET /transactions?limit=
TRANSACTIONS_MAX_LIMIT = 100


class TransactionService:
    def __init__(
        self,
        db: Session,
        receipt_provider: ReceiptProviderInterface | None = None,
        product_normalizer: ProductNormalizerInterface | None = None,
    ):
        self._db = db
        self._transactions = TransactionRepository(db)
        self._accounts = AccountRepository(db)
        self._categories = CategoryRepository(db)
        self._merchants = MerchantRepository(db)
        self._products = ProductRepository(db)
        self._receipts = ReceiptRepository(db)
        self._overrides = UserProductCategoryOverrideRepository(db)
        self._matching = ProductMatchingService(db)
        self._category_service = CategoryService(db)
        self._receipt_provider = receipt_provider or ProverkachekaReceiptProvider()
        self._product_normalizer = product_normalizer or get_product_normalizer()

    def list_transactions(self, filters: TransactionFilterDTO) -> TransactionsListResponseDTO:
        # Без limit — прежнее поведение: весь список по фильтру (фронт не ломаем)
        if filters.limit is None:
            rows = list_transactions_for_filters(
                self._transactions, filters, categories=self._categories
            )
            return TransactionsListResponseDTO(
                transactions=[map_transaction_to_list_item(t) for t in rows]
            )

        limit = min(max(filters.limit, 1), TRANSACTIONS_MAX_LIMIT)
        offset = max(filters.offset, 0)
        paginated = filters.model_copy(update={"limit": limit, "offset": offset})

        resolved = resolve_transaction_filters(
            self._transactions, paginated, categories=self._categories
        )
        total = self._transactions.count_for_user(
            resolved.user_id,
            from_date=resolved.from_date,
            to_date=resolved.to_date,
            transaction_type=resolved.transaction_type,
            account_id=resolved.account_id,
            category_ids=resolved.category_ids,
        )
        rows = list_transactions_for_filters(
            self._transactions, paginated, categories=self._categories
        )
        return TransactionsListResponseDTO(
            transactions=[map_transaction_to_list_item(t) for t in rows],
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(rows) < total,
        )

    def get_transaction(self, user_id: int, transaction_uid: str) -> TransactionResponseDTO:
        transaction = self._get_user_transaction(transaction_uid, user_id)
        return TransactionResponseDTO(transaction=self._to_detail_dto(transaction))

    def create_manual_transaction(self, dto: CreateManualTransactionDTO) -> TransactionResponseDTO:
        account = self._accounts.get_by_uid_for_user(dto.account_uid, dto.user_id)
        if not account:
            raise NotFoundError("Счёт не найден")

        category_id = None
        if dto.category_uid:
            category = self._categories.get_by_uid_for_user(dto.category_uid, dto.user_id)
            if not category:
                raise NotFoundError("Категория не найдена")
            category_id = category.id

        transaction = Transaction(
            uid=new_uid(),
            user_id=dto.user_id,
            account_id=account.id,
            type=dto.type.value,
            amount=dto.amount,
            currency=dto.currency.value,
            occurred_at=to_storage_datetime(dto.occurred_at, dto.timezone),
            source=TransactionSource.MANUAL.value,
            comment=dto.comment,
        )
        self._transactions.create(transaction)

        item = TransactionItem(
            uid=new_uid(),
            transaction_id=transaction.id,
            category_id=category_id,
            raw_name=dto.comment or "Ручная операция",
            amount=dto.amount,
        )
        self._transactions.create_item(item)

        self._adjust_account_balance(account.id, dto.type, dto.amount)
        self._db.commit()
        self._db.refresh(transaction)

        return TransactionResponseDTO(
            transaction=TransactionDetailDTO(
                id=transaction.uid,
                amount=transaction.amount,
                source=transaction.source,
            )
        )

    def update_transaction(self, dto: UpdateTransactionDTO) -> TransactionResponseDTO:
        transaction = self._get_user_transaction(dto.transaction_uid, dto.user_id)
        if transaction.source != TransactionSource.MANUAL.value:
            raise ForbiddenError("Можно редактировать только ручные транзакции")

        if dto.amount is not None and dto.amount != transaction.amount:
            delta = dto.amount - transaction.amount
            self._apply_balance_delta(
                transaction.account_id, TransactionType(transaction.type), delta
            )
            transaction.amount = dto.amount
            if transaction.items:
                transaction.items[0].amount = dto.amount

        if dto.category_uid is not None:
            category = self._categories.get_by_uid_for_user(dto.category_uid, dto.user_id)
            if not category:
                raise NotFoundError("Категория не найдена")
            if transaction.items:
                transaction.items[0].category_id = category.id

        if dto.comment is not None:
            transaction.comment = dto.comment

        self._db.commit()
        self._db.refresh(transaction)
        return TransactionResponseDTO(
            transaction=TransactionDetailDTO(
                id=transaction.uid,
                amount=transaction.amount,
                comment=transaction.comment,
                source=transaction.source,
            )
        )

    def update_transaction_item(self, dto: UpdateTransactionItemDTO) -> TransactionResponseDTO:
        transaction = self._get_user_transaction(dto.transaction_uid, dto.user_id)
        item = self._transactions.get_item_by_uid_for_user(
            dto.item_uid, dto.transaction_uid, dto.user_id
        )
        if not item:
            raise NotFoundError("Позиция не найдена")

        category = self._categories.get_by_uid_for_user(dto.category_uid, dto.user_id)
        if not category:
            raise NotFoundError("Категория не найдена")

        item.category_id = category.id
        if item.product_id:
            self._overrides.upsert(dto.user_id, item.product_id, category.id)

        self._db.commit()
        self._db.refresh(transaction)
        return TransactionResponseDTO(transaction=self._to_detail_dto(transaction))

    def delete_transaction(self, user_id: int, transaction_uid: str) -> SuccessResponseDTO:
        transaction = self._get_user_transaction(transaction_uid, user_id)
        self._revert_transaction_balance(transaction)
        self._transactions.delete(transaction)
        self._db.commit()
        return SuccessResponseDTO()

    def create_transaction_from_receipt(
        self, dto: CreateTransactionFromReceiptDTO
    ) -> TransactionResponseDTO:
        account = self._accounts.get_by_uid_for_user(dto.account_uid, dto.user_id)
        if not account:
            raise NotFoundError("Счёт не найден")

        receipt_data = self._receipt_provider.get_receipt_by_qr(
            ReceiptProviderInputDTO(qr=dto.qr)
        )

        merchant = self._find_or_create_merchant(receipt_data.merchant.name, receipt_data.merchant.inn, receipt_data.merchant.address)

        occurred_at = receipt_data.receipt.receipt_datetime or now_local(dto.timezone)
        if receipt_data.receipt.receipt_datetime:
            occurred_at = to_storage_datetime(receipt_data.receipt.receipt_datetime, dto.timezone)
        transaction = Transaction(
            uid=new_uid(),
            user_id=dto.user_id,
            account_id=account.id,
            merchant_id=merchant.id,
            type=TransactionType.EXPENSE.value,
            amount=receipt_data.receipt.total_sum,
            currency=Currency.RUB.value,
            occurred_at=occurred_at,
            source=TransactionSource.QR_RECEIPT.value,
        )
        self._transactions.create(transaction)

        receipt = Receipt(
            uid=new_uid(),
            transaction_id=transaction.id,
            fiscal_drive_number=receipt_data.receipt.fiscal_drive_number,
            fiscal_document_number=receipt_data.receipt.fiscal_document_number,
            fiscal_sign=receipt_data.receipt.fiscal_sign,
            operation_type=receipt_data.receipt.operation_type,
            receipt_datetime=receipt_data.receipt.receipt_datetime,
            total_sum=receipt_data.receipt.total_sum,
            raw_qr=dto.qr,
            raw_json=receipt_data.raw,
        )
        self._receipts.create(receipt)

        unknown_items = []
        known_mappings: list[tuple] = []

        for item in receipt_data.items:
            product = self._matching.find_existing_product(
                raw_name=item.raw_name,
                merchant_id=merchant.id,
                gtin=item.gtin,
            )
            if product:
                known_mappings.append((item, product))
            else:
                unknown_items.append(item)

        normalized_by_raw = self._normalize_unknown_items(merchant.name, unknown_items)

        response_items: list[TransactionItemBriefDTO] = []
        override_map = self._overrides.get_category_ids_for_products(
            dto.user_id, [product.id for _, product in known_mappings]
        )
        category_cache: dict[int, Category] = {}

        for item, product in known_mappings:
            category_id = override_map.get(product.id) or product.category_id
            tx_item = self._create_transaction_item(
                transaction_id=transaction.id,
                raw_name=item.raw_name,
                quantity=item.quantity,
                price=item.price,
                amount=item.amount,
                product=product,
                category_id=category_id,
            )
            cat = self._category_for_brief(category_id, product.category, category_cache)
            response_items.append(map_item_to_brief(tx_item, cat))

        created_products: dict[str, Product] = {}

        for item in unknown_items:
            norm = normalized_by_raw.get(item.raw_name)
            category = None
            product = created_products.get(item.raw_name)
            if norm and product is None:
                category = self._category_service.find_system_for_receipt(
                    norm.category, norm.subcategory
                )
                product = Product(
                    uid=new_uid(),
                    name=norm.product_name,
                    normalized_name=norm.normalized_name,
                    brand=norm.brand,
                    gtin=item.gtin,
                    category_id=category.id if category else None,
                )
                self._products.create_product(product)
                alias = ProductAlias(
                    uid=new_uid(),
                    product_id=product.id,
                    merchant_id=merchant.id,
                    raw_name=item.raw_name,
                    normalized_name=norm.normalized_name,
                    confidence=norm.confidence,
                )
                self._products.create_alias(alias)
                created_products[item.raw_name] = product
            elif norm and product is not None:
                category = self._db.get(Category, product.category_id) if product.category_id else None

            tx_item = self._create_transaction_item(
                transaction_id=transaction.id,
                raw_name=item.raw_name,
                quantity=item.quantity,
                price=item.price,
                amount=item.amount,
                product=product,
                category_id=category.id if category else None,
            )
            response_items.append(map_item_to_brief(tx_item, category))

        self._adjust_account_balance(account.id, TransactionType.EXPENSE, receipt_data.receipt.total_sum)
        self._db.commit()
        self._db.refresh(transaction)

        detail = TransactionDetailDTO(
            id=transaction.uid,
            amount=transaction.amount,
            source=transaction.source,
            merchant=MerchantBriefDTO(name=merchant.name),
            items=response_items,
        )
        return TransactionResponseDTO(transaction=detail)

    def _normalize_unknown_items(
        self, merchant_name: str, unknown_items: list[ReceiptItemDTO]
    ) -> dict[str, NormalizedItemDTO]:
        if not unknown_items:
            return {}

        try:
            result = self._product_normalizer.normalize_items(
                ProductNormalizerInputDTO(
                    merchant=merchant_name,
                    items=[
                        NormalizerInputItemDTO(
                            raw_name=i.raw_name, price=i.price, quantity=i.quantity
                        )
                        for i in unknown_items
                    ],
                )
            )
            out: dict[str, NormalizedItemDTO] = {}
            for i, item in enumerate(unknown_items):
                norm = next(
                    (n for n in result.items if n.raw_name == item.raw_name),
                    result.items[i] if i < len(result.items) else None,
                )
                if norm:
                    out[item.raw_name] = norm.model_copy(update={"raw_name": item.raw_name})
            return out
        except ExternalServiceError as exc:
            logger.warning(
                "AI-нормализация недоступна (%s), сохраняем позиции как в чеке",
                exc.message,
            )
            return {
                item.raw_name: NormalizedItemDTO(
                    raw_name=item.raw_name,
                    normalized_name=item.raw_name,
                    product_name=item.raw_name,
                    brand=None,
                    category="Прочее",
                    subcategory=None,
                    confidence=0.0,
                )
                for item in unknown_items
            }

    def _resolve_category_for_user(self, user_id: int, product: Product) -> int | None:
        override_id = self._overrides.get_category_id(user_id, product.id)
        if override_id:
            return override_id
        return product.category_id

    def _find_or_create_merchant(
        self, name: str, inn: str | None, address: str | None
    ) -> Merchant:
        merchant = self._merchants.find_by_inn(inn) if inn else None
        if not merchant:
            merchant = self._merchants.find_by_name(name)
        if not merchant:
            merchant = Merchant(uid=new_uid(), name=name, inn=inn, address=address)
            self._merchants.create(merchant)
        return merchant

    def _create_transaction_item(
        self,
        transaction_id: int,
        raw_name: str,
        quantity: int | None,
        price: int | None,
        amount: int,
        product: Product | None,
        category_id: int | None,
    ) -> TransactionItem:
        item = TransactionItem(
            uid=new_uid(),
            transaction_id=transaction_id,
            product_id=product.id if product else None,
            category_id=category_id,
            raw_name=raw_name,
            quantity=quantity,
            price=price,
            amount=amount,
        )
        return self._transactions.create_item(item)

    def _adjust_account_balance(
        self, account_id: int, transaction_type: TransactionType, amount: int
    ) -> None:
        self._apply_balance_delta(account_id, transaction_type, amount)

    def _apply_balance_delta(
        self, account_id: int, transaction_type: TransactionType, delta: int
    ) -> None:
        if delta == 0:
            return
        acc = self._db.get(Account, account_id)
        if not acc:
            return
        if transaction_type == TransactionType.EXPENSE:
            acc.balance -= delta
        else:
            acc.balance += delta

    def _revert_transaction_balance(self, transaction: Transaction) -> None:
        tx_type = TransactionType(transaction.type)
        reverse_type = (
            TransactionType.INCOME
            if tx_type == TransactionType.EXPENSE
            else TransactionType.EXPENSE
        )
        self._adjust_account_balance(transaction.account_id, reverse_type, transaction.amount)

    def _category_for_brief(
        self,
        category_id: int | None,
        fallback: Category | None,
        cache: dict[int, Category],
    ) -> Category | None:
        if not category_id:
            return fallback
        if fallback and fallback.id == category_id:
            return fallback
        if category_id not in cache:
            cache[category_id] = self._db.get(Category, category_id)
        return cache[category_id] or fallback

    def _get_user_transaction(self, uid: str, user_id: int) -> Transaction:
        transaction = self._transactions.get_by_uid_for_user(uid, user_id)
        if not transaction:
            raise NotFoundError("Транзакция не найдена")
        return transaction

    def _to_detail_dto(self, transaction: Transaction) -> TransactionDetailDTO:
        merchant = None
        if transaction.merchant:
            merchant = MerchantBriefDTO(
                id=transaction.merchant.uid,
                name=transaction.merchant.name,
            )
        items = [map_item_to_brief(item) for item in transaction.items]
        return TransactionDetailDTO(
            id=transaction.uid,
            amount=transaction.amount,
            source=transaction.source,
            type=transaction.type,
            currency=transaction.currency,
            occurred_at=transaction.occurred_at,
            comment=transaction.comment,
            merchant=merchant,
            items=items,
        )
