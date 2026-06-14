import { useEffect } from "react";
import { Link } from "react-router-dom";
import { PenLine, ScanLine, WifiOff } from "lucide-react";
import { useSync } from "@/context/SyncContext";
import { cn } from "@/lib/utils";

type Props = {
  open: boolean;
  onClose: () => void;
};

const ACTIONS = [
  {
    to: "/add",
    icon: PenLine,
    label: "Вручную",
    hint: "Расход или доход",
    needsOnline: false,
    delay: "fab-delay-2",
  },
  {
    to: "/qr",
    icon: ScanLine,
    label: "Чек",
    hint: "Сканировать QR",
    needsOnline: true,
    delay: "fab-delay-1",
  },
] as const;

export function FabActionMenu({ open, onClose }: Props) {
  const { online } = useSync();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <button
        type="button"
        aria-label="Закрыть меню"
        className="fixed inset-0 z-40 animate-fade-in bg-black/30 backdrop-blur-[1px] lg:hidden"
        onClick={onClose}
      />

      <div className="fixed bottom-[calc(4.5rem+env(safe-area-inset-bottom))] left-1/2 z-50 flex w-[min(100%,280px)] -translate-x-1/2 flex-col gap-2 px-4 lg:hidden">
        {ACTIONS.map((action) => {
          const disabled = action.needsOnline && !online;
          const Icon = action.icon;
          const content = (
            <>
              <span
                className={cn(
                  "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
                  disabled ? "bg-neutral-100 text-neutral-400" : "bg-brand text-white shadow-md shadow-brand/25"
                )}
              >
                <Icon size={18} />
              </span>
              <span className="min-w-0 flex-1 text-left">
                <span className="block text-sm font-semibold">{action.label}</span>
                <span className="block text-[11px] text-neutral-400">
                  {disabled ? "Нужен интернет" : action.hint}
                </span>
              </span>
              {disabled && <WifiOff size={14} className="shrink-0 text-neutral-300" />}
            </>
          );

          const className = cn(
            "flex items-center gap-3 rounded-2xl border border-neutral-100 bg-white px-3 py-2.5 shadow-lg shadow-black/10",
            "animate-fab-rise",
            action.delay,
            disabled ? "cursor-not-allowed" : "active:scale-[0.98] transition-transform"
          );

          if (disabled) {
            return (
              <div key={action.to} className={className}>
                {content}
              </div>
            );
          }

          return (
            <Link key={action.to} to={action.to} className={className} onClick={onClose}>
              {content}
            </Link>
          );
        })}
      </div>
    </>
  );
}

export function FabButton({ open, onClick }: { open: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-label={open ? "Закрыть" : "Добавить"}
      aria-expanded={open}
      onClick={onClick}
      className="mx-1 -mt-5 flex flex-col items-center"
    >
      <span
        className={cn(
          "flex h-12 w-12 items-center justify-center rounded-full bg-brand text-white shadow-lg shadow-brand/30",
          "transition-all duration-300 ease-out",
          open && "rotate-45 scale-105 bg-neutral-800 shadow-black/20"
        )}
      >
        <PlusIcon open={open} />
      </span>
    </button>
  );
}

function PlusIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      className={cn("transition-transform duration-300", open && "scale-110")}
    >
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}
