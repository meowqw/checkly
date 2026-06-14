import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline" | "ghost" | "brand";
  size?: "default" | "sm" | "lg";
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
        "inline-flex items-center justify-center font-medium transition-all duration-150 active:scale-[0.97] disabled:opacity-50",
        size === "default" && "rounded-xl px-4 py-2.5 text-sm",
        size === "sm" && "rounded-lg px-3 py-1.5 text-xs",
        size === "lg" && "rounded-xl px-4 py-3 text-base",
        variant === "default" && "bg-neutral-900 text-white hover:bg-neutral-800",
        variant === "brand" && "bg-brand text-white hover:bg-brand-dark",
        variant === "outline" && "border border-neutral-200 bg-white text-neutral-900 hover:bg-neutral-50",
        variant === "ghost" && "rounded-lg text-neutral-600 hover:bg-neutral-100",
        className
      )}
      {...props}
    />
  );
}
