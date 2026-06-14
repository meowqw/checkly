import { formatMoney, type Category, type Transaction } from "@/api/client";
import { buildCategoryDisplayMap, getCategoryGroupName } from "@/lib/categories";

export type CategoryStat = { name: string; amount: number; percent: number };

type TxWithItems = Transaction & {
  title?: string;
  category?: string | null;
  items?: Array<{ category_id?: string | null; amount: number; category?: { name: string } }>;
};

/** Без доп. запросов — использует items из списка транзакций. */
export function loadCategoryStats(expenseTx: Transaction[], categoriesTree: Category[]): CategoryStat[] {
  if (expenseTx.length === 0) return [];

  const displayMap = buildCategoryDisplayMap(categoriesTree);
  const totals = new Map<string, number>();

  for (const raw of expenseTx) {
    const tx = raw as TxWithItems;
    if (tx.items?.length) {
      for (const item of tx.items) {
        const name =
          (item.category_id && displayMap.get(item.category_id)) ||
          item.category?.name ||
          getCategoryGroupName(item.category_id ?? null, displayMap);
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
    }))
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 8);
}

export function formatStatAmount(kopecks: number): string {
  return formatMoney(kopecks);
}

export function txRowFromList(
  t: Transaction & { title?: string; merchant?: { name?: string }; category?: string | null },
  displayMap: Map<string, string>
) {
  const tx = t as TxWithItems;
  let title = tx.merchant?.name || tx.title || tx.comment || "Операция";
  if (tx.source === "qr_receipt" && !tx.merchant?.name) title = "Чек";

  let category = tx.category || "Прочее";
  const item = tx.items?.[0];
  if (item?.category_id) {
    category = displayMap.get(item.category_id) ?? item.category?.name ?? category;
  } else if (item?.category?.name) {
    category = item.category.name;
  }

  return {
    id: tx.id,
    title,
    amount: tx.amount,
    type: tx.type,
    occurredAt: tx.occurred_at,
    category,
  };
}
