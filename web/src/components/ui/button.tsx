import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm";
};

export function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition disabled:opacity-50",
        size === "default" && "px-4 py-2 text-sm",
        size === "sm" && "px-3 py-1.5 text-xs",
        variant === "default" && "rounded-2xl bg-neutral-900 text-white hover:bg-neutral-800",
        variant === "outline" && "rounded-2xl border border-neutral-200 bg-white text-neutral-900 hover:bg-neutral-50",
        variant === "ghost" && "rounded-xl text-neutral-600 hover:bg-neutral-100",
        className
      )}
      {...props}
    />
  );
}
