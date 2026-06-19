import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import * as data from "@/api/data-service";
import type { Category, TransactionItem } from "@/api/client";
import { ApiError } from "@/api/client";
import { CategoryPicker } from "@/components/CategoryPicker";
import { Button } from "@/components/ui/button";
import { getRootCategories, getSubcategories } from "@/lib/categories";

type Props = {
  open: boolean;
  transactionId: string;
  item: TransactionItem | null;
  txType?: "expense" | "income";
  onClose: () => void;
  onSaved: (transaction: Awaited<ReturnType<typeof data.updateTransactionItem>>["transaction"]) => void;
};

export function ItemCategorySheet({
  open,
  transactionId,
  item,
  txType = "expense",
  onClose,
  onSaved,
}: Props) {
  const [categoryTree, setCategoryTree] = useState<Category[]>([]);
  const [parentCategoryId, setParentCategoryId] = useState("");
  const [subcategoryId, setSubcategoryId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const rootCategories = useMemo(() => getRootCategories(categoryTree, txType), [categoryTree, txType]);
  const subcategories = useMemo(
    () => (parentCategoryId ? getSubcategories(categoryTree, parentCategoryId) : []),
    [categoryTree, parentCategoryId]
  );

  useEffect(() => {
    if (!open) return;
    setError("");
    data.getCategories().then((r) => {
      setCategoryTree(r.categories);
      if (item?.category_id) {
        const match = findCategoryPath(r.categories, item.category_id);
        setParentCategoryId(match.parentId);
        setSubcategoryId(match.subcategoryId);
      } else {
        setParentCategoryId("");
        setSubcategoryId("");
      }
    });
  }, [open, item?.category_id, item?.id]);

  const onParentChange = (id: string) => {
    setParentCategoryId(id);
    setSubcategoryId("");
  };

  if (!open || !item) return null;

  const finalCategoryId = subcategoryId || parentCategoryId;
  const categoryName =
    subcategories.find((c) => c.id === subcategoryId)?.name ??
    rootCategories.find((c) => c.id === parentCategoryId)?.name ??
    "";

  const save = async () => {
    if (!item.id) {
      setError("Нельзя изменить категорию этой позиции");
      return;
    }
    if (!finalCategoryId) {
      setError("Выберите категорию");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await data.updateTransactionItem(
        transactionId,
        item.id,
        { category_id: finalCategoryId },
        categoryName
      );
      onSaved(res.transaction);
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка сохранения");
    } finally {
      setLoading(false);
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-0 animate-fade-in">
      <button type="button" className="absolute inset-0" aria-label="Закрыть" onClick={onClose} />
      <div className="relative z-10 flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl bg-white shadow-xl animate-slide-up">
        <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-4 pt-4">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs text-neutral-400">Категория позиции</p>
              <p className="truncate text-sm font-semibold">{item.raw_name}</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-1 text-neutral-400 hover:bg-neutral-100"
            >
              <X size={18} />
            </button>
          </div>

          <p className="mb-3 text-xs text-neutral-500">
            {txType === "expense"
              ? "Для товаров из чека категория сохранится и подставится при следующих покупках."
              : "Категория будет обновлена для этой операции."}
          </p>

          {error && (
            <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <CategoryPicker
            roots={rootCategories}
            subcategories={subcategories}
            parentId={parentCategoryId}
            subcategoryId={subcategoryId}
            onParentChange={onParentChange}
            onSubcategoryChange={setSubcategoryId}
          />
        </div>

        <div className="shrink-0 border-t border-neutral-100 bg-white px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3">
          <Button
            variant="brand"
            className="w-full"
            disabled={loading || !finalCategoryId}
            onClick={() => void save()}
          >
            {loading ? "Сохранение..." : "Сохранить"}
          </Button>
        </div>
      </div>
    </div>,
    document.body
  );
}

function findCategoryPath(
  categories: Category[],
  targetId: string
): { parentId: string; subcategoryId: string } {
  for (const root of categories) {
    if (root.id === targetId) return { parentId: root.id, subcategoryId: "" };
    for (const child of root.children ?? []) {
      if (child.id === targetId) return { parentId: root.id, subcategoryId: child.id };
    }
  }
  return { parentId: "", subcategoryId: "" };
}
