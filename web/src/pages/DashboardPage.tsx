import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarDays, Plus, ScanLine } from "lucide-react";
import {
  api,
  formatMoney,
  type Account,
  type Transaction,
  type TransactionDetail,
} from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CategoryProgress } from "@/components/dashboard/CategoryProgress";
import { CompactMetric } from "@/components/dashboard/CompactMetric";
import { PeriodButton } from "@/components/dashboard/PeriodButton";
import { getPeriodRange, toApiDateTimeRange, formatTxDate, type Period } from "@/lib/dates";
import { buildCategoryDisplayMap, getCategoryGroupName } from "@/lib/categories";
import { formatStatAmount, loadCategoryStats, type CategoryStat } from "@/lib/stats";

type TxRow = {
  id: string;
  merchant: string;
  date: string;
  amount: string;
  category: string;
};

export default function DashboardPage() {
  const [period, setPeriod] = useState<Period>("day");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [expenses, setExpenses] = useState(0);
  const [income, setIncome] = useState(0);
  const [categories, setCategories] = useState<CategoryStat[]>([]);
  const [transactions, setTransactions] = useState<TxRow[]>([]);
  const [loading, setLoading] = useState(true);

  const range = useMemo(() => getPeriodRange(period), [period]);

  useEffect(() => {
    setLoading(true);
    const params = toApiDateTimeRange(range.from, range.to);

    Promise.all([
      api.accounts(),
      api.transactions({ ...params, type: "expense" }),
      api.transactions({ ...params, type: "income" }),
      api.categories(),
    ])
      .then(async ([accRes, expRes, incRes, catRes]) => {
        setAccounts(accRes.accounts);
        const expTotal = expRes.transactions.reduce((s, t) => s + t.amount, 0);
        const incTotal = incRes.transactions.reduce((s, t) => s + t.amount, 0);
        setExpenses(expTotal);
        setIncome(incTotal);

        const displayMap = buildCategoryDisplayMap(catRes.categories);
        const stats = await loadCategoryStats(expRes.transactions, catRes.categories);
        setCategories(stats);

        const weekRange = getPeriodRange("week");
        const weekParams = toApiDateTimeRange(weekRange.from, weekRange.to);
        const recentRes = await api.transactions({ ...weekParams, type: "expense" });
        const recent = recentRes.transactions.slice(0, 6);
        const rows = await Promise.all(recent.map((t) => toTxRow(t, displayMap)));
        setTransactions(rows);
      })
      .finally(() => setLoading(false));
  }, [range.from.getTime(), range.to.getTime()]);

  const balance = accounts.reduce((s, a) => s + a.balance, 0);

  if (loading) {
    return <p className="py-12 text-center text-neutral-500">Загрузка...</p>;
  }

  return (
    <>
      <header className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Главная</h1>
          <p className="mt-1 text-neutral-500">Контроль расходов по категориям</p>
        </div>
        <div className="flex gap-2">
          <Link to="/add">
            <Button variant="outline" className="gap-2">
              <Plus size={16} /> Добавить трату
            </Button>
          </Link>
          <Link to="/qr">
            <Button className="gap-2">
              <ScanLine size={16} /> Сканировать чек
            </Button>
          </Link>
        </div>
      </header>

      <section className="mb-6 flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div className="inline-flex w-fit rounded-2xl border border-neutral-200 bg-white p-1 shadow-sm">
          <PeriodButton label="День" active={period === "day"} onClick={() => setPeriod("day")} />
          <PeriodButton label="Неделя" active={period === "week"} onClick={() => setPeriod("week")} />
          <PeriodButton label="Месяц" active={period === "month"} onClick={() => setPeriod("month")} />
        </div>
        <div className="flex w-fit items-center gap-2 rounded-2xl border border-neutral-200 bg-white px-4 py-2 text-sm text-neutral-500 shadow-sm">
          <CalendarDays size={16} /> {range.label}
        </div>
      </section>

      <section className="mb-6 grid grid-cols-1 gap-3 md:grid-cols-3">
        <CompactMetric title="Расходы" value={formatMoney(expenses)} />
        <CompactMetric title="Доходы" value={formatMoney(income)} />
        <CompactMetric title="Остаток" value={formatMoney(balance)} />
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardContent>
              <div className="mb-5 flex items-center justify-between">
                <h2 className="text-lg font-semibold">Категории расходов</h2>
                <span className="text-sm text-neutral-500">100%</span>
              </div>
              {categories.length === 0 ? (
                <p className="text-sm text-neutral-500">Нет расходов за период</p>
              ) : (
                <div className="space-y-4">
                  {categories.map((c) => (
                    <CategoryProgress
                      key={c.name}
                      name={c.name}
                      amount={formatStatAmount(c.amount)}
                      percent={c.percent}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardContent>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold">Последние траты</h2>
                <Link to="/transactions">
                  <Button variant="ghost" size="sm">
                    Все
                  </Button>
                </Link>
              </div>
              {transactions.length === 0 ? (
                <p className="text-sm text-neutral-500">Пока нет трат</p>
              ) : (
                <div className="space-y-0">
                  {transactions.map((tx) => (
                    <div
                      key={tx.id}
                      className="flex items-center justify-between border-b py-3 last:border-0"
                    >
                      <div>
                        <div className="text-sm font-medium">{tx.merchant}</div>
                        <div className="mt-1 text-xs text-neutral-500">{tx.date}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold">{tx.amount}</div>
                        <Badge className="mt-1">{tx.category}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>
    </>
  );
}

async function toTxRow(t: Transaction, displayMap: Map<string, string>): Promise<TxRow> {
  let merchant = t.comment || "Операция";
  let category = "Прочее";

  try {
    const { transaction } = await api.transaction(t.id);
    if (t.source === "qr_receipt" && transaction.merchant?.name) {
      merchant = transaction.merchant.name;
    }
    category = pickCategory(transaction, displayMap);
  } catch {
    if (t.source === "qr_receipt") merchant = "Чек";
  }

  return {
    id: t.id,
    merchant,
    date: formatTxDate(t.occurred_at),
    amount: formatMoney(t.amount),
    category,
  };
}

function pickCategory(tx: TransactionDetail, displayMap: Map<string, string>): string {
  const item = tx.items?.[0];
  if (item?.category?.name && item.category_id) {
    return displayMap.get(item.category_id) ?? item.category.name;
  }
  return getCategoryGroupName(item?.category_id, displayMap);
}
