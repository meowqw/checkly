import { FormEvent, useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import * as data from "@/api/data-service";
import type { Category } from "@/api/client";
import { ApiError } from "@/api/client";
import { CategoryIcon } from "@/components/CategoryIcon";
import { Button } from "@/components/ui/button";
import {
  PRESET_CATEGORY_COLORS,
  PRESET_CATEGORY_ICONS,
  resolveCategoryIcon,
} from "@/lib/category-icons";
import { getRootCategories } from "@/lib/categories";
import { cn } from "@/lib/utils";

type Props = {
  open: boolean;
  type: "expense" | "income";
  categories: Category[];
  onClose: () => void;
  onCreated: () => void;
};

export function CreateCategorySheet({ open, type, categories, onClose, onCreated }: Props) {
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [icon, setIcon] = useState("tag");
  const [color, setColor] = useState(PRESET_CATEGORY_COLORS[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const roots = useMemo(
    () => getRootCategories(categories, type).filter((c) => !c.is_custom),
    [categories, type]
  );

  useEffect(() => {
    if (!open) return;
    setName("");
    setParentId("");
    setIcon("tag");
    setColor(PRESET_CATEGORY_COLORS[0]);
    setError("");
  }, [open, type]);

  if (!open) return null;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Введите название");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await data.createCategory({
        name: trimmed,
        type,
        parent_id: parentId || undefined,
        icon,
        color,
      });
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось создать категорию");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 animate-fade-in">
      <button type="button" className="absolute inset-0" aria-label="Закрыть" onClick={onClose} />
      <form
        onSubmit={(e) => void submit(e)}
        className="relative z-10 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white px-4 pb-safe-b pt-4 shadow-xl animate-slide-up"
      >
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs text-neutral-400">Новая категория</p>
            <p className="text-base font-semibold">{type === "expense" ? "Расход" : "Доход"}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-neutral-400 hover:bg-neutral-100"
          >
            <X size={18} />
          </button>
        </div>

        <p className="mb-4 text-xs text-neutral-500">
          Свои категории доступны при ручном вводе. При сканировании чеков используются только системные.
        </p>

        {error && (
          <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <label className="mb-4 block">
          <span className="mb-1.5 block text-xs text-neutral-500">Название</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Например, Хобби"
            className="w-full rounded-xl border border-neutral-200 px-3 py-2.5 text-sm outline-none focus:border-brand"
            maxLength={255}
          />
        </label>

        {roots.length > 0 && (
          <label className="mb-4 block">
            <span className="mb-1.5 block text-xs text-neutral-500">Родительская (необязательно)</span>
            <select
              value={parentId}
              onChange={(e) => setParentId(e.target.value)}
              className="w-full rounded-xl border border-neutral-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand"
            >
              <option value="">Без родителя — отдельная группа</option>
              {roots.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
        )}

        <div className="mb-4">
          <span className="mb-2 block text-xs text-neutral-500">Иконка</span>
          <div className="grid grid-cols-6 gap-2">
            {PRESET_CATEGORY_ICONS.map((preset) => {
              const Icon = resolveCategoryIcon(preset.id);
              const selected = icon === preset.id;
              return (
                <button
                  key={preset.id}
                  type="button"
                  title={preset.label}
                  onClick={() => setIcon(preset.id)}
                  className={cn(
                    "flex aspect-square items-center justify-center rounded-xl border transition",
                    selected
                      ? "border-brand bg-brand-muted text-brand-dark"
                      : "border-neutral-100 bg-neutral-50 text-neutral-600"
                  )}
                >
                  <Icon size={18} />
                </button>
              );
            })}
          </div>
        </div>

        <div className="mb-5">
          <span className="mb-2 block text-xs text-neutral-500">Цвет</span>
          <div className="flex flex-wrap gap-2">
            {PRESET_CATEGORY_COLORS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                className={cn(
                  "h-8 w-8 rounded-full border-2 transition",
                  color === c ? "border-neutral-900 scale-110" : "border-transparent"
                )}
                style={{ backgroundColor: c }}
                aria-label={`Цвет ${c}`}
              />
            ))}
          </div>
        </div>

        <div className="mb-4 flex items-center gap-3 rounded-xl bg-neutral-50 px-3 py-3">
          <CategoryIcon icon={icon} color={color} name={name || "Категория"} />
          <div>
            <p className="text-sm font-semibold">{name.trim() || "Новая категория"}</p>
            <p className="text-xs text-neutral-400">Предпросмотр</p>
          </div>
        </div>

        <Button type="submit" variant="brand" className="w-full" disabled={loading}>
          {loading ? "Создание..." : "Создать категорию"}
        </Button>
      </form>
    </div>
  );
}
