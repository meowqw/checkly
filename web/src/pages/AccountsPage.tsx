import { FormEvent, useEffect, useState } from "react";
import { Check, Copy, Link2, Users } from "lucide-react";
import * as data from "@/api/data-service";
import {
  formatMoney,
  isAccountOwner,
  rublesToKopecks,
  type Account,
} from "@/api/client";
import { ApiError } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { useAccounts } from "@/context/AccountsContext";
import { useSync } from "@/context/SyncContext";
import { NoAccountsNotice } from "@/components/NoAccountsNotice";
import { PageHeader } from "@/components/mobile/PageHeader";
import { FormSkeleton } from "@/components/mobile/Skeleton";
import { Button } from "@/components/ui/button";

export default function AccountsPage() {
  const { user } = useAuth();
  const { online } = useSync();
  const { accounts, loading: accountsLoading, error: loadError, refresh } = useAccounts();
  const [name, setName] = useState("");
  const [balanceRub, setBalanceRub] = useState("0");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [joinToken, setJoinToken] = useState("");
  const [joining, setJoining] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [inviteByAccount, setInviteByAccount] = useState<Record<string, string>>({});
  const [inviteBusy, setInviteBusy] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (!accountsLoading && accounts.length === 0) {
      setShowForm(true);
    }
  }, [accountsLoading, accounts.length]);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await data.createAccount({
        name,
        balance: rublesToKopecks(parseFloat(balanceRub) || 0),
      });
      setName("");
      setBalanceRub("0");
      setShowForm(false);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm("Удалить счёт? Это может сделать только владелец.")) return;
    try {
      await data.deleteAccount(id);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    }
  };

  const invite = async (accountId: string) => {
    if (!online) {
      setError("Приглашения доступны только онлайн");
      return;
    }
    setError("");
    setInviteBusy(accountId);
    try {
      const res = await data.createAccountInvite(accountId);
      setInviteByAccount((prev) => ({ ...prev, [accountId]: res.token }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось создать приглашение");
    } finally {
      setInviteBusy(null);
    }
  };

  const copyToken = async (accountId: string, token: string) => {
    try {
      await navigator.clipboard.writeText(token);
      setCopiedId(accountId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      setError("Не удалось скопировать токен");
    }
  };

  const join = async (e: FormEvent) => {
    e.preventDefault();
    if (!online) {
      setError("Присоединение к счёту доступно только онлайн");
      return;
    }
    setError("");
    setJoining(true);
    try {
      await data.joinAccount(joinToken);
      setJoinToken("");
      setShowJoin(false);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось присоединиться");
    } finally {
      setJoining(false);
    }
  };

  const total = accounts.reduce((s, a) => s + a.balance, 0);
  const displayError = error || loadError;

  return (
    <>
      <PageHeader
        title="Счета"
        subtitle={`Всего ${formatMoney(total)}`}
        action={
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowJoin((v) => !v);
                setShowForm(false);
              }}
            >
              {showJoin ? "Отмена" : "Войти"}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowForm((v) => !v);
                setShowJoin(false);
              }}
            >
              {showForm ? "Отмена" : "+ Новый"}
            </Button>
          </div>
        }
      />

      {displayError && (
        <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {displayError}
        </p>
      )}

      {!accountsLoading && accounts.length === 0 && (
        <div className="mb-4">
          <NoAccountsNotice showAction={false} />
        </div>
      )}

      {accountsLoading && accounts.length === 0 ? (
        <FormSkeleton />
      ) : (
        <>
          {showJoin && (
            <form onSubmit={join} className="mb-4 space-y-3 rounded-xl border border-neutral-100 p-3">
              <p className="text-xs text-neutral-500">
                Введите одноразовый токен приглашения от владельца счёта
              </p>
              <label className="block">
                <span className="mb-1 block text-xs text-neutral-500">Токен</span>
                <input
                  className="input-field font-mono text-xs"
                  value={joinToken}
                  onChange={(e) => setJoinToken(e.target.value)}
                  placeholder="вставьте токен"
                  required
                  disabled={!online}
                />
              </label>
              <Button
                type="submit"
                variant="brand"
                disabled={joining || !online || !joinToken.trim()}
                className="w-full gap-2"
              >
                <Link2 size={16} />
                {joining ? "Подключение..." : "Присоединиться"}
              </Button>
              {!online && (
                <p className="text-xs text-amber-700">Нужен интернет, чтобы принять приглашение</p>
              )}
            </form>
          )}

          {showForm && (
            <form onSubmit={create} className="mb-4 space-y-3 rounded-xl border border-neutral-100 p-3">
              <label className="block">
                <span className="mb-1 block text-xs text-neutral-500">Название</span>
                <input className="input-field" value={name} onChange={(e) => setName(e.target.value)} required />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs text-neutral-500">Начальный баланс (₽)</span>
                <input
                  className="input-field"
                  type="number"
                  step="0.01"
                  value={balanceRub}
                  onChange={(e) => setBalanceRub(e.target.value)}
                />
              </label>
              <Button type="submit" variant="brand" disabled={saving} className="w-full">
                Создать
              </Button>
            </form>
          )}

          <div className="space-y-3">
            {accounts.map((a) => (
              <AccountCard
                key={a.id}
                account={a}
                userId={user?.id}
                inviteToken={inviteByAccount[a.id]}
                inviteBusy={inviteBusy === a.id}
                copied={copiedId === a.id}
                online={online}
                onInvite={() => void invite(a.id)}
                onCopy={() => {
                  const t = inviteByAccount[a.id];
                  if (t) void copyToken(a.id, t);
                }}
                onRemove={() => void remove(a.id)}
              />
            ))}
            {accounts.length === 0 && !showForm && !showJoin && (
              <p className="px-3 py-8 text-center text-sm text-neutral-400">Нет счетов</p>
            )}
          </div>
        </>
      )}
    </>
  );
}

function AccountCard({
  account,
  userId,
  inviteToken,
  inviteBusy,
  copied,
  online,
  onInvite,
  onCopy,
  onRemove,
}: {
  account: Account;
  userId?: string;
  inviteToken?: string;
  inviteBusy: boolean;
  copied: boolean;
  online: boolean;
  onInvite: () => void;
  onCopy: () => void;
  onRemove: () => void;
}) {
  const owner = isAccountOwner(account, userId);
  const members = account.members ?? [];
  const shared = members.length > 1;

  return (
    <div className="rounded-xl border border-neutral-100 px-3 py-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <p className="text-sm font-medium">{account.name}</p>
            {shared && (
              <span className="inline-flex items-center gap-0.5 rounded-md bg-neutral-100 px-1.5 py-0.5 text-[10px] font-medium text-neutral-600">
                <Users size={10} /> Общий
              </span>
            )}
            {!owner && (
              <span className="rounded-md bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-800">
                Участник
              </span>
            )}
          </div>
          <p className="mt-0.5 text-lg font-semibold tabular-nums">{formatMoney(account.balance)}</p>
        </div>
        {owner && (
          <Button variant="ghost" size="sm" className="shrink-0 text-red-500" onClick={onRemove}>
            Удалить
          </Button>
        )}
      </div>

      {members.length > 0 && (
        <ul className="mt-2 space-y-1 border-t border-neutral-50 pt-2">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between text-xs text-neutral-600">
              <span className="truncate">{m.login}</span>
              <span className="shrink-0 text-neutral-400">
                {m.role === "owner" ? "владелец" : "участник"}
              </span>
            </li>
          ))}
        </ul>
      )}

      {owner && (
        <div className="mt-2 space-y-2 border-t border-neutral-50 pt-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full gap-1.5"
            disabled={!online || inviteBusy}
            onClick={onInvite}
          >
            <Link2 size={14} />
            {inviteBusy ? "Создание..." : inviteToken ? "Новый токен" : "Пригласить"}
          </Button>
          {inviteToken && (
            <div className="flex items-center gap-2 rounded-lg bg-neutral-50 px-2 py-2">
              <code className="min-w-0 flex-1 truncate font-mono text-[11px] text-neutral-700">
                {inviteToken}
              </code>
              <Button type="button" variant="ghost" size="sm" className="shrink-0 gap-1" onClick={onCopy}>
                {copied ? <Check size={14} className="text-brand" /> : <Copy size={14} />}
                {copied ? "Скопировано" : "Копировать"}
              </Button>
            </div>
          )}
          {!online && (
            <p className="text-[11px] text-amber-700">Приглашения только при интернете</p>
          )}
        </div>
      )}
    </div>
  );
}
