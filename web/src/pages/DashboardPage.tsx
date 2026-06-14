import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ScanLine } from "lucide-react";
import * as data from "@/api/data-service";
import { formatMoney } from "@/api/client";
import { useAccounts } from "@/context/AccountsContext";
import { CategoryProgress } from "@/components/dashboard/CategoryProgress";
import { PeriodNavigator } from "@/components/mobile/PeriodNavigator";
import { TxRow } from "@/components/mobile/TxRow";
import { Button } from "@/components/ui/button";
import { getPeriodRange, toApiDateTimeRange, type Period } from "@/lib/dates";
import { buildCategoryDisplayMap } from "@/lib/categories";
import { subscribeTransactionsChanged } from "@/lib/data-events";
import { formatStatAmount, loadCategoryStats, txRowFromList, type CategoryStat } from "@/lib/stats";

type TxRowData = {
  id: string;
  title: string;
  amount: number;
  type: string;
  occurredAt: string;
  category: string;
};

export default function DashboardPage() {
  const { accounts } = useAccounts();
  const [period, setPeriod] = useState<Period>("day");
  const [periodAnchor, setPeriodAnchor] = useState(() => new Date());
  const [expenses, setExpenses] = useState(0);
  const [income, setIncome] = useState(0);
  const [categories, setCategories] = useState<CategoryStat[]>([]);
  const [transactions, setTransactions] = useState<TxRowData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const range = useMemo(() => getPeriodRange(period, periodAnchor), [period, periodAnchor.getTime()]);
  const balance = accounts.reduce((s, a) => s + a.balance, 0);

  useEffect(() => {
    let cancelled = false;

    const load = () => {
      setLoading(true);
      setError("");
      const params = toApiDateTimeRange(range.from, range.to);
      const weekRange = getPeriodRange("week", period === "week" ? periodAnchor : new Date());
      const weekParams = toApiDateTimeRange(weekRange.from, weekRange.to);

      return Promise.all([
        data.getCategories(),
        data.getTransactions(params),
        data.getTransactions(weekParams),
      ])
        .then(([catRes, periodRes, weekRes]) => {
          if (cancelled) return;

          const periodTx = periodRes.transactions;
          setExpenses(periodTx.filter((t) => t.type === "expense").reduce((s, t) => s + t.amount, 0));
          setIncome(periodTx.filter((t) => t.type === "income").reduce((s, t) => s + t.amount, 0));

          const displayMap = buildCategoryDisplayMap(catRes.categories);
          setCategories(
            loadCategoryStats(
              periodTx.filter((t) => t.type === "expense"),
              catRes.categories
            )
          );

          const recent = weekRes.transactions
            .filter((t) => t.type === "expense")
            .slice(0, 8);
          setTransactions(recent.map((t) => txRowFromList(t, displayMap)));
        })
        .catch((err) => {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : "Не удалось загрузить данные");
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    };

    void load();
    const unsub = subscribeTransactionsChanged(() => {
      if (!cancelled) void load();
    });

    return () => {
      cancelled = true;
      unsub();
    };
  }, [range.from.getTime(), range.to.getTime(), period, periodAnchor.getTime()]);

  if (loading) {
    return <p className="py-16 text-center text-sm text-neutral-400">Загрузка...</p>;
  }

  if (error) {
    return (
      <p className="py-16 text-center text-sm text-red-600">
        {error}
      </p>
    );
  }

  return (
    <>
      <section className="mb-5 animate-scale-in">
        <p className="text-xs text-neutral-400">Общий баланс</p>
        <p className="mt-0.5 text-3xl font-bold tabular-nums tracking-tight">{formatMoney(balance)}</p>
        <div className="mt-3 flex gap-4 text-sm">
          <div>
            <span className="text-neutral-400">Расходы </span>
            <span className="font-semibold tabular-nums text-neutral-800">{formatMoney(expenses)}</span>
          </div>
          <div>
            <span className="text-neutral-400">Доходы </span>
            <span className="font-semibold tabular-nums text-brand">{formatMoney(income)}</span>
          </div>
        </div>
      </section>

      <PeriodNavigator
        period={period}
        anchor={periodAnchor}
        onPeriodChange={setPeriod}
        onAnchorChange={setPeriodAnchor}
        className="mb-4"
      />

      {categories.length > 0 && (
        <section className="mb-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="section-title">Категории</h2>
            <span className="text-[11px] text-neutral-400">{formatMoney(expenses)}</span>
          </div>
          <div className="space-y-3 stagger-in">
            {categories.slice(0, 5).map((c) => (
              <CategoryProgress
                key={c.name}
                name={c.name}
                amount={formatStatAmount(c.amount)}
                percent={c.percent}
              />
            ))}
          </div>
        </section>
      )}

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="section-title">Последние траты</h2>
          <div className="flex items-center gap-2">
            <Link to="/qr" className="hidden sm:block">
              <Button variant="ghost" size="sm" className="gap-1 text-brand">
                <ScanLine size={14} /> Чек
              </Button>
            </Link>
            <Link to="/transactions" className="text-xs font-medium text-brand">
              Все
            </Link>
          </div>
        </div>

        {transactions.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-neutral-400">Пока нет трат</p>
            <Link to="/add" className="mt-2 inline-block text-sm font-medium text-brand">
              Добавить первую
            </Link>
          </div>
        ) : (
          <div className="list-divider stagger-in">
            {transactions.map((tx, i) => (
              <TxRow
                key={tx.id}
                title={tx.title}
                subtitle={tx.category}
                amount={tx.amount}
                type={tx.type}
                occurredAt={tx.occurredAt}
                colorIndex={i}
              />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
