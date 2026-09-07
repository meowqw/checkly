import type { Category } from "@/api/client";
import { CategoryIcon } from "@/components/CategoryIcon";
import { cn } from "@/lib/utils";

type Props = {
  roots: Category[];
  selectedId: string;
  onChange: (id: string) => void;
};

export function CategoryPicker({ roots, selectedId, onChange }: Props) {
  return (
    <div>
      <p className="mb-2 text-xs text-neutral-500">Категория</p>
      <div className="grid grid-cols-3 gap-1.5">
        {roots.map((cat) => {
          const selected = selectedId === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onChange(cat.id)}
              className={cn(
                "flex flex-col items-center gap-1.5 rounded-xl border px-1 py-2.5 text-center text-xs transition",
                selected
                  ? "border-brand bg-brand-muted text-brand-dark"
                  : "border-neutral-100 bg-neutral-50 text-neutral-700"
              )}
            >
              <CategoryIcon
                icon={cat.icon}
                color={cat.color}
                name={cat.name}
                size="sm"
                className={selected ? "ring-2 ring-white/80" : undefined}
              />
              <span className="line-clamp-2 font-medium leading-tight">{cat.name}</span>
              {cat.is_custom && (
                <span className="text-[10px] font-normal text-neutral-400">Моя</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
