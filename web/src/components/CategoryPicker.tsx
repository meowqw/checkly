import { useEffect, useState } from "react";
import type { Category } from "@/api/client";
import { CategoryIcon } from "@/components/CategoryIcon";
import { cn } from "@/lib/utils";

type Props = {
  roots: Category[];
  selectedId: string;
  onChange: (id: string) => void;
  /** Сколько показывать до кнопки «Ещё» (по умолчанию 8). */
  collapsedLimit?: number;
};

/** Компактный выбор категории; порядок — как пришёл (частота с бэка / getRootCategories). */
export function CategoryPicker({
  roots,
  selectedId,
  onChange,
  collapsedLimit = 8,
}: Props) {
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!selectedId) return;
    const idx = roots.findIndex((c) => c.id === selectedId);
    if (idx >= collapsedLimit) setExpanded(true);
  }, [selectedId, roots, collapsedLimit]);

  const visible = expanded ? roots : roots.slice(0, collapsedLimit);
  const hiddenCount = Math.max(0, roots.length - collapsedLimit);

  return (
    <div>
      <p className="mb-1.5 text-xs text-neutral-500">Категория</p>
      <div className="grid grid-cols-4 gap-1">
        {visible.map((cat) => {
          const selected = selectedId === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onChange(cat.id)}
              className={cn(
                "flex flex-col items-center gap-0.5 rounded-lg border px-0.5 py-1.5 text-center transition",
                selected
                  ? "border-brand bg-brand-muted text-brand-dark"
                  : "border-neutral-100 bg-neutral-50 text-neutral-700"
              )}
            >
              <CategoryIcon
                icon={cat.icon}
                color={cat.color}
                name={cat.name}
                size="xs"
                className={cn("rounded-lg", selected ? "ring-2 ring-white/80" : undefined)}
              />
              <span className="line-clamp-2 text-[10px] font-medium leading-tight">{cat.name}</span>
            </button>
          );
        })}
      </div>
      {!expanded && hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="mt-1.5 w-full py-1 text-center text-xs font-medium text-brand"
        >
          Ещё {hiddenCount}
        </button>
      )}
      {expanded && roots.length > collapsedLimit && (
        <button
          type="button"
          onClick={() => setExpanded(false)}
          className="mt-1.5 w-full py-1 text-center text-xs font-medium text-neutral-500"
        >
          Свернуть
        </button>
      )}
    </div>
  );
}
