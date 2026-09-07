import {
  api,
  getUser,
  type Account,
  type Category,
  type CreateTransactionBody,
  type PeriodStats,
  type TransactionDetail,
} from "@/api/client";
import { ApiError } from "@/api/client";
import { isOnline } from "@/lib/connectivity";
import {
  cacheAccounts,
  cacheCategories,
  cacheTags,
  cacheStats,
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
  readTagsCache,
  readStatsCache,
  readTransactionsCache,
  removeLocalTransaction,
  transactionsCacheKey,
  statsCacheKey,
} from "@/lib/offline/cache";
import { buildStatsFromTransactions } from "@/lib/stats";
import { enqueue, newOpId } from "@/lib/offline/queue";
import { processSyncQueue, warmCacheIfOnline } from "@/lib/offline/sync";
import type { LocalTransaction } from "@/lib/offline/types";
import { notifyAccountsChanged, notifyCategoriesChanged, notifyTransactionsChanged } from "@/lib/data-events";

export type CacheLoadOptions = {
  /** Не запускать фоновую проверку с бэкендом (после notify*Changed). */
  skipRevalidate?: boolean;
};

export { isOnline, processSyncQueue, warmCacheIfOnline };

export type CacheFirstResult<T> = {
  data: T;
  fromCache: boolean;
  /** Завершится после фоновой проверки актуальности с бэкендом. */
  fresh?: Promise<void>;
};

let accountsInflight: Promise<{ accounts: Account[]; fromCache: boolean; fresh?: Promise<void> }> | null =
  null;
let accountsRevalidateInflight: Promise<void> | null = null;
const transactionsInflight = new Map<
  string,
  Promise<{
    transactions: Awaited<ReturnType<typeof mergeTransactions>>;
    fromCache: boolean;
    fresh?: Promise<void>;
    total?: number;
    limit?: number;
    offset?: number;
    has_more?: boolean;
  }>
>();
const transactionsRevalidateInflight = new Map<string, Promise<void>>();
let categoriesInflight: Promise<{ categories: Category[]; fromCache: boolean; fresh?: Promise<void> }> | null =
  null;
let categoriesRevalidateInflight: Promise<void> | null = null;
const statsInflight = new Map<
  string,
  Promise<{ stats: PeriodStats; fromCache: boolean; fresh?: Promise<void> }>
>();
const statsRevalidateInflight = new Map<string, Promise<void>>();

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

async function revalidateAccounts(): Promise<void> {
  if (!isOnline()) return;
  if (accountsRevalidateInflight) return accountsRevalidateInflight;

  accountsRevalidateInflight = (async () => {
    try {
      const res = await api.accounts();
      await cacheAccounts(res.accounts);
      notifyAccountsChanged();
    } catch {
      // оставляем кэш
    } finally {
      accountsRevalidateInflight = null;
    }
  })();

  return accountsRevalidateInflight;
}

async function revalidateCategories(): Promise<void> {
  if (!isOnline()) return;
  if (categoriesRevalidateInflight) return categoriesRevalidateInflight;

  categoriesRevalidateInflight = (async () => {
    try {
      const res = await api.categories();
      await cacheCategories(res.categories);
      notifyCategoriesChanged();
    } catch {
      // оставляем кэш
    } finally {
      categoriesRevalidateInflight = null;
    }
  })();

  return categoriesRevalidateInflight;
}

async function revalidateStats(params?: Record<string, string>): Promise<void> {
  if (!isOnline()) return;
  const key = statsCacheKey(params);
  if (statsRevalidateInflight.has(key)) {
    return statsRevalidateInflight.get(key)!;
  }

  const task = (async () => {
    try {
      const res = await api.stats(params);
      await cacheStats(params, res);
      notifyTransactionsChanged();
    } catch {
      // оставляем кэш
    } finally {
      statsRevalidateInflight.delete(key);
    }
  })();

  statsRevalidateInflight.set(key, task);
  return task;
}

async function buildStatsFallback(params?: Record<string, string>): Promise<PeriodStats> {
  const cachedTx = await readTransactionsCache(params);
  const cachedCats = await readCategoriesCache();
  if (cachedTx && cachedCats) {
    return buildStatsFromTransactions(
      await mergeTransactions(cachedTx, params),
      cachedCats
    );
  }
  const [txRes, catRes] = await Promise.all([
    getTransactions(params, { skipRevalidate: true }),
    getCategories({ skipRevalidate: true }),
  ]);
  return buildStatsFromTransactions(txRes.transactions, catRes.categories);
}

async function revalidateTransactions(params?: Record<string, string>): Promise<void> {
  if (!isOnline()) return;
  const key = transactionsCacheKey(params);
  if (transactionsRevalidateInflight.has(key)) {
    return transactionsRevalidateInflight.get(key)!;
  }

  const task = (async () => {
    try {
      const res = await api.transactions(params);
      await cacheTransactions(params, res.transactions);
      notifyTransactionsChanged();
    } catch {
      // оставляем кэш
    } finally {
      transactionsRevalidateInflight.delete(key);
    }
  })();

  transactionsRevalidateInflight.set(key, task);
  return task;
}

export async function getAccounts(opts?: CacheLoadOptions): Promise<{
  accounts: Account[];
  fromCache: boolean;
  fresh?: Promise<void>;
}> {
  if (accountsInflight) return accountsInflight;

  accountsInflight = (async () => {
    const cached = await readAccountsCache();
    if (cached) {
      return {
        accounts: await mergeAccounts(cached),
        fromCache: true,
        fresh: !opts?.skipRevalidate ? revalidateAccounts() : undefined,
      };
    }

    if (!isOnline()) {
      throw new ApiError("Нет кэша счетов. Откройте приложение при интернете.", 0);
    }

    const res = await api.accounts();
    await cacheAccounts(res.accounts);
    return { accounts: await mergeAccounts(res.accounts), fromCache: false };
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
  const user = getUser();
  const cached = (await readAccountsCache()) ?? [];
  const optimistic: Account = {
    id: tempId,
    name: body.name,
    balance: body.balance,
    members: user
      ? [{ id: user.id, login: user.login, role: "owner" }]
      : [],
  };
  await cacheAccounts([...cached, optimistic]);
  notifyAccountsChanged();
  return { account: optimistic };
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

/** Инвайт и join — только online. */
export async function createAccountInvite(accountId: string) {
  if (!isOnline()) {
    throw new ApiError("Приглашения доступны только онлайн", 0);
  }
  return api.createAccountInvite(accountId);
}

export async function joinAccount(token: string) {
  if (!isOnline()) {
    throw new ApiError("Присоединение к счёту доступно только онлайн", 0);
  }
  const res = await api.joinAccount({ token: token.trim() });
  await refreshAccountsCacheOnline();
  return res;
}

/** @deprecated используйте getCategories — уже cache-first */
export async function peekCategories(): Promise<Category[] | null> {
  return readCategoriesCache();
}

/** @deprecated используйте getTransactions — уже cache-first */
export async function peekTransactions(params?: Record<string, string>) {
  const cached = await readTransactionsCache(params);
  if (!cached) return null;
  return mergeTransactions(cached, params);
}

export async function getCategories(opts?: CacheLoadOptions): Promise<{
  categories: Category[];
  fromCache: boolean;
  fresh?: Promise<void>;
}> {
  if (categoriesInflight) return categoriesInflight;

  categoriesInflight = (async () => {
    const cached = await readCategoriesCache();
    if (cached) {
      return {
        categories: cached,
        fromCache: true,
        fresh: !opts?.skipRevalidate ? revalidateCategories() : undefined,
      };
    }

    if (!isOnline()) {
      throw new ApiError("Нет кэша категорий. Откройте приложение при интернете.", 0);
    }

    const res = await api.categories();
    await cacheCategories(res.categories);
    return { categories: res.categories, fromCache: false };
  })().finally(() => {
    categoriesInflight = null;
  });

  return categoriesInflight;
}

async function refreshCategoriesCache() {
  const res = await api.categories();
  await cacheCategories(res.categories);
  return res.categories;
}

export async function createCategory(body: import("@/api/client").CreateCategoryBody) {
  if (!isOnline()) {
    throw new ApiError("Создание категорий доступно только онлайн", 0);
  }
  const res = await api.createCategory(body);
  await refreshCategoriesCache();
  notifyCategoriesChanged();
  return res;
}

export async function updateCategory(id: string, body: import("@/api/client").UpdateCategoryBody) {
  if (!isOnline()) {
    throw new ApiError("Редактирование категорий доступно только онлайн", 0);
  }
  const res = await api.updateCategory(id, body);
  await refreshCategoriesCache();
  notifyCategoriesChanged();
  return res;
}

export async function deleteCategory(id: string) {
  if (!isOnline()) {
    throw new ApiError("Удаление категорий доступно только онлайн", 0);
  }
  const res = await api.deleteCategory(id);
  await refreshCategoriesCache();
  notifyCategoriesChanged();
  return res;
}

let tagsInflight: Promise<{ tags: import("@/api/client").Tag[]; fromCache: boolean; fresh?: Promise<void> }> | null =
  null;
let tagsRevalidateInflight: Promise<void> | null = null;

async function revalidateTags(): Promise<void> {
  if (!isOnline()) return;
  if (tagsRevalidateInflight) return tagsRevalidateInflight;
  tagsRevalidateInflight = (async () => {
    try {
      const res = await api.tags();
      await cacheTags(res.tags);
      notifyCategoriesChanged();
    } catch {
      // оставляем кэш
    } finally {
      tagsRevalidateInflight = null;
    }
  })();
  return tagsRevalidateInflight;
}

export async function getTags(opts?: CacheLoadOptions): Promise<{
  tags: import("@/api/client").Tag[];
  fromCache: boolean;
  fresh?: Promise<void>;
}> {
  if (tagsInflight) return tagsInflight;
  tagsInflight = (async () => {
    const cached = await readTagsCache();
    if (cached) {
      return {
        tags: cached,
        fromCache: true,
        fresh: !opts?.skipRevalidate ? revalidateTags() : undefined,
      };
    }
    if (!isOnline()) {
      throw new ApiError("Нет кэша тегов. Откройте приложение при интернете.", 0);
    }
    const res = await api.tags();
    await cacheTags(res.tags);
    return { tags: res.tags, fromCache: false };
  })().finally(() => {
    tagsInflight = null;
  });
  return tagsInflight;
}

export async function createTag(body: import("@/api/client").CreateTagBody) {
  if (!isOnline()) {
    throw new ApiError("Создание тегов доступно только онлайн", 0);
  }
  const res = await api.createTag(body);
  const list = await api.tags();
  await cacheTags(list.tags);
  notifyCategoriesChanged();
  return res;
}

export async function deleteTag(id: string) {
  if (!isOnline()) {
    throw new ApiError("Удаление тегов доступно только онлайн", 0);
  }
  const res = await api.deleteTag(id);
  const list = await api.tags();
  await cacheTags(list.tags);
  notifyCategoriesChanged();
  return res;
}

export async function getTransactions(params?: Record<string, string>, opts?: CacheLoadOptions) {
  const key = transactionsCacheKey(params);
  if (transactionsInflight.has(key)) return transactionsInflight.get(key)!;

  const task = (async () => {
    const cached = await readTransactionsCache(params);
    if (cached) {
      return {
        transactions: await mergeTransactions(cached, params),
        fromCache: true,
        fresh: !opts?.skipRevalidate ? revalidateTransactions(params) : undefined,
      };
    }

    if (!isOnline()) {
      // Offline: пробуем кэш без limit/offset (полная выборка за период)
      const withoutPage = stripPaginationParams(params);
      if (withoutPage !== params) {
        const fullCached = await readTransactionsCache(withoutPage);
        if (fullCached) {
          return {
            transactions: await mergeTransactions(fullCached, params),
            fromCache: true,
          };
        }
      }
      throw new ApiError("Нет кэша операций за этот период. Откройте раздел при интернете.", 0);
    }

    const res = await api.transactions(params);
    await cacheTransactions(params, res.transactions);
    return {
      transactions: await mergeTransactions(res.transactions, params),
      fromCache: false,
      total: res.total,
      limit: res.limit,
      offset: res.offset,
      has_more: res.has_more,
    };
  })().finally(() => {
    transactionsInflight.delete(key);
  });

  transactionsInflight.set(key, task);
  return task;
}

function stripPaginationParams(
  params?: Record<string, string>
): Record<string, string> | undefined {
  if (!params) return params;
  if (!("limit" in params) && !("offset" in params)) return params;
  const next = { ...params };
  delete next.limit;
  delete next.offset;
  return next;
}

export async function getStats(params?: Record<string, string>, opts?: CacheLoadOptions) {
  const key = statsCacheKey(params);
  if (statsInflight.has(key)) return statsInflight.get(key)!;

  const task = (async () => {
    const cached = await readStatsCache(params);
    if (cached) {
      return {
        stats: cached,
        fromCache: true,
        fresh: !opts?.skipRevalidate ? revalidateStats(params) : undefined,
      };
    }

    if (!isOnline()) {
      try {
        return {
          stats: await buildStatsFallback(params),
          fromCache: true,
        };
      } catch {
        throw new ApiError("Нет кэша статистики за этот период. Откройте главную при интернете.", 0);
      }
    }

    const res = await api.stats(params);
    await cacheStats(params, res);
    return {
      stats: res,
      fromCache: false,
    };
  })().finally(() => {
    statsInflight.delete(key);
  });

  statsInflight.set(key, task);
  return task;
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
  body: { category_id: string; tag_ids?: string[] },
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
