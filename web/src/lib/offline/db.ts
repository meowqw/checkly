import { openDB, type DBSchema, type IDBPDatabase } from "idb";
import type { CacheEntry, QueuedOp } from "@/lib/offline/types";
import type { LocalTransaction } from "@/lib/offline/types";

interface FMDB extends DBSchema {
  cache: {
    key: string;
    value: CacheEntry<unknown>;
  };
  queue: {
    key: string;
    value: QueuedOp;
  };
  localTransactions: {
    key: string;
    value: LocalTransaction;
  };
  hiddenIds: {
    key: string;
    value: { id: string; kind: "transaction" | "account" };
  };
}

let dbPromise: Promise<IDBPDatabase<FMDB>> | null = null;

export function getDb() {
  if (!dbPromise) {
    dbPromise = openDB<FMDB>("finance_manager", 1, {
      upgrade(db) {
        db.createObjectStore("cache");
        db.createObjectStore("queue");
        db.createObjectStore("localTransactions");
        db.createObjectStore("hiddenIds");
      },
    });
  }
  return dbPromise;
}

export async function clearOfflineData() {
  const db = await getDb();
  await Promise.all([
    db.clear("cache"),
    db.clear("queue"),
    db.clear("localTransactions"),
    db.clear("hiddenIds"),
  ]);
}
