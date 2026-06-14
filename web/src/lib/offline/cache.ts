import type { Account, Category, Transaction } from "@/api/client";
import { parseRangeBound, parseApiDateTime } from "@/lib/dates";
import { getDb } from "@/lib/offline/db";
import type { CacheEntry, LocalTransaction } from "@/lib/offline/types";

export async function setCache<T>(key: string, data: T): Promise<void> {
  const db = await getDb();
  const entry: CacheEntry<T> = { data, fetchedAt: Date.now() };
  await db.put("cache", entry, key);
}

export async function getCache<T>(key: string): Promise<T | null> {
  const db = await getDb();
  const entry = await db.get("cache", key);
  return entry ? (entry.data as T) : null;
}

export async function getCacheEntry<T>(key: string): Promise<CacheEntry<T> | null> {
  const db = await getDb();
  const entry = await db.get("cache", key);
  return entry ? (entry as CacheEntry<T>) : null;
}

const ACCOUNTS_KEY = "accounts";
const CATEGORIES_KEY = "categories";

export function transactionsCacheKey(params?: Record<string, string>): string {
  return `transactions:${JSON.stringify(params ?? {})}`;
}

export async function cacheAccounts(accounts: Account[]) {
  await setCache(ACCOUNTS_KEY, accounts);
}

export async function readAccountsCache(): Promise<Account[] | null> {
  return getCache<Account[]>(ACCOUNTS_KEY);
}

export async function cacheCategories(categories: Category[]) {
  await setCache(CATEGORIES_KEY, categories);
}

export async function readCategoriesCache(): Promise<Category[] | null> {
  return getCache<Category[]>(CATEGORIES_KEY);
}

export async function cacheTransactions(params: Record<string, string> | undefined, txs: Transaction[]) {
  await setCache(transactionsCacheKey(params), txs);
}

export async function readTransactionsCache(params?: Record<string, string>): Promise<Transaction[] | null> {
  return getCache<Transaction[]>(transactionsCacheKey(params));
}

export async function invalidateAllTransactionsCache(): Promise<void> {
  const db = await getDb();
  const keys = await db.getAllKeys("cache");
  await Promise.all(
    keys
      .filter((key): key is string => typeof key === "string" && key.startsWith("transactions:"))
      .map((key) => db.delete("cache", key))
  );
}

export async function putLocalTransaction(tx: LocalTransaction) {
  const db = await getDb();
  await db.put("localTransactions", tx, tx.id);
}

export async function removeLocalTransaction(id: string) {
  const db = await getDb();
  await db.delete("localTransactions", id);
}

export async function listLocalTransactions(): Promise<LocalTransaction[]> {
  const db = await getDb();
  return db.getAll("localTransactions");
}

export async function hideEntity(id: string, kind: "transaction" | "account") {
  const db = await getDb();
  await db.put("hiddenIds", { id, kind }, `${kind}:${id}`);
}

export async function listHiddenIds(kind: "transaction" | "account"): Promise<Set<string>> {
  const db = await getDb();
  const all = await db.getAll("hiddenIds");
  return new Set(all.filter((x) => x.kind === kind).map((x) => x.id));
}

export async function clearHiddenId(id: string, kind: "transaction" | "account") {
  const db = await getDb();
  await db.delete("hiddenIds", `${kind}:${id}`);
}

export async function mergeTransactions(
  server: Transaction[],
  params?: Record<string, string>
): Promise<Transaction[]> {
  const hidden = await listHiddenIds("transaction");
  const local = await listLocalTransactions();
  const filtered = server.filter((t) => !hidden.has(t.id));

  const typeFilter = params?.type;
  const accountFilter = params?.account_id;

  const localFiltered = local.filter((t) => {
    if (hidden.has(t.id)) return false;
    if (typeFilter && t.type !== typeFilter) return false;
    if (accountFilter && t.account?.id !== accountFilter) return false;
    if (params?.from) {
      const at = parseApiDateTime(t.occurred_at).getTime();
      if (at < parseRangeBound(params.from, "start")) return false;
    }
    if (params?.to) {
      const at = parseApiDateTime(t.occurred_at).getTime();
      if (at > parseRangeBound(params.to, "end")) return false;
    }
    return true;
  });

  const byId = new Map<string, Transaction>();
  for (const t of filtered) byId.set(t.id, t);
  for (const t of localFiltered) byId.set(t.id, t);

  return [...byId.values()].sort(
    (a, b) => parseApiDateTime(b.occurred_at).getTime() - parseApiDateTime(a.occurred_at).getTime()
  );
}

export async function patchItemCategory(
  transactionId: string,
  itemId: string,
  categoryId: string,
  categoryName: string
) {
  const db = await getDb();
  const local = await db.get("localTransactions", transactionId);
  if (local?.items) {
    local.items = local.items.map((it) =>
      it.id === itemId ? { ...it, category_id: categoryId, category: { name: categoryName } } : it
    );
    await db.put("localTransactions", local, transactionId);
  }

  const keys = await db.getAllKeys("cache");
  for (const key of keys) {
    if (typeof key !== "string" || !key.startsWith("transactions:")) continue;
    const entry = await db.get("cache", key);
    if (!entry?.data) continue;
    const txs = entry.data as Transaction[];
    let changed = false;
    const next = txs.map((tx) => {
      if (tx.id !== transactionId || !tx.items) return tx;
      changed = true;
      return {
        ...tx,
        items: tx.items.map((it) =>
          it.id === itemId ? { ...it, category_id: categoryId, category: { name: categoryName } } : it
        ),
      };
    });
    if (changed) await db.put("cache", { ...entry, data: next }, key);
  }
}

export async function mergeAccounts(server: Account[]): Promise<Account[]> {
  const hidden = await listHiddenIds("account");
  const db = await getDb();
  const queue = await db.getAll("queue");
  const tempAccounts: Account[] = [];
  for (const op of queue) {
    if (op.type === "createAccount") {
      tempAccounts.push({
        id: op.tempId,
        name: op.body.name,
        balance: op.body.balance,
      });
    }
  }

  const byId = new Map<string, Account>();
  for (const a of server.filter((x) => !hidden.has(x.id))) byId.set(a.id, a);
  for (const a of tempAccounts) byId.set(a.id, a);
  return [...byId.values()];
}
