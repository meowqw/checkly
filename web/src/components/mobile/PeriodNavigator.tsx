import { useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { PeriodTabs } from "@/components/mobile/PeriodTabs";
import {
  canGoPeriodNext,
  getPeriodRange,
  shiftPeriodAnchor,
  type Period,
} from "@/lib/dates";
import { cn } from "@/lib/utils";

type Props = {
  period: Period;
  anchor: Date;
  onPeriodChange: (p: Period) => void;
  onAnchorChange: (d: Date) => void;
  className?: string;
};

export function PeriodNavigator({
  period,
  anchor,
  onPeriodChange,
  onAnchorChange,
  className,
}: Props) {
  const range = useMemo(() => getPeriodRange(period, anchor), [period, anchor.getTime()]);
  const canNext = canGoPeriodNext(period, anchor);

  const handlePeriodChange = (p: Period) => {
    onPeriodChange(p);
    onAnchorChange(new Date());
  };

  return (
    <div className={className}>
      <PeriodTabs value={period} onChange={handlePeriodChange} className="mb-2" />
      <div className="mb-3 flex items-center gap-1">
        <button
          type="button"
          onClick={() => onAnchorChange(shiftPeriodAnchor(period, range.anchor, -1))}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-neutral-500 transition active:bg-neutral-100"
          aria-label="Предыдущий период"
        >
          <ChevronLeft size={20} />
        </button>
        <p className="min-w-0 flex-1 truncate text-center text-xs text-neutral-500">{range.label}</p>
        <button
          type="button"
          disabled={!canNext}
          onClick={() => onAnchorChange(shiftPeriodAnchor(period, range.anchor, 1))}
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition",
            canNext ? "text-neutral-500 active:bg-neutral-100" : "text-neutral-200"
          )}
          aria-label="Следующий период"
        >
          <ChevronRight size={20} />
        </button>
      </div>
    </div>
  );
}
