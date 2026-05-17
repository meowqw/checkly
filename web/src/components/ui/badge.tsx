import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "secondary",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: "secondary" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-xl px-2 py-0.5 text-xs font-medium",
        variant === "secondary" && "bg-neutral-100 text-neutral-600",
        className
      )}
      {...props}
    />
  );
}
