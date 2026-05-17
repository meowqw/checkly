import { FormEvent, useEffect, useState } from "react";
import { api, formatMoney, rublesToKopecks, type Account } from "@/api/client";
import { ApiError } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [name, setName] = useState("");
  const [balanceRub, setBalanceRub] = useState("0");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = () => api.accounts().then((r) => setAccounts(r.accounts));

  useEffect(() => {
    load();
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.createAccount({
        name,
        balance: rublesToKopecks(parseFloat(balanceRub) || 0),
      });
      setName("");
      setBalanceRub("0");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm("Удалить счёт?")) return;
    try {
      await api.deleteAccount(id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    }
  };

  return (
    <>
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Счета</h1>
        <p className="mt-1 text-neutral-500">Управление счетами</p>
      </header>

      {error && (
        <p className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <Card className="mb-6 rounded-3xl">
        <CardContent>
          <h2 className="mb-4 text-lg font-semibold">Новый счёт</h2>
          <form onSubmit={create} className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-1.5 block text-sm text-neutral-500">Название</span>
              <input className="input-field" value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label className="block">
              <span className="mb-1.5 block text-sm text-neutral-500">Начальный баланс (₽)</span>
              <input
                className="input-field"
                type="number"
                step="0.01"
                value={balanceRub}
                onChange={(e) => setBalanceRub(e.target.value)}
              />
            </label>
            <div className="md:col-span-2">
              <Button type="submit" disabled={loading}>
                Создать
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {accounts.map((a) => (
          <Card key={a.id} className="rounded-3xl">
            <CardContent className="flex items-start justify-between">
              <div>
                <div className="font-medium">{a.name}</div>
                <div className="mt-2 text-2xl font-semibold">{formatMoney(a.balance)}</div>
              </div>
              <Button variant="outline" size="sm" onClick={() => remove(a.id)}>
                Удалить
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
