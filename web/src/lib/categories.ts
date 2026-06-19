import type { Category, Transaction } from "@/api/client";
import { resolveCategoryColor } from "@/lib/category-icons";

export function getRootCategories(categories: Category[], type: string): Category[] {
  return categories
    .filter((c) => c.type === type)
    .sort((a, b) => {
      const aCustom = a.is_custom ? 1 : 0;
      const bCustom = b.is_custom ? 1 : 0;
      if (aCustom !== bCustom) return aCustom - bCustom;
      return a.name.localeCompare(b.name, "ru");
    });
}

export function getSubcategories(categories: Category[], parentId: string): Category[] {
  const parent = findCategoryById(categories, parentId);
  return parent?.children ?? [];
}

export function findCategoryById(categories: Category[], id: string): Category | null {
  for (const c of categories) {
    if (c.id === id) return c;
    if (c.children?.length) {
      const found = findCategoryById(c.children, id);
      if (found) return found;
    }
  }
  return null;
}

/** id → «Родитель › Подкатегория» или только имя */
export function buildCategoryDisplayMap(categories: Category[]): Map<string, string> {
  const map = new Map<string, string>();

  const walk = (list: Category[], parentName?: string) => {
    for (const c of list) {
      const label = parentName ? `${parentName} › ${c.name}` : c.name;
      map.set(c.id, label);
      if (c.children?.length) walk(c.children, c.name);
    }
  };

  walk(categories);
  return map;
}

/** id и display label → hex цвет категории */
export function buildCategoryColorMap(categories: Category[]): Map<string, string> {
  const map = new Map<string, string>();

  const walk = (list: Category[], parentName?: string) => {
    for (const c of list) {
      const label = parentName ? `${parentName} › ${c.name}` : c.name;
      const color = resolveCategoryColor(c.color, c.name);
      map.set(c.id, color);
      map.set(label, color);
      if (c.children?.length) walk(c.children, c.name);
    }
  };

  walk(categories);
  return map;
}

/** Для статистики: подкатегория → родитель, иначе корень */
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
