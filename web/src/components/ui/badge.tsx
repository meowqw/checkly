import { cn } from "@/lib/utils";

type Props = { className?: string; variant?: "default" | "secondary" };

export function Badge({ className, variant = "default", ...props }: React.HTMLAttributes<HTMLSpanElement> & Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-medium",
        variant === "default" && "bg-brand-light text-brand-dark",
        variant === "secondary" && "bg-neutral-100 text-neutral-600",
        className
      )}
      {...props}
    />
  );
}
