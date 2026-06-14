import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

type Props = {
  to: string;
  icon: React.ReactNode;
  label: string;
  end?: boolean;
};

export function MenuItem({ to, icon, label, end }: Props) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition",
          isActive ? "bg-brand-muted font-medium text-brand-dark" : "text-neutral-600 hover:bg-neutral-50"
        )
      }
    >
      {icon}
      {label}
    </NavLink>
  );
}
