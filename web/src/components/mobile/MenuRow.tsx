import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  to?: string;
  icon: React.ReactNode;
  label: string;
  hint?: string;
  onClick?: () => void;
  danger?: boolean;
};

export function MenuRow({ to, icon, label, hint, onClick, danger }: Props) {
  const className = cn(
    "flex w-full items-center gap-3 px-4 py-3 text-left transition active:bg-neutral-50",
    danger && "text-red-600"
  );

  const content = (
    <>
      <span className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-neutral-100", danger && "bg-red-50")}>
        {icon}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium">{label}</span>
        {hint && <span className="block text-xs text-neutral-400">{hint}</span>}
      </span>
      <ChevronRight size={16} className="shrink-0 text-neutral-300" />
    </>
  );

  if (to) {
    return (
      <Link to={to} className={className}>
        {content}
      </Link>
    );
  }

  return (
    <button type="button" onClick={onClick} className={className}>
      {content}
    </button>
  );
}
