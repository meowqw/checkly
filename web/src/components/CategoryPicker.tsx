import type { Category } from "@/api/client";
import { cn } from "@/lib/utils";

const CATEGORY_EMOJI: Record<string, string> = {
  Продукты: "🛒",
  Здоровье: "💊",
  Дом: "🏠",
  Транспорт: "🚗",
  Развлечения: "🎬",
  Одежда: "👕",
  Связь: "📱",
  Образование: "📚",
  Подарки: "🎁",
  Прочее: "📦",
  Зарплата: "💰",
  Подработка: "💼",
  Возвраты: "↩️",
  "Прочие доходы": "✨",
};

function emojiFor(name: string): string {
  return CATEGORY_EMOJI[name] ?? name.charAt(0).toUpperCase();
}

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
    <div className="space-y-4">
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-700">Категория</p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {roots.map((cat) => {
            const selected = parentId === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => onParentChange(cat.id)}
                className={cn(
                  "flex items-center gap-2 rounded-2xl border px-3 py-3 text-left text-sm transition",
                  selected
                    ? "border-neutral-900 bg-neutral-900 text-white shadow-sm"
                    : "border-neutral-200 bg-white hover:border-neutral-400 hover:bg-neutral-50"
                )}
              >
                <span className="text-lg leading-none">{emojiFor(cat.name)}</span>
                <span className="font-medium leading-tight">{cat.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {parentId && subcategories.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-medium text-neutral-700">Подкатегория</p>
          <div className="flex flex-wrap gap-2">
            <Chip
              label="Без уточнения"
              selected={!subcategoryId}
              onClick={() => onSubcategoryChange("")}
            />
            {subcategories.map((cat) => (
              <Chip
                key={cat.id}
                label={cat.name}
                selected={subcategoryId === cat.id}
                onClick={() => onSubcategoryChange(cat.id)}
              />
            ))}
          </div>
        </div>
      )}

      {parentId && subcategories.length === 0 && (
        <p className="text-xs text-neutral-500">Подкатегорий нет — будет сохранена выбранная категория.</p>
      )}
    </div>
  );
}

function Chip({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-4 py-2 text-sm transition",
        selected
          ? "border-neutral-900 bg-neutral-900 text-white"
          : "border-neutral-200 bg-white text-neutral-700 hover:border-neutral-400"
      )}
    >
      {label}
    </button>
  );
}
