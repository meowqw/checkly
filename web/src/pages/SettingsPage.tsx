import { useNavigate } from "react-router-dom";
import {
  LayoutGrid,
  LogOut,
  ReceiptText,
  ScanLine,
  User,
  Wallet,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useAccounts } from "@/context/AccountsContext";
import { useSync } from "@/context/SyncContext";
import { formatMoney } from "@/api/client";
import { MenuRow } from "@/components/mobile/MenuRow";
import { PageHeader } from "@/components/mobile/PageHeader";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { online } = useSync();
  const { accounts } = useAccounts();
  const navigate = useNavigate();

  const totalBalance = accounts.reduce((s, a) => s + a.balance, 0);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <>
      <PageHeader title="Ещё" subtitle="Настройки и разделы" />

      <div className="mb-5 rounded-xl bg-brand-muted px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand text-white">
            <User size={18} />
          </span>
          <div className="min-w-0">
            <p className="truncate font-semibold">{user?.login}</p>
            <p className="truncate text-xs text-neutral-500">{user?.email}</p>
          </div>
        </div>
        {accounts.length > 0 && (
          <p className="mt-3 text-sm">
            <span className="text-neutral-500">Баланс </span>
            <span className="font-semibold tabular-nums">{formatMoney(totalBalance)}</span>
          </p>
        )}
      </div>

      <nav className="overflow-hidden rounded-xl border border-neutral-100">
        <MenuRow to="/qr" icon={<ScanLine size={16} className="text-brand" />} label="Сканировать чек" hint={online ? undefined : "Нужен интернет"} />
        <MenuRow to="/add" icon={<ReceiptText size={16} className="text-brand" />} label="Добавить операцию" />
        <MenuRow to="/accounts" icon={<Wallet size={16} className="text-brand" />} label="Счета" hint={`${accounts.length} сч.`} />
        <MenuRow to="/categories" icon={<LayoutGrid size={16} className="text-brand" />} label="Категории" />
      </nav>

      <nav className="mt-4 overflow-hidden rounded-xl border border-neutral-100">
        <MenuRow
          icon={<LogOut size={16} />}
          label="Выйти"
          onClick={handleLogout}
          danger
        />
      </nav>
    </>
  );
}
