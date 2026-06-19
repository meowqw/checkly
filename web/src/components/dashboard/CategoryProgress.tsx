import { cn } from "@/lib/utils";

type Props = { name: string; amount: string; percent: number; color?: string };

const BAR_COLORS = ["bg-brand", "bg-blue-500", "bg-amber-500", "bg-violet-500", "bg-rose-500"];

export function CategoryProgress({ name, amount, percent, color }: Props) {
  const barColorClass = color ? undefined : BAR_COLORS[Math.abs(name.charCodeAt(0)) % BAR_COLORS.length];
  const barStyle = color ? { width: `${percent}%`, backgroundColor: color } : { width: `${percent}%` };

  return (
    <div className="flex items-center gap-3">
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center justify-between gap-2">
          <span className="truncate text-sm">{name}</span>
          <span className="shrink-0 text-xs font-semibold tabular-nums text-neutral-600">{amount}</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-neutral-100">
          <div
            className={cn("h-full rounded-full transition-all duration-700 ease-out", barColorClass)}
            style={barStyle}
          />
        </div>
      </div>
      <span className="w-8 shrink-0 text-right text-[11px] text-neutral-400">{percent}%</span>
    </div>
  );
}
