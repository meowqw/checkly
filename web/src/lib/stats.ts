import { api, formatMoney, type Category, type Transaction } from "@/api/client";
import { buildCategoryDisplayMap, getCategoryGroupName } from "@/lib/categories";

export type CategoryStat = { name: string; amount: number; percent: number };

export async function loadCategoryStats(
  expenseTx: Transaction[],
  categoriesTree: Category[]
): Promise<CategoryStat[]> {
  if (expenseTx.length === 0) return [];

  const displayMap = buildCategoryDisplayMap(categoriesTree);
  const totals = new Map<string, number>();

  await Promise.all(
    expenseTx.map(async (tx) => {
      try {
        const { transaction } = await api.transaction(tx.id);
        if (transaction.items?.length) {
          for (const item of transaction.items) {
            const name = getCategoryGroupName(item.category_id, displayMap);
            totals.set(name, (totals.get(name) ?? 0) + item.amount);
          }
        } else {
          const name = getCategoryGroupName(null, displayMap);
          totals.set(name, (totals.get(name) ?? 0) + transaction.amount);
        }
      } catch {
        totals.set("Прочее", (totals.get("Прочее") ?? 0) + tx.amount);
      }
    })
  );

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
