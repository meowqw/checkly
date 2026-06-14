import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import * as data from "@/api/data-service";
import { rublesToKopecks, type Category } from "@/api/client";
import { ApiError } from "@/api/client";
import { useAccounts } from "@/context/AccountsContext";
import { CategoryPicker } from "@/components/CategoryPicker";
import { Button } from "@/components/ui/button";
import { getRootCategories, getSubcategories } from "@/lib/categories";
import { toApiDateTimeLocal, toDateTimeLocalValue } from "@/lib/dates";
import { cn } from "@/lib/utils";

export default function AddTransactionPage() {
  const navigate = useNavigate();
  const { accounts, loading: accountsLoading } = useAccounts();
  const [categoryTree, setCategoryTree] = useState<Category[]>([]);
  const [accountId, setAccountId] = useState("");
  const [type, setType] = useState<"expense" | "income">("expense");
  const [parentCategoryId, setParentCategoryId] = useState("");
  const [subcategoryId, setSubcategoryId] = useState("");
  const [amountRub, setAmountRub] = useState("");
  const [comment, setComment] = useState("");
  const [occurredAt, setOccurredAt] = useState(() => toDateTimeLocalValue());
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  const rootCategories = useMemo(
    () => getRootCategories(categoryTree, type),
    [categoryTree, type]
  );

  const subcategories = useMemo(
    () => (parentCategoryId ? getSubcategories(categoryTree, parentCategoryId) : []),
    [categoryTree, parentCategoryId]
  );

  useEffect(() => {
    if (accounts[0] && !accountId) setAccountId(accounts[0].id);
  }, [accounts, accountId]);

  useEffect(() => {
    data
      .getCategories()
      .then((cat) => setCategoryTree(cat.categories))
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить данные");
      })
      .finally(() => setInitialLoading(false));
  }, []);

  useEffect(() => {
    setParentCategoryId("");
    setSubcategoryId("");
  }, [type]);

  useEffect(() => {
    setSubcategoryId("");
  }, [parentCategoryId]);

  const finalCategoryId = subcategoryId || parentCategoryId || undefined;

  const setNow = () => setOccurredAt(toDateTimeLocalValue(new Date()));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const rub = parseFloat(amountRub);
      if (!rub || rub <= 0) throw new Error("Укажите сумму");
      await data.createTransaction({
        account_id: accountId,
        type,
        amount: rublesToKopecks(rub),
        currency: "RUB",
        occurred_at: toApiDateTimeLocal(occurredAt),
        category_id: finalCategoryId,
        comment: comment || undefined,
      });
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="-mx-4 px-4 md:mx-0 md:px-0">
      {initialLoading || accountsLoading ? (
        <p className="py-16 text-center text-sm text-neutral-400">Загрузка...</p>
      ) : (
        <>
      <Link
        to="/"
        className="mb-3 inline-flex items-center gap-1.5 text-sm text-neutral-500 active:text-neutral-900"
      >
        <ArrowLeft size={16} /> Назад
      </Link>

      <header className="mb-4">
        <h1 className="text-lg font-semibold">Новая операция</h1>
      </header>

      {error && (
        <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <form onSubmit={submit} className="space-y-4">
        <label className="block">
          <input
            className="w-full border-0 bg-transparent py-2 text-4xl font-bold tabular-nums outline-none placeholder:text-neutral-300"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0"
            value={amountRub}
            onChange={(e) => setAmountRub(e.target.value)}
            required
            autoFocus
          />
          <span className="text-sm text-neutral-400">₽</span>
        </label>

        <div className="flex border-b border-neutral-100">
          {(["expense", "income"] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setType(t)}
              className={cn(
                "relative flex-1 py-2 text-sm font-medium",
                type === t ? "text-brand" : "text-neutral-400"
              )}
            >
              {t === "expense" ? "Расход" : "Доход"}
              {type === t && (
                <span className="absolute inset-x-4 -bottom-px h-0.5 rounded-full bg-brand" />
              )}
            </button>
          ))}
        </div>

        {accounts.length > 1 && (
          <label className="block">
            <span className="mb-1.5 block text-xs text-neutral-500">Счёт</span>
            <select
              className="input-field"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
            >
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </label>
        )}

        <CategoryPicker
          roots={rootCategories}
          subcategories={subcategories}
          parentId={parentCategoryId}
          subcategoryId={subcategoryId}
          onParentChange={setParentCategoryId}
          onSubcategoryChange={setSubcategoryId}
        />

        <label className="block">
          <div className="mb-1 flex items-center justify-between">
            <span className="text-xs text-neutral-500">Дата и время</span>
            <button type="button" onClick={setNow} className="text-xs font-medium text-brand">
              Сейчас
            </button>
          </div>
          <input
            className="input-field"
            type="datetime-local"
            value={occurredAt}
            onChange={(e) => setOccurredAt(e.target.value)}
            required
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs text-neutral-500">Комментарий</span>
          <input
            className="input-field"
            placeholder="Обед, такси..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
        </label>

        <Button type="submit" variant="brand" className="w-full" size="lg" disabled={loading || !accountId}>
          {loading ? "Сохранение..." : "Сохранить"}
        </Button>
      </form>
        </>
      )}
    </div>
  );
}
