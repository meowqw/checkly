import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { api, rublesToKopecks, type Account, type Category } from "@/api/client";
import { ApiError } from "@/api/client";
import { CategoryPicker } from "@/components/CategoryPicker";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getRootCategories, getSubcategories } from "@/lib/categories";
import { fromDateTimeLocalValue, toDateTimeLocalValue } from "@/lib/dates";
import { cn } from "@/lib/utils";

export default function AddTransactionPage() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[]>([]);
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

  const rootCategories = useMemo(
    () => getRootCategories(categoryTree, type),
    [categoryTree, type]
  );

  const subcategories = useMemo(
    () => (parentCategoryId ? getSubcategories(categoryTree, parentCategoryId) : []),
    [categoryTree, parentCategoryId]
  );

  useEffect(() => {
    Promise.all([api.accounts(), api.categories()]).then(([acc, cat]) => {
      setAccounts(acc.accounts);
      if (acc.accounts[0]) setAccountId(acc.accounts[0].id);
      setCategoryTree(cat.categories);
    });
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
      await api.createTransaction({
        account_id: accountId,
        type,
        amount: rublesToKopecks(rub),
        currency: "RUB",
        occurred_at: fromDateTimeLocalValue(occurredAt),
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
    <>
      <Link to="/" className="mb-4 inline-flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-900">
        <ArrowLeft size={16} /> Назад
      </Link>
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Добавить операцию</h1>
        <p className="mt-1 text-neutral-500">Нажмите на категорию, затем на подкатегорию</p>
      </header>

      {error && (
        <p className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <Card className="max-w-2xl rounded-3xl">
        <CardContent>
          <form onSubmit={submit} className="space-y-5">
            <div className="inline-flex rounded-2xl border border-neutral-200 bg-neutral-50 p-1">
              {(["expense", "income"] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setType(t)}
                  className={cn(
                    "rounded-xl px-4 py-2 text-sm font-medium transition",
                    type === t ? "bg-white text-neutral-900 shadow-sm" : "text-neutral-500"
                  )}
                >
                  {t === "expense" ? "Расход" : "Доход"}
                </button>
              ))}
            </div>

            {accounts.length > 1 ? (
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-neutral-700">Счёт</span>
                <div className="flex flex-wrap gap-2">
                  {accounts.map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      onClick={() => setAccountId(a.id)}
                      className={cn(
                        "rounded-full border px-4 py-2 text-sm transition",
                        accountId === a.id
                          ? "border-neutral-900 bg-neutral-900 text-white"
                          : "border-neutral-200 bg-white hover:border-neutral-400"
                      )}
                    >
                      {a.name}
                    </button>
                  ))}
                </div>
              </label>
            ) : (
              <input type="hidden" value={accountId} readOnly />
            )}

            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-neutral-700">Сумма (₽)</span>
              <input
                className="input-field text-lg font-semibold"
                type="number"
                step="0.01"
                min="0.01"
                placeholder="0"
                value={amountRub}
                onChange={(e) => setAmountRub(e.target.value)}
                required
              />
            </label>

            <CategoryPicker
              roots={rootCategories}
              subcategories={subcategories}
              parentId={parentCategoryId}
              subcategoryId={subcategoryId}
              onParentChange={setParentCategoryId}
              onSubcategoryChange={setSubcategoryId}
            />

            <label className="block">
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-sm font-medium text-neutral-700">Дата и время</span>
                <button
                  type="button"
                  onClick={setNow}
                  className="text-xs font-medium text-neutral-500 hover:text-neutral-900"
                >
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
              <span className="mb-1.5 block text-sm font-medium text-neutral-700">Комментарий</span>
              <input
                className="input-field"
                placeholder="Например: обед, такси..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
            </label>

            <Button type="submit" className="w-full" disabled={loading || !accountId}>
              {loading ? "Сохранение..." : "Сохранить"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </>
  );
}
