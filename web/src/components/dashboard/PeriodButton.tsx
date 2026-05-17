import { cn } from "@/lib/utils";

type Props = {
  label: string;
  active: boolean;
  onClick: () => void;
};

export function PeriodButton({ label, active, onClick }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-xl px-4 py-2 text-sm transition",
        active ? "bg-neutral-900 text-white" : "text-neutral-500 hover:text-neutral-900"
      )}
    >
      {label}
    </button>
  );
}
