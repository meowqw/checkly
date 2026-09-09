import { useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import type { Tag } from "@/api/client";
import { cn } from "@/lib/utils";

type Props = {
  tags: Tag[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  max?: number;
};

const COLLAPSED_LIMIT = 10;

function sortByUsage(a: Tag, b: Tag): number {
  const usageDiff = (b.usage_count ?? 0) - (a.usage_count ?? 0);
  if (usageDiff !== 0) return usageDiff;
  return a.name.localeCompare(b.name, "ru");
}

/** Мультивыбор тегов (независимы от категории). */
export function TagPicker({ tags, selectedIds, onChange, max = 5 }: Props) {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(false);

  const sorted = useMemo(() => [...tags].sort(sortByUsage), [tags]);

  const selected = useMemo(
    () => sorted.filter((t) => selectedIds.includes(t.id)),
    [sorted, selectedIds]
  );

  const available = useMemo(
    () => sorted.filter((t) => !selectedIds.includes(t.id)),
    [sorted, selectedIds]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return available;
    return available.filter((t) => t.name.toLowerCase().includes(q));
  }, [available, query]);

  const searching = query.trim().length > 0;
  const visible =
    searching || expanded ? filtered : filtered.slice(0, COLLAPSED_LIMIT);
  const hiddenCount = searching || expanded ? 0 : Math.max(0, filtered.length - COLLAPSED_LIMIT);

  const toggle = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((x) => x !== id));
      return;
    }
    if (selectedIds.length >= max) return;
    onChange([...selectedIds, id]);
  };

  if (tags.length === 0) return null;

  const atLimit = selectedIds.length >= max;

  return (
    <div className="space-y-2.5">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-xs text-neutral-500">
          Теги <span className="text-neutral-400">(необязательно)</span>
        </p>
        <p className="text-[11px] tabular-nums text-neutral-400">
          {selectedIds.length}/{max}
        </p>
      </div>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selected.map((tag) => (
            <button
              key={tag.id}
              type="button"
              onClick={() => toggle(tag.id)}
              className="inline-flex items-center gap-1 rounded-full bg-brand px-2.5 py-1 text-xs font-medium text-white"
            >
              {tag.name}
              <X size={12} strokeWidth={2.5} aria-hidden />
            </button>
          ))}
        </div>
      )}

      <div className="relative">
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-neutral-400"
          aria-hidden
        />
        <input
          type="search"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (e.target.value.trim()) setExpanded(true);
          }}
          placeholder="Найти тег…"
          className="w-full rounded-xl border border-neutral-200 bg-neutral-50 py-2 pl-9 pr-3 text-sm outline-none transition focus:border-brand focus:bg-white"
          enterKeyHint="search"
        />
      </div>

      {atLimit && (
        <p className="text-[11px] text-neutral-400">Выбрано максимум тегов. Снимите один, чтобы добавить другой.</p>
      )}

      <div
        className={cn(
          "rounded-xl border border-neutral-100 bg-neutral-50/80",
          (searching || expanded) && "max-h-44 overflow-y-auto overscroll-contain"
        )}
      >
        {visible.length === 0 ? (
          <p className="px-3 py-3 text-center text-xs text-neutral-400">
            {searching ? "Ничего не найдено" : "Все теги уже выбраны"}
          </p>
        ) : (
          <div className="flex flex-wrap gap-1.5 p-2.5">
            {visible.map((tag) => (
              <button
                key={tag.id}
                type="button"
                disabled={atLimit}
                onClick={() => toggle(tag.id)}
                className={cn(
                  "rounded-full px-2.5 py-1 text-xs font-medium transition",
                  atLimit
                    ? "cursor-not-allowed bg-neutral-100 text-neutral-300"
                    : "bg-white text-neutral-600 shadow-sm ring-1 ring-neutral-200/80 active:bg-neutral-100"
                )}
              >
                {tag.name}
                {tag.is_custom ? (
                  <span className="ml-1 text-[10px] text-neutral-400">моя</span>
                ) : null}
              </button>
            ))}
          </div>
        )}
      </div>

      {!searching && hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="w-full py-1 text-center text-xs font-medium text-brand"
        >
          Ещё {hiddenCount} тегов
        </button>
      )}
      {!searching && expanded && filtered.length > COLLAPSED_LIMIT && (
        <button
          type="button"
          onClick={() => setExpanded(false)}
          className="w-full py-1 text-center text-xs font-medium text-neutral-500"
        >
          Свернуть
        </button>
      )}
    </div>
  );
}
