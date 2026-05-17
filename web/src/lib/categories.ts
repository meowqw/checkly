import type { Category } from "@/api/client";

export function getRootCategories(categories: Category[], type: string): Category[] {
  return categories.filter((c) => c.type === type);
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

/** Для статистики: подкатегория → родитель, иначе корень */
export function getCategoryGroupName(
  categoryId: string | null | undefined,
  displayMap: Map<string, string>
): string {
  if (!categoryId) return "Прочее";
  return displayMap.get(categoryId) ?? "Прочее";
}
