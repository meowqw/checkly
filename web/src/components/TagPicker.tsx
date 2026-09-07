import type { Tag } from "@/api/client";
import { cn } from "@/lib/utils";

type Props = {
  tags: Tag[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  max?: number;
};

/** Мультивыбор тегов (независимы от категории). */
export function TagPicker({ tags, selectedIds, onChange, max = 5 }: Props) {
  const toggle = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((x) => x !== id));
      return;
    }
    if (selectedIds.length >= max) return;
    onChange([...selectedIds, id]);
  };

  if (tags.length === 0) return null;

  return (
    <div>
      <p className="mb-2 text-xs text-neutral-500">
        Теги <span className="text-neutral-400">(необязательно, до {max})</span>
      </p>
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => {
          const selected = selectedIds.includes(tag.id);
          return (
            <button
              key={tag.id}
              type="button"
              onClick={() => toggle(tag.id)}
              className={cn(
                "rounded-full px-3 py-1 text-xs font-medium transition",
                selected ? "bg-brand text-white" : "bg-neutral-100 text-neutral-600"
              )}
            >
              {tag.name}
              {tag.is_custom ? " · моя" : ""}
            </button>
          );
        })}
      </div>
    </div>
  );
}
