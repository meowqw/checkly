import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronUp, ReceiptText, ScanLine } from "lucide-react";
import { api, formatMoney, type Account } from "@/api/client";
import { ApiError } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PeriodButton } from "@/components/dashboard/PeriodButton";
import { getPeriodRange, toApiDateTimeRange, type Period } from "@/lib/dates";
import {
  formatFullDate,
  groupByDate,
  sourceLabel,
  type TransactionListItem,
} from "@/lib/transactions";
import { cn } from "@/lib/utils";

export default function TransactionsPage() {
  const [period, setPeriod] = useState<Period>("month");
  const [transactions, setTransactions] = useState<TransactionListItem[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [type, setType] = useState<"" | "expense" | "income">("");
  const [accountId, setAccountId] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const range = useMemo(() => getPeriodRange(period), [period]);

  useEffect(() => {
    api.accounts().then((r) => setAccounts(r.accounts));
  }, []);

  const load = () => {
    setLoading(true);
    const params: Record<string, string> = toApiDateTimeRange(range.from, range.to);
    if (type) params.type = type;
    if (accountId) params.account_id = accountId;
    api
      .transactions(params)
      .then((r) => setTransactions(r.transactions as TransactionListItem[]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [range.from.getTime(), range.to.getTime(), type, accountId]);

  const grouped = useMemo(() => groupByDate(transactions), [transactions]);

  const totals = useMemo(() => {
    let expense = 0;
    let income = 0;
    for (const t of transactions) {
      if (t.type === "expense") expense += t.amount;
      else income += t.amount;
    }
    return { expense, income, count: transactions.length };
  }, [transactions]);

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const remove = async (id: string) => {
    if (!confirm("Удалить операцию?")) return;
    try {
      await api.deleteTransaction(id);
      load();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Ошибка");
    }
  };

  return (
    <>
      <header className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Транзакции</h1>
          <p className="mt-1 text-neutral-500">
            {totals.count > 0
              ? `${totals.count} операций за период`
              : "История доходов и расходов"}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/add">
            <Button variant="outline" className="gap-2">
              <ReceiptText size={16} /> Добавить
            </Button>
          </Link>
          <Link to="/qr">
            <Button className="gap-2">
              <ScanLine size={16} /> QR-чек
            </Button>
          </Link>
        </div>
      </header>

      <section className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <SummaryCard label="Расходы" value={formatMoney(totals.expense)} />
        <SummaryCard label="Доходы" value={formatMoney(totals.income)} highlight />
        <SummaryCard
          label="Баланс периода"
          value={formatMoney(totals.income - totals.expense)}
        />
      </section>

      <section className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="inline-flex w-fit rounded-2xl border border-neutral-200 bg-white p-1 shadow-sm">
          <PeriodButton label="Сегодня" active={period === "day"} onClick={() => setPeriod("day")} />
          <PeriodButton label="Неделя" active={period === "week"} onClick={() => setPeriod("week")} />
          <PeriodButton label="Месяц" active={period === "month"} onClick={() => setPeriod("month")} />
        </div>
        <p className="text-sm text-neutral-500">{range.label}</p>
      </section>

      <div className="mb-4 flex flex-wrap gap-2">
        <FilterChip active={type === ""} onClick={() => setType("")}>
          Все
        </FilterChip>
        <FilterChip active={type === "expense"} onClick={() => setType("expense")}>
          Расходы
        </FilterChip>
        <FilterChip active={type === "income"} onClick={() => setType("income")}>
          Доходы
        </FilterChip>
        <span className="mx-1 w-px self-stretch bg-neutral-200" />
        <FilterChip active={accountId === ""} onClick={() => setAccountId("")}>
          Все счета
        </FilterChip>
        {accounts.map((a) => (
          <FilterChip key={a.id} active={accountId === a.id} onClick={() => setAccountId(a.id)}>
            {a.name}
          </FilterChip>
        ))}
      </div>

      {loading ? (
        <p className="py-12 text-center text-neutral-500">Загрузка...</p>
      ) : transactions.length === 0 ? (
        <Card className="rounded-3xl">
          <CardContent className="py-12 text-center text-neutral-500">
            Нет операций за выбранный период
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {grouped.map((group) => (
            <section key={group.label}>
              <h2 className="mb-3 text-sm font-semibold text-neutral-500">{group.label}</h2>
              <div className="space-y-3">
                {group.items.map((tx) => (
                  <TransactionCard
                    key={tx.id}
                    tx={tx}
                    expanded={expanded.has(tx.id)}
                    onToggle={() => toggleExpand(tx.id)}
                    onDelete={() => remove(tx.id)}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </>
  );
}

function SummaryCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <Card className="rounded-2xl">
      <CardContent className="px-4 py-3">
        <p className="text-sm text-neutral-500">{label}</p>
        <p className={cn("mt-1 text-lg font-semibold", highlight && "text-green-700")}>{value}</p>
      </CardContent>
    </Card>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1.5 text-sm transition",
        active
          ? "border-neutral-900 bg-neutral-900 text-white"
          : "border-neutral-200 bg-white text-neutral-600 hover:border-neutral-400"
      )}
    >
      {children}
    </button>
  );
}

function TransactionCard({
  tx,
  expanded,
  onToggle,
  onDelete,
}: {
  tx: TransactionListItem;
  expanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const hasItems = (tx.items_count ?? 0) > 0;
  const isExpense = tx.type === "expense";

  return (
    <Card className="overflow-hidden rounded-3xl">
      <CardContent className="p-0">
        <div className="flex gap-4 p-4 md:p-5">
          <div
            className={cn(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-lg",
              isExpense ? "bg-neutral-100" : "bg-green-50"
            )}
          >
            {tx.source === "qr_receipt" ? "🧾" : isExpense ? "↓" : "↑"}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="truncate font-semibold">{tx.title}</h3>
                <p className="mt-0.5 text-xs text-neutral-500">{formatFullDate(tx.occurred_at)}</p>
              </div>
              <p
                className={cn(
                  "shrink-0 text-lg font-semibold",
                  isExpense ? "text-neutral-900" : "text-green-700"
                )}
              >
                {isExpense ? "−" : "+"}
                {formatMoney(tx.amount)}
              </p>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <Badge>{sourceLabel(tx.source)}</Badge>
              <Badge variant="secondary">{isExpense ? "Расход" : "Доход"}</Badge>
              {tx.account && <Badge variant="secondary">{tx.account.name}</Badge>}
              {tx.category && <Badge variant="secondary">{tx.category}</Badge>}
              {tx.merchant && tx.source === "qr_receipt" && (
                <Badge variant="secondary">{tx.merchant.name}</Badge>
              )}
            </div>

            {tx.comment && tx.comment !== tx.title && (
              <p className="mt-2 text-sm text-neutral-600">{tx.comment}</p>
            )}

            {hasItems && (
              <button
                type="button"
                onClick={onToggle}
                className="mt-3 flex items-center gap-1 text-sm font-medium text-neutral-600 hover:text-neutral-900"
              >
                {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                {tx.items_count} {itemsWord(tx.items_count ?? 0)}
              </button>
            )}
          </div>
        </div>

        {expanded && tx.items && tx.items.length > 0 && (
          <ul className="border-t border-neutral-100 bg-neutral-50 px-4 py-3 md:px-5">
            {tx.items.map((item, i) => (
              <li
                key={item.id ?? i}
                className="flex items-center justify-between gap-3 border-b border-neutral-100 py-2.5 last:border-0"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{item.raw_name}</p>
                  {item.category?.name && (
                    <p className="text-xs text-neutral-500">{item.category.name}</p>
                  )}
                </div>
                <span className="shrink-0 text-sm font-semibold">{formatMoney(item.amount)}</span>
              </li>
            ))}
          </ul>
        )}

        <div className="flex justify-end border-t border-neutral-100 px-4 py-2 md:px-5">
          <Button variant="ghost" size="sm" onClick={onDelete}>
            Удалить
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function itemsWord(n: number): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return "позиция";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return "позиции";
  return "позиций";
}
