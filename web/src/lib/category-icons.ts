import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  Briefcase,
  Car,
  Clapperboard,
  Coffee,
  Dumbbell,
  Gift,
  HeartPulse,
  Home,
  Music,
  Package,
  Palette,
  Plane,
  Shirt,
  ShoppingCart,
  Smartphone,
  Sparkles,
  Tag,
  Undo2,
  Utensils,
  Wallet,
} from "lucide-react";

export const CATEGORY_ICON_MAP: Record<string, LucideIcon> = {
  "shopping-cart": ShoppingCart,
  "heart-pulse": HeartPulse,
  home: Home,
  car: Car,
  clapperboard: Clapperboard,
  shirt: Shirt,
  smartphone: Smartphone,
  "book-open": BookOpen,
  gift: Gift,
  package: Package,
  wallet: Wallet,
  briefcase: Briefcase,
  "undo-2": Undo2,
  sparkles: Sparkles,
  coffee: Coffee,
  utensils: Utensils,
  dumbbell: Dumbbell,
  plane: Plane,
  music: Music,
  palette: Palette,
  tag: Tag,
};

/** Fallback по имени системной категории */
export const CATEGORY_NAME_ICON: Record<string, string> = {
  Продукты: "shopping-cart",
  Здоровье: "heart-pulse",
  Дом: "home",
  Транспорт: "car",
  Развлечения: "clapperboard",
  Одежда: "shirt",
  Связь: "smartphone",
  Образование: "book-open",
  Подарки: "gift",
  Прочее: "package",
  Зарплата: "wallet",
  Подработка: "briefcase",
  Возвраты: "undo-2",
  "Прочие доходы": "sparkles",
};

export const CATEGORY_NAME_COLOR: Record<string, string> = {
  Продукты: "#16a34a",
  Здоровье: "#ef4444",
  Дом: "#f59e0b",
  Транспорт: "#3b82f6",
  Развлечения: "#a855f7",
  Одежда: "#ec4899",
  Связь: "#06b6d4",
  Образование: "#6366f1",
  Подарки: "#f97316",
  Прочее: "#78716c",
  Зарплата: "#16a34a",
  Подработка: "#0891b2",
  Возвраты: "#64748b",
  "Прочие доходы": "#eab308",
};

export const PRESET_CATEGORY_ICONS: { id: string; label: string }[] = [
  { id: "tag", label: "Метка" },
  { id: "shopping-cart", label: "Покупки" },
  { id: "coffee", label: "Кофе" },
  { id: "utensils", label: "Еда" },
  { id: "heart-pulse", label: "Здоровье" },
  { id: "home", label: "Дом" },
  { id: "car", label: "Авто" },
  { id: "clapperboard", label: "Досуг" },
  { id: "shirt", label: "Одежда" },
  { id: "smartphone", label: "Связь" },
  { id: "book-open", label: "Учёба" },
  { id: "gift", label: "Подарок" },
  { id: "dumbbell", label: "Спорт" },
  { id: "plane", label: "Путешествия" },
  { id: "music", label: "Музыка" },
  { id: "palette", label: "Творчество" },
  { id: "wallet", label: "Деньги" },
  { id: "briefcase", label: "Работа" },
];

export const PRESET_CATEGORY_COLORS = [
  "#16a34a",
  "#0891b2",
  "#3b82f6",
  "#6366f1",
  "#a855f7",
  "#ec4899",
  "#ef4444",
  "#f97316",
  "#eab308",
  "#78716c",
];

export function resolveCategoryIcon(icon?: string | null, name?: string): LucideIcon {
  if (icon && CATEGORY_ICON_MAP[icon]) return CATEGORY_ICON_MAP[icon];
  if (name && CATEGORY_NAME_ICON[name] && CATEGORY_ICON_MAP[CATEGORY_NAME_ICON[name]]) {
    return CATEGORY_ICON_MAP[CATEGORY_NAME_ICON[name]];
  }
  return Tag;
}

export function resolveCategoryColor(color?: string | null, name?: string): string {
  return color ?? (name ? CATEGORY_NAME_COLOR[name] : undefined) ?? "#78716c";
}
