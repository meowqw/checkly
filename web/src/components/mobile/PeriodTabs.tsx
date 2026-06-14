import { cn } from "@/lib/utils";
import type { Period } from "@/lib/dates";

const LABELS: Record<Period, string> = {
  day: "День",
  week: "Неделя",
  month: "Месяц",
};

type Props = {
  value: Period;
  onChange: (p: Period) => void;
  className?: string;
};

export function PeriodTabs({ value, onChange, className }: Props) {
  return (
    <div className={cn("flex gap-1 border-b border-neutral-100", className)}>
      {(Object.keys(LABELS) as Period[]).map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onChange(p)}
          className={cn(
            "relative px-3 py-2 text-sm font-medium transition",
            value === p ? "text-brand" : "text-neutral-400"
          )}
        >
          {LABELS[p]}
          {value === p && (
            <span className="absolute inset-x-1 -bottom-px h-0.5 rounded-full bg-brand" />
          )}
        </button>
      ))}
    </div>
  );
}
