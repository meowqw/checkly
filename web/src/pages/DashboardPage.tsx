import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronUp, ScanLine } from "lucide-react";
import * as data from "@/api/data-service";
import { formatMoney, type CategoryStat, type PeriodStats } from "@/api/client";
import { useAccounts } from "@/context/AccountsContext";
import { CategoryProgress } from "@/components/dashboard/CategoryProgress";
import { NoAccountsNotice } from "@/components/NoAccountsNotice";
import { PeriodNavigator } from "@/components/mobile/PeriodNavigator";
import { RefreshBar } from "@/components/mobile/RefreshBar";
import { DashboardSkeleton } from "@/components/mobile/Skeleton";
import { TxRow } from "@/components/mobile/TxRow";
import { Button } from "@/components/ui/button";
import { trackBackgroundFresh } from "@/lib/cache-first";
import { resolveTransactionDotColor } from "@/lib/categories";
import { getPeriodRange, toApiDateTimeRange, type Period } from "@/lib/dates";
import { subscribeTransactionsChanged } from "@/lib/data-events";
import { colorMapFromStats, formatStatAmount, txRowFromList } from "@/lib/stats";

type TxRowData = {
  id: string;
  title: string;
  amount: number;
  type: string;
  occurredAt: string;
  category: string;
  source?: string;
  items?: PeriodStats["recent_expenses"][number]["items"];
  dotColor?: string | null;
};

const CATEGORY_PREVIEW = 5;

export default function DashboardPage() {
  const { accounts, loading: accountsLoading } = useAccounts();
  const [period, setPeriod] = useState<Period>("day");
  const [periodAnchor, setPeriodAnchor] = useState(() => new Date());
  const [expenses, setExpenses] = useState(0);
  const [income, setIncome] = useState(0);
  const [categories, setCategories] = useState<CategoryStat[]>([]);
  const [transactions, setTransactions] = useState<TxRowData[]>([]);
  const [booting, setBooting] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [categoriesExpanded, setCategoriesExpanded] = useState(false);
  const hasEverLoaded = useRef(false);

  const range = useMemo(() => getPeriodRange(period, periodAnchor), [period, periodAnchor.getTime()]);
  const balance = accounts.reduce((s, a) => s + a.balance, 0);

  const periodParams = useMemo(
    () => toApiDateTimeRange(range.from, range.to),
    [range.from.getTime(), range.to.getTime()]
  );

  const applyStats = useCallback((stats: PeriodStats) => {
    setExpenses(stats.expense);
    setIncome(stats.income);
    setCategories(stats.categories);
    const colorMap = colorMapFromStats(stats.categories);
    setTransactions(
      stats.recent_expenses.map((t) => {
        const row = txRowFromList(t, new Map());
        return {
          ...row,
          dotColor: resolveTransactionDotColor(t, colorMap),
        };
      })
    );
  }, []);

  useEffect(() => {
    let cancelled = false;

    if (accountsLoading || accounts.length === 0) {
      if (!accountsLoading && accounts.length === 0) {
        setBooting(false);
        setLoaded(true);
      }
      return () => {
        cancelled = true;
      };
    }

    const load = async (skipRevalidate = false) => {
      if (!hasEverLoaded.current) setBooting(true);
      setError("");

      try {
        const statsRes = await data.getStats(periodParams, { skipRevalidate });
        if (cancelled) return;
        applyStats(statsRes.stats);
        hasEverLoaded.current = true;
        setLoaded(true);
        setBooting(false);
        if (!skipRevalidate) {
          trackBackgroundFresh([statsRes], setRefreshing);
        }
      } catch (err) {
        if (!cancelled && !hasEverLoaded.current) {
          setError(err instanceof Error ? err.message : "Не удалось загрузить данные");
          setBooting(false);
        }
      }
    };

    void load(false);
    const unsub = subscribeTransactionsChanged(() => {
      if (!cancelled) void load(true);
    });

    return () => {
      cancelled = true;
      unsub();
    };
  }, [periodParams, applyStats, accounts.length, accountsLoading]);

  useEffect(() => {
    setCategoriesExpanded(false);
  }, [period, periodAnchor.getTime()]);

  const visibleCategories = categoriesExpanded ? categories : categories.slice(0, CATEGORY_PREVIEW);
  const hiddenCategoryCount = Math.max(0, categories.length - CATEGORY_PREVIEW);

  if (booting && !loaded) {
    return <DashboardSkeleton />;
  }

  if (error && !loaded) {
    return <p className="py-16 text-center text-sm text-red-600">{error}</p>;
  }

  if (!accountsLoading && accounts.length === 0) {
    return (
      <div className="py-6">
        <NoAccountsNotice />
      </div>
    );
  }

  return (
    <>
      <RefreshBar active={refreshing} />

      <section className="mb-5 min-w-0 animate-scale-in">
        <p className="text-xs text-neutral-400">Общий баланс</p>
        <p className="mt-0.5 break-all text-2xl font-bold tabular-nums tracking-tight sm:text-3xl">
          {formatMoney(balance)}
        </p>
        <div className="mt-3 flex min-w-0 flex-wrap gap-x-4 gap-y-1 text-sm">
          <div className="min-w-0">
            <span className="text-neutral-400">Расходы </span>
            <span className="font-semibold tabular-nums text-neutral-800">{formatMoney(expenses)}</span>
          </div>
          <div className="min-w-0">
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
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="section-title">Категории</h2>
            <div className="flex shrink-0 items-center gap-1.5">
              {hiddenCategoryCount > 0 && (
                <button
                  type="button"
                  onClick={() => setCategoriesExpanded((v) => !v)}
                  className="inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] font-medium text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-neutral-700"
                  aria-expanded={categoriesExpanded}
                  aria-label={
                    categoriesExpanded ? "Свернуть список категорий" : `Показать ещё ${hiddenCategoryCount} категорий`
                  }
                >
                  {categoriesExpanded ? (
                    <>
                      <ChevronUp size={13} />
                      <span>Свернуть</span>
                    </>
                  ) : (
                    <>
                      <ChevronDown size={13} />
                      <span>+{hiddenCategoryCount}</span>
                    </>
                  )}
                </button>
              )}
              <span className="text-[11px] text-neutral-400">{formatMoney(expenses)}</span>
            </div>
          </div>
          <div className="space-y-3 stagger-in">
            {visibleCategories.map((c) => (
              <CategoryProgress
                key={c.name}
                name={c.name}
                amount={formatStatAmount(c.amount)}
                percent={c.percent}
                color={c.color ?? undefined}
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
            <p className="text-sm text-neutral-400">Нет трат за выбранный период</p>
            <Link to="/qr" className="mt-2 inline-block text-sm font-medium text-brand">
              Сканировать чек
            </Link>
          </div>
        ) : (
          <div className="list-divider stagger-in">
            {transactions.map((tx) => (
              <TxRow
                key={tx.id}
                title={tx.title}
                subtitle={tx.category}
                amount={tx.amount}
                type={tx.type}
                occurredAt={tx.occurredAt}
                dotColor={tx.dotColor}
              />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
