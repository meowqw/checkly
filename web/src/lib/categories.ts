import type { Category, Transaction } from "@/api/client";
import { resolveCategoryColor } from "@/lib/category-icons";

/** Категории нужного типа (плоский список). Чаще используемые — выше. */
export function getRootCategories(categories: Category[], type: string): Category[] {
  return categories
    .filter((c) => c.type === type)
    .sort((a, b) => {
      const usageDiff = (b.usage_count ?? 0) - (a.usage_count ?? 0);
      if (usageDiff !== 0) return usageDiff;
      const aCustom = a.is_custom ? 1 : 0;
      const bCustom = b.is_custom ? 1 : 0;
      if (aCustom !== bCustom) return aCustom - bCustom;
      return a.name.localeCompare(b.name, "ru");
    });
}

export function findCategoryById(categories: Category[], id: string): Category | null {
  return categories.find((c) => c.id === id) ?? null;
}

/** id → имя категории */
export function buildCategoryDisplayMap(categories: Category[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const c of categories) {
    map.set(c.id, c.name);
  }
  return map;
}

/** id и name → hex цвет категории */
export function buildCategoryColorMap(categories: Category[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const c of categories) {
    const color = resolveCategoryColor(c.color, c.name);
    map.set(c.id, color);
    map.set(c.name, color);
  }
  return map;
}

export function getCategoryGroupName(
  categoryId: string | null | undefined,
  displayMap: Map<string, string>
): string {
  if (!categoryId) return "Прочее";
  return displayMap.get(categoryId) ?? "Прочее";
}

type TxColorInput = Transaction & {
  category?: string | null;
  items?: Array<{ category_id?: string | null; category?: { name: string } }>;
};

/** Цвет маркера операции: receipt = null (белый с обводкой), иначе hex */
export function resolveTransactionDotColor(
  tx: TxColorInput,
  colorMap: Map<string, string>
): string | null {
  if (tx.source === "qr_receipt") return null;

  const item = tx.items?.[0];
  if (item?.category_id) {
    const byId = colorMap.get(item.category_id);
    if (byId) return byId;
  }
  if (item?.category?.name) {
    const byName = colorMap.get(item.category.name);
    if (byName) return byName;
  }
  if (tx.category) {
    const byTx = colorMap.get(tx.category);
    if (byTx) return byTx;
  }
  return "#78716c";
}
