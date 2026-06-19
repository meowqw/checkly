import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Home,
  LayoutGrid,
  ReceiptText,
  Settings,
  Wallet,
  WifiOff,
} from "lucide-react";
import { formatMoney } from "@/api/client";
import { useAccounts } from "@/context/AccountsContext";
import { useSync } from "@/context/SyncContext";
import { MenuItem } from "@/components/dashboard/MenuItem";
import { NoAccountsNotice } from "@/components/NoAccountsNotice";
import { FabActionMenu, FabButton } from "@/components/mobile/FabActionMenu";
import { cn } from "@/lib/utils";

const HIDE_NAV = ["/add", "/qr"];

export default function Layout() {
  const location = useLocation();
  const { online, pendingCount, syncing } = useSync();
  const { primaryAccount, accounts, loading: accountsLoading } = useAccounts();
  const [fabOpen, setFabOpen] = useState(false);
  const hideNav = HIDE_NAV.some((p) => location.pathname.startsWith(p));
  const needsAccount = !accountsLoading && accounts.length === 0;
  const onAccountsPage = location.pathname.startsWith("/accounts");

  useEffect(() => {
    setFabOpen(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen overflow-x-hidden bg-white text-neutral-950">
      <div className="flex min-h-screen overflow-x-hidden">
        <aside className="hidden w-56 flex-col justify-between border-r border-neutral-100 bg-white p-4 lg:flex">
          <div>
            <Brand />
            <nav className="mt-6 space-y-0.5">
              <MenuItem to="/" end icon={<Home size={18} />} label="Главная" />
              <MenuItem to="/transactions" icon={<ReceiptText size={18} />} label="Операции" />
              <MenuItem to="/accounts" icon={<Wallet size={18} />} label="Счета" />
              <MenuItem to="/categories" icon={<LayoutGrid size={18} />} label="Категории" />
              <MenuItem to="/settings" icon={<Settings size={18} />} label="Ещё" />
            </nav>
          </div>

          {primaryAccount && (
            <div className="rounded-xl bg-brand-muted px-3 py-3 animate-scale-in">
              <div className="text-xs text-neutral-500">{primaryAccount.name}</div>
              <div className="mt-0.5 text-lg font-semibold tabular-nums">
                {formatMoney(primaryAccount.balance)}
              </div>
            </div>
          )}
        </aside>

        <main className="w-full min-w-0 flex-1 overflow-x-hidden">
          {!online && (
            <div className="animate-fade-in border-b border-amber-200 bg-amber-50 px-4 py-2 text-center text-xs text-amber-900">
              <WifiOff size={14} className="mr-1 inline" />
              Offline — чеки недоступны. Данные из кэша
              {pendingCount > 0 && ` · ${pendingCount} ждут синхронизации`}
            </div>
          )}
          {online && pendingCount > 0 && (
            <div className="animate-fade-in border-b border-brand-light bg-brand-muted px-4 py-2 text-center text-xs text-brand-dark">
              {syncing ? "Синхронизация…" : `${pendingCount} изменений отправятся на сервер`}
            </div>
          )}
          {needsAccount && !onAccountsPage && <NoAccountsNotice variant="banner" />}
          <div key={location.pathname} className="page-shell animate-page-in">
            <Outlet />
          </div>
        </main>
      </div>

      <FabActionMenu open={fabOpen && !hideNav} onClose={() => setFabOpen(false)} needsAccount={needsAccount} />

      {!hideNav && (
        <nav className="fixed bottom-0 left-0 right-0 z-40 overflow-x-hidden border-t border-neutral-100 bg-white/95 pb-safe-b backdrop-blur-md lg:hidden">
          <div className="mx-auto flex w-full max-w-lg items-end px-1 pt-1">
            <MobileTab to="/" icon={<Home size={20} />} label="Главная" end />
            <MobileTab to="/transactions" icon={<ReceiptText size={20} />} label="Операции" />
            <FabButton open={fabOpen} onClick={() => setFabOpen((v) => !v)} />
            <MobileTab to="/accounts" icon={<Wallet size={20} />} label="Счета" />
            <MobileTab to="/settings" icon={<Settings size={20} />} label="Ещё" />
          </div>
        </nav>
      )}
    </div>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5 px-1">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand text-white">
        <ReceiptText size={18} />
      </div>
      <div>
        <div className="text-base font-semibold">Checkly</div>
        <div className="text-[11px] text-neutral-400">учёт расходов</div>
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
          "flex flex-1 flex-col items-center gap-0.5 py-1.5 text-[10px] font-medium transition-all duration-200",
          isActive ? "text-brand" : "text-neutral-400 active:opacity-80"
        )
      }
    >
      {icon}
      {label}
    </NavLink>
  );
}
