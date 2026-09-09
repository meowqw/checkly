import { useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { PeriodTabs } from "@/components/mobile/PeriodTabs";
import {
  canGoPeriodNext,
  getCustomPeriodRange,
  getPeriodRange,
  shiftPeriodAnchor,
  toApiDate,
  type Period,
} from "@/lib/dates";
import { cn } from "@/lib/utils";

type Props = {
  period: Period;
  anchor: Date;
  onPeriodChange: (p: Period) => void;
  onAnchorChange: (d: Date) => void;
  customFrom: string;
  customTo: string;
  onCustomRangeChange: (from: string, to: string) => void;
  className?: string;
};

export function PeriodNavigator({
  period,
  anchor,
  onPeriodChange,
  onAnchorChange,
  customFrom,
  customTo,
  onCustomRangeChange,
  className,
}: Props) {
  const range = useMemo(() => {
    if (period === "custom") return getCustomPeriodRange(customFrom, customTo);
    return getPeriodRange(period, anchor);
  }, [period, anchor.getTime(), customFrom, customTo]);

  const canNext = period !== "custom" && canGoPeriodNext(period, anchor);

  const handlePeriodChange = (p: Period) => {
    if (p === "custom") {
      const month = getPeriodRange("month", new Date());
      onCustomRangeChange(toApiDate(month.from), toApiDate(month.to));
    } else {
      onAnchorChange(new Date());
    }
    onPeriodChange(p);
  };

  return (
    <div className={className}>
      <PeriodTabs value={period} onChange={handlePeriodChange} className="mb-2" />
      {period === "custom" ? (
        <div className="mb-3 grid grid-cols-2 gap-2">
          <label className="min-w-0">
            <span className="mb-1 block text-[11px] text-neutral-400">С</span>
            <input
              type="date"
              className="input-field py-2 text-xs"
              value={customFrom}
              max={customTo || undefined}
              onChange={(e) => onCustomRangeChange(e.target.value, customTo || e.target.value)}
            />
          </label>
          <label className="min-w-0">
            <span className="mb-1 block text-[11px] text-neutral-400">По</span>
            <input
              type="date"
              className="input-field py-2 text-xs"
              value={customTo}
              min={customFrom || undefined}
              onChange={(e) => onCustomRangeChange(customFrom || e.target.value, e.target.value)}
            />
          </label>
        </div>
      ) : (
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
      )}
    </div>
  );
}
