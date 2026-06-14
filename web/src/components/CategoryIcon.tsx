import { cn } from "@/lib/utils";
import { resolveCategoryColor, resolveCategoryIcon } from "@/lib/category-icons";

type Props = {
  icon?: string | null;
  color?: string | null;
  name?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
};

const SIZE = {
  sm: { box: "h-7 w-7", icon: 14 },
  md: { box: "h-9 w-9", icon: 18 },
  lg: { box: "h-11 w-11", icon: 22 },
};

export function CategoryIcon({ icon, color, name, size = "md", className }: Props) {
  const Icon = resolveCategoryIcon(icon, name);
  const bg = resolveCategoryColor(color, name);
  const s = SIZE[size];

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-xl text-white shadow-sm",
        s.box,
        className
      )}
      style={{ backgroundColor: bg }}
    >
      <Icon size={s.icon} strokeWidth={2.2} />
    </span>
  );
}
