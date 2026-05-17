"""Провайдер чеков через proverkacheka.com."""
import json
import logging
from datetime import datetime
from urllib.parse import parse_qs

import requests

from app.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.dto.receipts import (
    ReceiptItemDTO,
    ReceiptMerchantDTO,
    ReceiptMetaDTO,
    ReceiptProviderInputDTO,
    ReceiptProviderOutputDTO,
)
from app.interfaces.receipt_provider import ReceiptProviderInterface

logger = logging.getLogger(__name__)

PROVERKACHEKA_URL = "https://proverkacheka.com/api/v1/check/get"


class ProverkachekaReceiptProvider(ReceiptProviderInterface):
    def get_receipt_by_qr(self, dto: ReceiptProviderInputDTO) -> ReceiptProviderOutputDTO:
        settings = get_settings()
        if not settings.proverkacheka_token:
            raise ExternalServiceError("PROVERKACHEKA_TOKEN не задан")

        try:
            response = requests.post(
                PROVERKACHEKA_URL,
                json={"token": settings.proverkacheka_token, "qrraw": dto.qr},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.exception("Ошибка запроса к proverkacheka.com")
            raise ExternalServiceError("Не удалось получить данные чека") from exc

        self._validate_api_response(payload)

        receipt_json = self._extract_receipt_json(payload) or {}
        qr_params = self._parse_qr_params(dto.qr)
        if not self._looks_like_receipt(receipt_json) and not qr_params.get("s"):
            logger.warning("Пустой json чека, ответ API: %s", str(payload)[:500])
            raise ExternalServiceError(
                "Не удалось разобрать чек. Проверьте PROVERKACHEKA_TOKEN, лимит API или QR-строку."
            )

        return self._map_response(receipt_json, payload, dto.qr)

    def _validate_api_response(self, payload: dict) -> None:
        code = payload.get("code")
        if code is None:
            return
        if code in (1, "1", True):
            return
        data = payload.get("data")
        if isinstance(data, str) and data.strip():
            raise ExternalServiceError(data.strip())
        data_msg = data.get("message") if isinstance(data, dict) else None
        message = payload.get("message") or payload.get("error") or data_msg
        if code in (401, "401") and not message:
            message = (
                "Неверный PROVERKACHEKA_TOKEN. Укажите токен в .env в корне проекта "
                "и пересоздайте контейнер: docker compose up -d --force-recreate app"
            )
        raise ExternalServiceError(
            str(message)
            if message
            else "Сервис не вернул данные чека (проверьте токен и лимит API)"
        )

    def _extract_receipt_json(self, payload: dict) -> dict | None:
        candidates: list[dict] = []

        def add(obj: object) -> None:
            if isinstance(obj, dict):
                candidates.append(obj)
            elif isinstance(obj, str):
                try:
                    parsed = json.loads(obj)
                    if isinstance(parsed, dict):
                        candidates.append(parsed)
                except json.JSONDecodeError:
                    pass

        add(payload.get("json"))
        data = payload.get("data")
        add(data)
        if isinstance(data, dict):
            add(data.get("json"))
            for key in ("ticket", "document", "content", "receipt"):
                add(data.get(key))

        for candidate in candidates:
            if self._looks_like_receipt(candidate):
                return candidate
            for key in ("ticket", "document", "content", "receipt", "json"):
                inner = candidate.get(key)
                if isinstance(inner, dict) and self._looks_like_receipt(inner):
                    return inner

        return None

    def _looks_like_receipt(self, data: dict) -> bool:
        return any(
            key in data
            for key in ("totalSum", "total_sum", "items", "user", "retailPlace", "userInn")
        )

    def _parse_qr_params(self, qr: str) -> dict[str, str]:
        normalized = qr.strip()
        if "?" in normalized:
            normalized = normalized.split("?", 1)[1]
        parsed = parse_qs(normalized, keep_blank_values=True)
        return {k: (v[0] if v else "") for k, v in parsed.items()}

    def _to_kopecks(self, value: object | None, *, from_qr_sum: bool = False) -> int:
        if value is None or value == "":
            return 0
        s = str(value).strip().replace(",", ".")
        num = float(s)
        if "." in s or from_qr_sum:
            return int(round(num * 100))
        return int(num)

    def _map_response(self, receipt: dict, raw: dict, qr_raw: str) -> ReceiptProviderOutputDTO:
        qr_params = self._parse_qr_params(qr_raw)

        merchant_name = (
            receipt.get("user")
            or receipt.get("retailPlace")
            or receipt.get("retailPlaceAddress")
            or receipt.get("name")
            or receipt.get("organizationName")
            or receipt.get("seller")
        )
        if not merchant_name:
            merchant_name = "Неизвестный магазин"

        total_sum = self._to_kopecks(receipt.get("totalSum") or receipt.get("total_sum"))
        if total_sum <= 0 and qr_params.get("s"):
            total_sum = self._to_kopecks(qr_params["s"], from_qr_sum=True)

        receipt_datetime = self._parse_datetime(receipt.get("dateTime"))
        if not receipt_datetime and qr_params.get("t"):
            receipt_datetime = self._parse_datetime(qr_params["t"])

        receipt_meta = ReceiptMetaDTO(
            fiscal_drive_number=str(
                receipt.get("fiscalDriveNumber") or qr_params.get("fn") or ""
            )
            or None,
            fiscal_document_number=str(
                receipt.get("fiscalDocumentNumber") or qr_params.get("i") or ""
            )
            or None,
            fiscal_sign=str(receipt.get("fiscalSign") or qr_params.get("fp") or "") or None,
            operation_type=receipt.get("operationType"),
            receipt_datetime=receipt_datetime,
            total_sum=total_sum,
        )

        items = [self._map_item(item) for item in receipt.get("items") or []]
        items_total = sum(i.amount for i in items)

        if total_sum <= 0 and items_total > 0:
            total_sum = items_total

        if not items and total_sum > 0:
            items = [
                ReceiptItemDTO(
                    raw_name="Покупка",
                    price=total_sum,
                    quantity=1,
                    amount=total_sum,
                    gtin=None,
                )
            ]

        if total_sum <= 0:
            raise ExternalServiceError(
                "Сумма чека не определена. Проверьте QR-строку или ответ сервиса proverkacheka."
            )

        return ReceiptProviderOutputDTO(
            raw=raw,
            merchant=ReceiptMerchantDTO(
                name=str(merchant_name),
                inn=receipt.get("userInn") or qr_params.get("inn"),
                address=receipt.get("retailPlaceAddress") or receipt.get("address"),
            ),
            receipt=receipt_meta,
            items=items,
        )

    def _map_item(self, item: dict) -> ReceiptItemDTO:
        raw_name = item.get("name") or item.get("productName") or item.get("text") or "Товар"
        quantity_raw = item.get("quantity") or 1
        quantity = int(float(quantity_raw))
        if quantity <= 0:
            quantity = 1

        price = self._to_kopecks(item.get("price"))
        amount = self._to_kopecks(item.get("sum") or item.get("amount"))
        if amount <= 0 and price > 0:
            amount = price * max(quantity, 1)
        if amount <= 0 and price > 0:
            amount = price

        gtin = None
        product_code = item.get("productCodeNew") or item.get("productCode")
        if isinstance(product_code, dict):
            gtin = product_code.get("km") or product_code.get("gtin")
        elif isinstance(product_code, str):
            gtin = product_code

        return ReceiptItemDTO(
            raw_name=raw_name,
            price=price,
            quantity=quantity,
            amount=amount,
            gtin=gtin,
        )

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        cleaned = str(value).strip().replace("Z", "")
        for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dT%H%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(cleaned[:19], fmt)
            except ValueError:
                continue
        return None
