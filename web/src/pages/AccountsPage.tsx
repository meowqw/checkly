import { FormEvent, useState } from "react";
import * as data from "@/api/data-service";
import { formatMoney, rublesToKopecks } from "@/api/client";
import { ApiError } from "@/api/client";
import { useAccounts } from "@/context/AccountsContext";
import { PageHeader } from "@/components/mobile/PageHeader";
import { Button } from "@/components/ui/button";

export default function AccountsPage() {
  const { accounts, loading: accountsLoading, error: loadError, refresh } = useAccounts();
  const [name, setName] = useState("");
  const [balanceRub, setBalanceRub] = useState("0");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

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
    if (!confirm("Удалить счёт?")) return;
    try {
      await data.deleteAccount(id);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
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
          <Button variant="ghost" size="sm" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Отмена" : "+ Новый"}
          </Button>
        }
      />

      {displayError && (
        <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {displayError}
        </p>
      )}

      {accountsLoading && accounts.length === 0 ? (
        <p className="py-12 text-center text-sm text-neutral-400">Загрузка...</p>
      ) : (
        <>
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

          <div className="list-divider overflow-hidden rounded-xl border border-neutral-100">
            {accounts.map((a) => (
              <div key={a.id} className="flex items-center justify-between px-3 py-3">
                <div>
                  <p className="text-sm font-medium">{a.name}</p>
                  <p className="text-lg font-semibold tabular-nums">{formatMoney(a.balance)}</p>
                </div>
                <Button variant="ghost" size="sm" className="text-red-500" onClick={() => remove(a.id)}>
                  Удалить
                </Button>
              </div>
            ))}
            {accounts.length === 0 && (
              <p className="px-3 py-8 text-center text-sm text-neutral-400">Нет счетов</p>
            )}
          </div>
        </>
      )}
    </>
  );
}
