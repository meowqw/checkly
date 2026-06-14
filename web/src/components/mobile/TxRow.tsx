import { ChevronRight } from "lucide-react";
import { formatMoney } from "@/api/client";
import { formatTxDate } from "@/lib/dates";
import { cn } from "@/lib/utils";

const DOT_COLORS = [
  "bg-brand",
  "bg-blue-500",
  "bg-amber-500",
  "bg-violet-500",
  "bg-rose-500",
  "bg-cyan-500",
];

type Props = {
  title: string;
  subtitle?: string;
  amount: number;
  type?: "expense" | "income" | string;
  occurredAt?: string;
  category?: string;
  colorIndex?: number;
  onClick?: () => void;
  trailing?: React.ReactNode;
};

export function TxRow({
  title,
  subtitle,
  amount,
  type = "expense",
  occurredAt,
  category,
  colorIndex = 0,
  onClick,
  trailing,
}: Props) {
  const isExpense = type === "expense";
  const meta = subtitle ?? (occurredAt ? formatTxDate(occurredAt) : category);

  const inner = (
    <>
      <span
        className={cn("mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full", DOT_COLORS[colorIndex % DOT_COLORS.length])}
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{title}</p>
        {meta && <p className="truncate text-xs text-neutral-400">{meta}</p>}
      </div>
      <div className="shrink-0 text-right">
        <p className={cn("text-sm font-semibold tabular-nums", isExpense ? "text-neutral-900" : "text-brand")}>
          {isExpense ? "−" : "+"}
          {formatMoney(amount)}
        </p>
        {trailing}
      </div>
      {onClick && <ChevronRight size={16} className="shrink-0 text-neutral-300" />}
    </>
  );

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className="flex w-full items-start gap-3 py-2.5 text-left tap-scale rounded-lg">
        {inner}
      </button>
    );
  }

  return <div className="flex items-start gap-3 py-2.5">{inner}</div>;
}
