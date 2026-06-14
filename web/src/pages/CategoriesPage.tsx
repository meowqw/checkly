import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import * as data from "@/api/data-service";
import { ApiError, type Category } from "@/api/client";
import { CategoryIcon } from "@/components/CategoryIcon";
import { CreateCategorySheet } from "@/components/CreateCategorySheet";
import { PageHeader } from "@/components/mobile/PageHeader";
import { cn } from "@/lib/utils";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [filter, setFilter] = useState<"expense" | "income">("expense");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    data
      .getCategories()
      .then((r) => setCategories(r.categories))
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить категории");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const roots = useMemo(() => {
    return categories
      .filter((c) => c.type === filter)
      .sort((a, b) => {
        const aCustom = a.is_custom ? 1 : 0;
        const bCustom = b.is_custom ? 1 : 0;
        if (aCustom !== bCustom) return aCustom - bCustom;
        return a.name.localeCompare(b.name, "ru");
      });
  }, [categories, filter]);

  const removeCategory = async (cat: Category) => {
    if (!cat.is_custom) return;
    if (!confirm(`Удалить категорию «${cat.name}»?`)) return;
    setDeletingId(cat.id);
    try {
      await data.deleteCategory(cat.id);
      load();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Не удалось удалить");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <>
      <PageHeader
        title="Категории"
        subtitle="Системные и свои"
        action={
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand text-white shadow-sm"
            aria-label="Добавить категорию"
          >
            <Plus size={18} />
          </button>
        }
      />

      <div className="mb-4 flex border-b border-neutral-100">
        {(["expense", "income"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setFilter(t)}
            className={cn(
              "relative flex-1 py-2 text-sm font-medium",
              filter === t ? "text-brand" : "text-neutral-400"
            )}
          >
            {t === "expense" ? "Расходы" : "Доходы"}
            {filter === t && (
              <span className="absolute inset-x-4 -bottom-px h-0.5 rounded-full bg-brand" />
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="py-12 text-center text-sm text-neutral-400">Загрузка...</p>
      ) : error ? (
        <p className="py-12 text-center text-sm text-red-600">{error}</p>
      ) : (
        <div className="space-y-3 pb-4">
          {roots.map((cat) => (
            <CategoryCard
              key={cat.id}
              category={cat}
              deleting={deletingId === cat.id}
              onDelete={() => void removeCategory(cat)}
            />
          ))}
        </div>
      )}

      <CreateCategorySheet
        open={createOpen}
        type={filter}
        categories={categories}
        onClose={() => setCreateOpen(false)}
        onCreated={load}
      />
    </>
  );
}

function CategoryCard({
  category,
  deleting,
  onDelete,
}: {
  category: Category;
  deleting: boolean;
  onDelete: () => void;
}) {
  const children = category.children ?? [];

  return (
    <div className="overflow-hidden rounded-xl border border-neutral-100">
      <div className="flex items-center gap-3 bg-neutral-50 px-3 py-2.5">
        <CategoryIcon icon={category.icon} color={category.color} name={category.name} size="sm" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate text-sm font-semibold">{category.name}</span>
            {category.is_custom && (
              <span className="shrink-0 rounded-full bg-brand-muted px-2 py-0.5 text-[10px] font-medium text-brand-dark">
                Моя
              </span>
            )}
          </div>
          {!category.is_custom && (
            <p className="text-[11px] text-neutral-400">Системная · для чеков</p>
          )}
        </div>
        {category.is_custom && (
          <button
            type="button"
            onClick={onDelete}
            disabled={deleting}
            className="rounded-lg p-2 text-neutral-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
            aria-label="Удалить категорию"
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>

      {children.length > 0 ? (
        <ul className="list-divider">
          {children.map((ch) => (
            <li key={ch.id} className="flex items-center gap-2.5 px-3 py-2.5">
              <span
                className="h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ backgroundColor: category.color ?? "#d4d4d4" }}
              />
              <span className="min-w-0 flex-1 truncate text-sm text-neutral-600">{ch.name}</span>
              {ch.is_custom && (
                <span className="shrink-0 text-[10px] text-neutral-400">моя</span>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="px-3 py-2 text-xs text-neutral-400">Без подкатегорий</p>
      )}
    </div>
  );
}
