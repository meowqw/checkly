import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import * as data from "@/api/data-service";
import { ApiError, type Category, type Tag } from "@/api/client";
import { CategoryIcon } from "@/components/CategoryIcon";
import { CreateCategorySheet } from "@/components/CreateCategorySheet";
import { PageHeader } from "@/components/mobile/PageHeader";
import { RefreshBar } from "@/components/mobile/RefreshBar";
import { CategoryListSkeleton } from "@/components/mobile/Skeleton";
import { Button } from "@/components/ui/button";
import { trackBackgroundFresh } from "@/lib/cache-first";
import { subscribeCategoriesChanged } from "@/lib/data-events";
import { cn } from "@/lib/utils";

export default function CategoriesPage() {
  const [tab, setTab] = useState<"categories" | "tags">("categories");
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [filter, setFilter] = useState<"expense" | "income">("expense");
  const [booting, setBooting] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [tagName, setTagName] = useState("");
  const [tagSaving, setTagSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const hasEverLoaded = useRef(false);

  const load = useCallback(
    (skipRevalidate = false) =>
      (async () => {
        if (!hasEverLoaded.current) setBooting(true);
        setError("");
        try {
          const [catRes, tagRes] = await Promise.all([
            data.getCategories({ skipRevalidate }),
            data.getTags({ skipRevalidate }),
          ]);
          setCategories(catRes.categories);
          setTags(tagRes.tags);
          hasEverLoaded.current = true;
          setBooting(false);
          if (!skipRevalidate) {
            trackBackgroundFresh([catRes, tagRes], setRefreshing);
          }
        } catch (err) {
          if (!hasEverLoaded.current) {
            setError(err instanceof ApiError ? err.message : "Не удалось загрузить");
            setBooting(false);
          }
        }
      })(),
    []
  );

  useEffect(() => {
    void load(false);
    return subscribeCategoriesChanged(() => {
      void load(true);
    });
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
      void load(true);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Не удалось удалить");
    } finally {
      setDeletingId(null);
    }
  };

  const removeTag = async (tag: Tag) => {
    if (!tag.is_custom) return;
    if (!confirm(`Удалить тег «${tag.name}»?`)) return;
    setDeletingId(tag.id);
    try {
      await data.deleteTag(tag.id);
      void load(true);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Не удалось удалить");
    } finally {
      setDeletingId(null);
    }
  };

  const createTag = async (e: FormEvent) => {
    e.preventDefault();
    const name = tagName.trim();
    if (!name) return;
    setTagSaving(true);
    try {
      await data.createTag({ name });
      setTagName("");
      void load(true);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Не удалось создать тег");
    } finally {
      setTagSaving(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Категории и теги"
        subtitle="Плоские категории · независимые теги"
        action={
          tab === "categories" ? (
            <button
              type="button"
              onClick={() => setCreateOpen(true)}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand text-white shadow-sm"
              aria-label="Добавить категорию"
            >
              <Plus size={18} />
            </button>
          ) : undefined
        }
      />

      <div className="mb-3 flex border-b border-neutral-100">
        {(
          [
            ["categories", "Категории"],
            ["tags", "Теги"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={cn(
              "relative flex-1 py-2 text-sm font-medium",
              tab === id ? "text-brand" : "text-neutral-400"
            )}
          >
            {label}
            {tab === id && (
              <span className="absolute inset-x-4 -bottom-px h-0.5 rounded-full bg-brand" />
            )}
          </button>
        ))}
      </div>

      <RefreshBar active={refreshing} />

      {booting && !hasEverLoaded.current ? (
        <CategoryListSkeleton />
      ) : error && !hasEverLoaded.current ? (
        <p className="py-12 text-center text-sm text-red-600">{error}</p>
      ) : tab === "categories" ? (
        <>
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
          <div className="space-y-2 pb-4">
            {roots.map((cat) => (
              <div
                key={cat.id}
                className="flex items-center gap-3 rounded-xl border border-neutral-100 px-3 py-2.5"
              >
                <CategoryIcon icon={cat.icon} color={cat.color} name={cat.name} size="sm" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-semibold">{cat.name}</span>
                    {cat.is_custom && (
                      <span className="shrink-0 rounded-full bg-brand-muted px-2 py-0.5 text-[10px] font-medium text-brand-dark">
                        Моя
                      </span>
                    )}
                  </div>
                  {!cat.is_custom && (
                    <p className="text-[11px] text-neutral-400">Системная · для чеков</p>
                  )}
                </div>
                {cat.is_custom && (
                  <button
                    type="button"
                    onClick={() => void removeCategory(cat)}
                    disabled={deletingId === cat.id}
                    className="rounded-lg p-2 text-neutral-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                    aria-label="Удалить категорию"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="space-y-4 pb-4">
          <p className="text-xs text-neutral-500">
            Теги не привязаны к категориям. Один тег можно использовать с любой категорией.
          </p>
          <form onSubmit={(e) => void createTag(e)} className="flex gap-2">
            <input
              className="input-field flex-1"
              placeholder="Новый тег"
              value={tagName}
              onChange={(e) => setTagName(e.target.value)}
            />
            <Button type="submit" variant="brand" disabled={tagSaving || !tagName.trim()}>
              {tagSaving ? "…" : "Добавить"}
            </Button>
          </form>
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <span
                key={tag.id}
                className="inline-flex items-center gap-1 rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-700"
              >
                {tag.name}
                {tag.is_custom ? (
                  <button
                    type="button"
                    className="text-neutral-400 hover:text-red-500"
                    disabled={deletingId === tag.id}
                    onClick={() => void removeTag(tag)}
                    aria-label={`Удалить ${tag.name}`}
                  >
                    <Trash2 size={12} />
                  </button>
                ) : (
                  <span className="text-[10px] text-neutral-400">sys</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      <CreateCategorySheet
        open={createOpen}
        type={filter}
        onClose={() => setCreateOpen(false)}
        onCreated={() => void load(true)}
      />
    </>
  );
}
