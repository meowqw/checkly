import {
  api,
  type Account,
  type Category,
  type CreateTransactionBody,
  type TransactionDetail,
} from "@/api/client";
import { ApiError } from "@/api/client";
import { isOnline } from "@/lib/connectivity";
import {
  cacheAccounts,
  cacheCategories,
  cacheTransactions,
  hideEntity,
  invalidateAllTransactionsCache,
  listLocalTransactions,
  mergeAccounts,
  mergeTransactions,
  patchItemCategory,
  putLocalTransaction,
  readAccountsCache,
  readCategoriesCache,
  readTransactionsCache,
  removeLocalTransaction,
} from "@/lib/offline/cache";
import { enqueue, newOpId } from "@/lib/offline/queue";
import { processSyncQueue, warmCacheIfOnline } from "@/lib/offline/sync";
import type { LocalTransaction } from "@/lib/offline/types";
import { notifyAccountsChanged, notifyTransactionsChanged } from "@/lib/data-events";

export { isOnline, processSyncQueue, warmCacheIfOnline };

let accountsInflight: Promise<{ accounts: Account[]; fromCache: boolean }> | null = null;

async function refreshAccountsCacheOnline() {
  if (!isOnline()) return;
  const res = await api.accounts();
  await cacheAccounts(res.accounts);
  notifyAccountsChanged();
}

async function invalidateTransactionsAfterMutation() {
  await invalidateAllTransactionsCache();
  notifyTransactionsChanged();
}

export async function getAccounts(): Promise<{ accounts: Account[]; fromCache: boolean }> {
  if (accountsInflight) return accountsInflight;

  accountsInflight = (async () => {
    if (isOnline()) {
      try {
        const res = await api.accounts();
        await cacheAccounts(res.accounts);
        const merged = await mergeAccounts(res.accounts);
        return { accounts: merged, fromCache: false };
      } catch (err) {
        const cached = await readAccountsCache();
        if (cached) {
          return { accounts: await mergeAccounts(cached), fromCache: true };
        }
        throw err;
      }
    }
    const cached = await readAccountsCache();
    if (!cached) {
      throw new ApiError("Нет кэша счетов. Откройте приложение при интернете.", 0);
    }
    return { accounts: await mergeAccounts(cached), fromCache: true };
  })().finally(() => {
    accountsInflight = null;
  });

  return accountsInflight;
}

export async function createAccount(body: { name: string; balance: number }) {
  if (isOnline()) {
    const res = await api.createAccount(body);
    await refreshAccountsCacheOnline();
    return res;
  }
  const tempId = `local_${newOpId()}`;
  await enqueue({
    id: newOpId(),
    type: "createAccount",
    createdAt: Date.now(),
    tempId,
    body,
  });
  const cached = (await readAccountsCache()) ?? [];
  await cacheAccounts([...cached, { id: tempId, name: body.name, balance: body.balance }]);
  notifyAccountsChanged();
  return { account: { id: tempId, name: body.name, balance: body.balance } };
}

export async function deleteAccount(id: string) {
  if (isOnline()) {
    const res = await api.deleteAccount(id);
    await refreshAccountsCacheOnline();
    return res;
  }
  await hideEntity(id, "account");
  await enqueue({
    id: newOpId(),
    type: "deleteAccount",
    createdAt: Date.now(),
    accountId: id,
  });
  notifyAccountsChanged();
  return { success: true };
}

export async function getCategories(includeChildren = true): Promise<{ categories: Category[]; fromCache: boolean }> {
  if (isOnline()) {
    try {
      const res = await api.categories(includeChildren);
      await cacheCategories(res.categories);
      return { categories: res.categories, fromCache: false };
    } catch (err) {
      const cached = await readCategoriesCache();
      if (cached) return { categories: cached, fromCache: true };
      throw err;
    }
  }
  const cached = await readCategoriesCache();
  if (!cached) {
    throw new ApiError("Нет кэша категорий. Откройте приложение при интернете.", 0);
  }
  return { categories: cached, fromCache: true };
}

async function refreshCategoriesCache() {
  const res = await api.categories(true);
  await cacheCategories(res.categories);
  return res.categories;
}

export async function createCategory(body: import("@/api/client").CreateCategoryBody) {
  if (!isOnline()) {
    throw new ApiError("Создание категорий доступно только онлайн", 0);
  }
  const res = await api.createCategory(body);
  await refreshCategoriesCache();
  return res;
}

export async function updateCategory(id: string, body: import("@/api/client").UpdateCategoryBody) {
  if (!isOnline()) {
    throw new ApiError("Редактирование категорий доступно только онлайн", 0);
  }
  const res = await api.updateCategory(id, body);
  await refreshCategoriesCache();
  return res;
}

export async function deleteCategory(id: string) {
  if (!isOnline()) {
    throw new ApiError("Удаление категорий доступно только онлайн", 0);
  }
  const res = await api.deleteCategory(id);
  await refreshCategoriesCache();
  return res;
}

export async function getTransactions(params?: Record<string, string>) {
  if (isOnline()) {
    try {
      const res = await api.transactions(params);
      await cacheTransactions(params, res.transactions);
      const merged = await mergeTransactions(res.transactions, params);
      return { transactions: merged, fromCache: false };
    } catch (err) {
      const cached = await readTransactionsCache(params);
      if (cached) {
        return { transactions: await mergeTransactions(cached, params), fromCache: true };
      }
      throw err;
    }
  }
  const cached = await readTransactionsCache(params);
  if (!cached) {
    throw new ApiError("Нет кэша операций за этот период. Откройте раздел при интернете.", 0);
  }
  return { transactions: await mergeTransactions(cached, params), fromCache: true };
}

export async function getTransaction(id: string): Promise<{ transaction: TransactionDetail }> {
  if (id.startsWith("local_")) {
    const txs = await listLocalTransactions();
    const found = txs.find((t) => t.id === id);
    if (!found) throw new ApiError("Транзакция не найдена", 404);
    return {
      transaction: {
        id: found.id,
        amount: found.amount,
        source: found.source,
        type: found.type,
        currency: found.currency,
        occurred_at: found.occurred_at,
        comment: found.comment,
        items: found.items,
      },
    };
  }
  if (isOnline()) {
    return api.transaction(id);
  }
  throw new ApiError("Детали операции недоступны offline", 0);
}

export async function createTransaction(body: CreateTransactionBody) {
  if (isOnline()) {
    const res = await api.createTransaction(body);
    await refreshAccountsCacheOnline();
    await invalidateTransactionsAfterMutation();
    return res;
  }
  const tempId = `local_${newOpId()}`;
  const accounts = await readAccountsCache();
  const account = accounts?.find((a) => a.id === body.account_id);
  const localTx: LocalTransaction = {
    id: tempId,
    type: body.type,
    amount: body.amount,
    currency: body.currency,
    occurred_at: body.occurred_at,
    source: "manual",
    comment: body.comment ?? null,
    title: body.comment ?? "Операция",
    account: account ? { id: account.id, name: account.name } : undefined,
    _local: true,
    _pending: true,
  };
  await putLocalTransaction(localTx);
  await enqueue({
    id: newOpId(),
    type: "createTransaction",
    createdAt: Date.now(),
    tempId,
    body,
  });
  notifyTransactionsChanged();
  return { transaction: { id: tempId, amount: body.amount, source: "manual" } };
}

export async function deleteTransaction(id: string) {
  if (isOnline()) {
    const res = await api.deleteTransaction(id);
    await refreshAccountsCacheOnline();
    await invalidateTransactionsAfterMutation();
    return res;
  }
  await hideEntity(id, "transaction");
  if (id.startsWith("local_")) {
    await removeLocalTransaction(id);
  }
  await enqueue({
    id: newOpId(),
    type: "deleteTransaction",
    createdAt: Date.now(),
    transactionId: id,
  });
  notifyTransactionsChanged();
  return { success: true };
}

export async function updateTransactionItem(
  transactionId: string,
  itemId: string,
  body: { category_id: string },
  categoryName?: string
) {
  if (isOnline()) {
    const res = await api.updateTransactionItem(transactionId, itemId, body);
    await invalidateTransactionsAfterMutation();
    return res;
  }
  await enqueue({
    id: newOpId(),
    type: "updateTransactionItem",
    createdAt: Date.now(),
    transactionId,
    itemId,
    categoryId: body.category_id,
  });
  if (categoryName) {
    await patchItemCategory(transactionId, itemId, body.category_id, categoryName);
  }
  notifyTransactionsChanged();
  const detail = await getTransaction(transactionId);
  return { transaction: detail.transaction };
}

/** QR всегда только online */
export async function scanQr(body: { account_id: string; qr: string }) {
  if (!isOnline()) {
    throw new ApiError("Сканирование чеков доступно только при подключении к интернету", 0);
  }
  const res = await api.scanQr(body);
  await refreshAccountsCacheOnline();
  await invalidateTransactionsAfterMutation();
  return res;
}

export async function prefetchCoreData() {
  if (!isOnline()) return;
  await warmCacheIfOnline();
}
