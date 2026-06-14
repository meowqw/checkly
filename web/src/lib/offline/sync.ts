import { api } from "@/api/client";
import {
  cacheAccounts,
  cacheCategories,
  clearHiddenId,
  readAccountsCache,
  readCategoriesCache,
  removeLocalTransaction,
} from "@/lib/offline/cache";
import { dequeue, listQueue } from "@/lib/offline/queue";
import type { QueuedOp } from "@/lib/offline/types";
import { isOnline } from "@/lib/connectivity";
import { loadTempIdMap, resolveTempId, saveTempId } from "@/lib/offline/temp-id-map";
import { notifyAccountsChanged, notifyTransactionsChanged } from "@/lib/data-events";

export async function processSyncQueue(): Promise<{ ok: number; failed: number }> {
  if (!isOnline()) return { ok: 0, failed: 0 };

  const ops = await listQueue();
  const tempIdMap = await loadTempIdMap();
  let ok = 0;
  let failed = 0;

  for (const op of ops) {
    try {
      await applyOp(op, tempIdMap);
      await dequeue(op.id);
      ok++;
    } catch {
      failed++;
      break;
    }
  }

  if (ok > 0) {
    try {
      const [acc, cat] = await Promise.all([api.accounts(), api.categories()]);
      await cacheAccounts(acc.accounts);
      await cacheCategories(cat.categories);
      notifyAccountsChanged();
      notifyTransactionsChanged();
    } catch {
      // keep stale cache
    }
  }

  return { ok, failed };
}

async function applyOp(op: QueuedOp, tempIdMap: Map<string, string>) {
  switch (op.type) {
    case "createAccount": {
      const res = await api.createAccount(op.body);
      tempIdMap.set(op.tempId, res.account.id);
      await saveTempId(op.tempId, res.account.id);
      await clearHiddenId(op.tempId, "account");
      break;
    }
    case "deleteAccount": {
      if (op.accountId.startsWith("local_") && !tempIdMap.has(op.accountId)) {
        await clearHiddenId(op.accountId, "account");
        break;
      }
      const id = await resolveTempId(op.accountId, tempIdMap);
      await api.deleteAccount(id);
      await clearHiddenId(op.accountId, "account");
      break;
    }
    case "createTransaction": {
      const body = { ...op.body };
      body.account_id = await resolveTempId(body.account_id, tempIdMap);
      const res = await api.createTransaction(body);
      tempIdMap.set(op.tempId, res.transaction.id);
      await saveTempId(op.tempId, res.transaction.id);
      await removeLocalTransaction(op.tempId);
      break;
    }
    case "deleteTransaction": {
      if (op.transactionId.startsWith("local_") && !tempIdMap.has(op.transactionId)) {
        await removeLocalTransaction(op.transactionId);
        await clearHiddenId(op.transactionId, "transaction");
        break;
      }
      const id = await resolveTempId(op.transactionId, tempIdMap);
      await api.deleteTransaction(id);
      await removeLocalTransaction(op.transactionId);
      await clearHiddenId(op.transactionId, "transaction");
      break;
    }
    case "updateTransactionItem": {
      const txId = await resolveTempId(op.transactionId, tempIdMap);
      await api.updateTransactionItem(txId, op.itemId, { category_id: op.categoryId });
      break;
    }
  }
}

export async function warmCacheIfOnline() {
  if (!isOnline()) return;
  try {
    const [acc, cat] = await Promise.all([api.accounts(), api.categories()]);
    await cacheAccounts(acc.accounts);
    await cacheCategories(cat.categories);
  } catch {
    const acc = await readAccountsCache();
    const cat = await readCategoriesCache();
    if (!acc && !cat) throw new Error("offline");
  }
}
