import type { Category } from "@/api/client";
import { CategoryIcon } from "@/components/CategoryIcon";
import { cn } from "@/lib/utils";

type Props = {
  roots: Category[];
  subcategories: Category[];
  parentId: string;
  subcategoryId: string;
  onParentChange: (id: string) => void;
  onSubcategoryChange: (id: string) => void;
};

export function CategoryPicker({
  roots,
  subcategories,
  parentId,
  subcategoryId,
  onParentChange,
  onSubcategoryChange,
}: Props) {
  return (
    <div className="space-y-3">
      <div>
        <p className="mb-2 text-xs text-neutral-500">Категория</p>
        <div className="grid grid-cols-3 gap-1.5">
          {roots.map((cat) => {
            const selected = parentId === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => onParentChange(cat.id)}
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

      {parentId && subcategories.length > 0 && (
        <div>
          <p className="mb-2 text-xs text-neutral-500">Подкатегория</p>
          <div className="flex flex-wrap gap-1.5">
            <Chip
              label="Общая"
              selected={!subcategoryId}
              onClick={() => onSubcategoryChange("")}
            />
            {subcategories.map((cat) => (
              <Chip
                key={cat.id}
                label={cat.name}
                selected={subcategoryId === cat.id}
                onClick={() => onSubcategoryChange(cat.id)}
                custom={cat.is_custom}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Chip({
  label,
  selected,
  custom,
  onClick,
}: {
  label: string;
  selected: boolean;
  custom?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1 text-xs font-medium transition",
        selected ? "bg-brand text-white" : "bg-neutral-100 text-neutral-600"
      )}
    >
      {label}
      {custom ? " · моя" : ""}
    </button>
  );
}
