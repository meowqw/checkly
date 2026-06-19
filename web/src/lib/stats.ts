import { formatMoney, type Category, type CategoryStat, type PeriodStats, type Transaction } from "@/api/client";
import { buildCategoryDisplayMap, getCategoryGroupName } from "@/lib/categories";
import { resolveCategoryColor } from "@/lib/category-icons";
import { parseApiDateTime } from "@/lib/dates";
import { sourceLabel } from "@/lib/transactions";

export type { CategoryStat };

type TxWithItems = Transaction & {
  title?: string;
  category?: string | null;
  items?: Array<{ category_id?: string | null; amount: number; category?: { name: string } }>;
};

function resolveItemCategoryName(
  item: NonNullable<TxWithItems["items"]>[number],
  displayMap: Map<string, string>
): string {
  return (
    (item.category_id && displayMap.get(item.category_id)) ||
    item.category?.name ||
    getCategoryGroupName(item.category_id ?? null, displayMap)
  );
}

/** Offline-fallback: считает статистику из списка транзакций (как раньше на главной). */
export function buildStatsFromTransactions(
  transactions: Transaction[],
  categoriesTree: Category[]
): PeriodStats {
  const expenseTx = transactions.filter((t) => t.type === "expense");
  const incomeTx = transactions.filter((t) => t.type === "income");

  const categories = loadCategoryStats(expenseTx, categoriesTree).map((row) => ({
    category_id: null,
    name: row.name,
    amount: row.amount,
    percent: row.percent,
    color: row.color ?? null,
  }));

  const recent_expenses = [...expenseTx]
    .sort(
      (a, b) => parseApiDateTime(b.occurred_at).getTime() - parseApiDateTime(a.occurred_at).getTime()
    )
    .slice(0, 8);

  return {
    expense: expenseTx.reduce((sum, t) => sum + t.amount, 0),
    income: incomeTx.reduce((sum, t) => sum + t.amount, 0),
    categories,
    recent_expenses,
  };
}

/** Без доп. запросов — использует items из списка транзакций. */
export function loadCategoryStats(expenseTx: Transaction[], categoriesTree: Category[]) {
  if (expenseTx.length === 0) return [];

  const displayMap = buildCategoryDisplayMap(categoriesTree);
  const totals = new Map<string, number>();

  for (const raw of expenseTx) {
    const tx = raw as TxWithItems;
    if (tx.source === "qr_receipt" && tx.items?.length) {
      for (const item of tx.items) {
        const name = resolveItemCategoryName(item, displayMap);
        totals.set(name, (totals.get(name) ?? 0) + item.amount);
      }
    } else if (tx.items?.length) {
      for (const item of tx.items) {
        const name = resolveItemCategoryName(item, displayMap);
        totals.set(name, (totals.get(name) ?? 0) + item.amount);
      }
    } else if (tx.category) {
      totals.set(tx.category, (totals.get(tx.category) ?? 0) + tx.amount);
    } else {
      totals.set("Прочее", (totals.get("Прочее") ?? 0) + tx.amount);
    }
  }

  const total = [...totals.values()].reduce((a, b) => a + b, 0) || 1;
  return [...totals.entries()]
    .map(([name, amount]) => ({
        name,
        amount,
        percent: Math.round((amount / total) * 100),
        color: resolveStatColorForLabel(categoriesTree, name),
      }))
    .sort((a, b) => b.amount - a.amount);
}

function resolveStatColorForLabel(categories: Category[], label: string): string | undefined {
  for (const root of categories) {
    if (root.name === label) {
      return resolveCategoryColor(root.color, root.name);
    }
    for (const child of root.children ?? []) {
      if (`${root.name} › ${child.name}` === label) {
        return resolveCategoryColor(child.color ?? root.color, child.name);
      }
    }
  }
  return undefined;
}

export function formatStatAmount(kopecks: number): string {
  return formatMoney(kopecks);
}

export function colorMapFromStats(categories: CategoryStat[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const row of categories) {
    if (!row.color) continue;
    map.set(row.name, row.color);
    if (row.category_id) map.set(row.category_id, row.color);
  }
  return map;
}

export function txRowFromList(
  t: Transaction & {
    title?: string;
    merchant?: { name?: string };
    category?: string | null;
    source?: string;
    items_count?: number;
  },
  displayMap: Map<string, string>
) {
  const tx = t as TxWithItems;
  let title = tx.merchant?.name || tx.title || tx.comment || "Операция";
  if (tx.source === "qr_receipt" && !tx.merchant?.name && !tx.title) title = "Чек";

  let category = tx.category || "Прочее";
  if (tx.source !== "qr_receipt") {
    const item = tx.items?.[0];
    if (item?.category_id) {
      category = displayMap.get(item.category_id) ?? item.category?.name ?? category;
    } else if (item?.category?.name) {
      category = item.category.name;
    }
  } else {
    category = "";
  }

  let subtitle = category;
  if (tx.source === "qr_receipt") {
    const parts: string[] = [sourceLabel("qr_receipt")];
    const count = tx.items_count ?? tx.items?.length ?? 0;
    if (count > 1) parts.push(`${count} поз.`);
    subtitle = parts.join(" · ");
  }

  return {
    id: tx.id,
    title,
    amount: tx.amount,
    type: tx.type,
    occurredAt: tx.occurred_at,
    category: subtitle,
    source: tx.source,
    items: tx.items,
  };
}
