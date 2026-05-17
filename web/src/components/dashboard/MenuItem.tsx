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
          "flex items-center gap-3 rounded-2xl px-3 py-2 text-sm transition",
          isActive ? "bg-neutral-900 text-white" : "text-neutral-600 hover:bg-neutral-100"
        )
      }
    >
      {icon}
      {label}
    </NavLink>
  );
}
