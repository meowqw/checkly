import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { Home, PieChart, ReceiptText, ScanLine, Settings, Wallet } from "lucide-react";
import { api, formatMoney, type Account } from "@/api/client";
import { Card, CardContent } from "@/components/ui/card";
import { MenuItem } from "@/components/dashboard/MenuItem";
import { cn } from "@/lib/utils";

export default function Layout() {
  const location = useLocation();
  const [primaryAccount, setPrimaryAccount] = useState<Account | null>(null);

  useEffect(() => {
    api.accounts().then((r) => {
      if (r.accounts[0]) setPrimaryAccount(r.accounts[0]);
    });
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-neutral-100 text-neutral-950">
      <div className="flex min-h-screen pb-20 md:pb-0">
        <aside className="hidden w-64 flex-col justify-between border-r border-neutral-200 bg-white p-5 md:flex">
          <div>
            <Brand />
            <nav className="mt-8 space-y-1">
              <MenuItem to="/" end icon={<Home size={18} />} label="Главная" />
              <MenuItem to="/accounts" icon={<Wallet size={18} />} label="Счета" />
              <MenuItem to="/transactions" icon={<ReceiptText size={18} />} label="Транзакции" />
              <MenuItem to="/categories" icon={<PieChart size={18} />} label="Категории" />
              <MenuItem to="/settings" icon={<Settings size={18} />} label="Настройки" />
            </nav>
          </div>

          {primaryAccount && (
            <Card className="rounded-2xl shadow-sm">
              <CardContent className="p-4">
                <div className="mb-1 text-sm font-medium">{primaryAccount.name}</div>
                <div className="text-2xl font-semibold">{formatMoney(primaryAccount.balance)}</div>
                <div className="mt-1 text-xs text-neutral-500">доступный баланс</div>
              </CardContent>
            </Card>
          )}
        </aside>

        <main className="flex-1 p-4 md:p-8">
          <Outlet />
        </main>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 z-40 flex border-t border-neutral-200 bg-white px-2 py-2 md:hidden">
        <MobileTab to="/" icon={<Home size={20} />} label="Главная" end />
        <MobileTab to="/transactions" icon={<ReceiptText size={20} />} label="Операции" />
        <MobileTab to="/accounts" icon={<Wallet size={20} />} label="Счета" />
        <MobileTab to="/settings" icon={<Settings size={20} />} label="Ещё" />
      </nav>

      <div className="fixed bottom-20 right-4 z-50 flex gap-2 md:bottom-4">
        <Link
          to="/add"
          className="flex h-11 w-11 items-center justify-center rounded-2xl border border-neutral-200 bg-white shadow-md"
        >
          <ReceiptText size={18} />
        </Link>
        <Link
          to="/qr"
          className="flex h-11 items-center gap-2 rounded-2xl bg-neutral-900 px-3 text-sm font-medium text-white shadow-md"
        >
          <ScanLine size={16} /> Чек
        </Link>
      </div>
    </div>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-neutral-900 text-white">
        <ReceiptText size={20} />
      </div>
      <div>
        <div className="text-lg font-semibold">Checkly</div>
        <div className="text-xs text-neutral-500">учёт расходов</div>
      </div>
    </div>
  );
}

function MobileTab({
  to,
  icon,
  label,
  end,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
  end?: boolean;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1 text-[10px]",
          isActive ? "text-neutral-900" : "text-neutral-500"
        )
      }
    >
      {icon}
      {label}
    </NavLink>
  );
}
