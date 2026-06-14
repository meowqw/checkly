import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, ChevronUp } from "lucide-react";
import * as data from "@/api/data-service";
import { formatMoney, type TransactionItem } from "@/api/client";
import { ApiError } from "@/api/client";
import { useAccounts } from "@/context/AccountsContext";
import { ItemCategorySheet } from "@/components/ItemCategorySheet";
import { PageHeader } from "@/components/mobile/PageHeader";
import { PeriodNavigator } from "@/components/mobile/PeriodNavigator";
import { TxRow } from "@/components/mobile/TxRow";
import { Button } from "@/components/ui/button";
import { getPeriodRange, toApiDateTimeRange, type Period } from "@/lib/dates";
import { subscribeTransactionsChanged } from "@/lib/data-events";
import { groupByDate, sourceLabel, type TransactionListItem } from "@/lib/transactions";
import { cn } from "@/lib/utils";

export default function TransactionsPage() {
  const { accounts } = useAccounts();
  const [period, setPeriod] = useState<Period>("month");
  const [periodAnchor, setPeriodAnchor] = useState(() => new Date());
  const [transactions, setTransactions] = useState<TransactionListItem[]>([]);
  const [type, setType] = useState<"" | "expense" | "income">("");
  const [accountId, setAccountId] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editItem, setEditItem] = useState<{
    txId: string;
    item: TransactionItem;
    txType: "expense" | "income";
  } | null>(null);

  const range = useMemo(() => getPeriodRange(period, periodAnchor), [period, periodAnchor.getTime()]);

  const reload = useCallback(() => {
    const params: Record<string, string> = toApiDateTimeRange(range.from, range.to);
    if (type) params.type = type;
    if (accountId) params.account_id = accountId;
    setLoading(true);
    setError("");
    return data
      .getTransactions(params)
      .then((r) => setTransactions(r.transactions as TransactionListItem[]))
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить операции");
      })
      .finally(() => setLoading(false));
  }, [range.from.getTime(), range.to.getTime(), type, accountId]);

  useEffect(() => {
    let cancelled = false;
    void reload();
    const unsub = subscribeTransactionsChanged(() => {
      if (!cancelled) void reload();
    });
    return () => {
      cancelled = true;
      unsub();
    };
  }, [reload]);

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
      await data.deleteTransaction(id);
      reload();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Ошибка");
    }
  };

  return (
    <>
      <PageHeader
        title="Операции"
        subtitle={
          totals.count > 0 ? `${totals.count} за период` : "История доходов и расходов"
        }
      />

      <div className="mb-4 flex items-baseline justify-between gap-3 rounded-xl bg-neutral-50 px-3 py-2.5">
        <div>
          <p className="text-[11px] text-neutral-400">Расходы</p>
          <p className="text-base font-semibold tabular-nums">{formatMoney(totals.expense)}</p>
        </div>
        <div className="text-center">
          <p className="text-[11px] text-neutral-400">Баланс</p>
          <p className="text-base font-semibold tabular-nums text-brand">
            {formatMoney(totals.income - totals.expense)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[11px] text-neutral-400">Доходы</p>
          <p className="text-base font-semibold tabular-nums">{formatMoney(totals.income)}</p>
        </div>
      </div>

      <PeriodNavigator
        period={period}
        anchor={periodAnchor}
        onPeriodChange={setPeriod}
        onAnchorChange={setPeriodAnchor}
        className="mb-1"
      />

      <div className="mb-4 -mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1 scrollbar-none">
        <FilterChip active={type === ""} onClick={() => setType("")}>
          Все
        </FilterChip>
        <FilterChip active={type === "expense"} onClick={() => setType("expense")}>
          Расходы
        </FilterChip>
        <FilterChip active={type === "income"} onClick={() => setType("income")}>
          Доходы
        </FilterChip>
        {accounts.length > 1 && (
          <>
            <span className="mx-0.5 w-px shrink-0 self-center bg-neutral-200" />
            <FilterChip active={accountId === ""} onClick={() => setAccountId("")}>
              Все счета
            </FilterChip>
            {accounts.map((a) => (
              <FilterChip key={a.id} active={accountId === a.id} onClick={() => setAccountId(a.id)}>
                {a.name}
              </FilterChip>
            ))}
          </>
        )}
      </div>

      {loading ? (
        <p className="py-16 text-center text-sm text-neutral-400">Загрузка...</p>
      ) : error ? (
        <p className="py-16 text-center text-sm text-red-600">{error}</p>
      ) : transactions.length === 0 ? (
        <p className="py-16 text-center text-sm text-neutral-400">Нет операций за период</p>
      ) : (
        <div className="space-y-4">
          {grouped.map((group) => (
            <section key={group.label}>
              <h2 className="mb-1 px-0.5 text-xs font-semibold text-neutral-400">{group.label}</h2>
              <div className="list-divider rounded-xl bg-neutral-50/50 px-2">
                {group.items.map((tx, i) => (
                  <TransactionRow
                    key={tx.id}
                    tx={tx}
                    colorIndex={i}
                    expanded={expanded.has(tx.id)}
                    onToggle={() => toggleExpand(tx.id)}
                    onDelete={() => remove(tx.id)}
                    onEditItem={(item, txType) =>
                      setEditItem({ txId: tx.id, item, txType })
                    }
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      <ItemCategorySheet
        open={!!editItem}
        transactionId={editItem?.txId ?? ""}
        item={editItem?.item ?? null}
        txType={editItem?.txType}
        onClose={() => setEditItem(null)}
        onSaved={() => void reload()}
      />
    </>
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
        "shrink-0 rounded-full px-3 py-1 text-xs font-medium transition",
        active ? "bg-brand text-white" : "bg-neutral-100 text-neutral-600"
      )}
    >
      {children}
    </button>
  );
}

function TransactionRow({
  tx,
  colorIndex,
  expanded,
  onToggle,
  onDelete,
  onEditItem,
}: {
  tx: TransactionListItem;
  colorIndex: number;
  expanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  onEditItem: (item: TransactionItem, txType: "expense" | "income") => void;
}) {
  const hasItems = (tx.items_count ?? 0) > 0;
  const txType = tx.type === "income" ? "income" : "expense";
  const editableItems = (tx.items ?? []).filter((i) => i.id);
  const canEditItems = editableItems.length > 0;
  const subtitle = [sourceLabel(tx.source), tx.account?.name, tx.category].filter(Boolean).join(" · ");

  return (
    <div className="hairline-b last:border-0">
      <button type="button" onClick={onToggle} className="flex w-full items-start gap-1 text-left active:bg-neutral-100/80">
        <div className="min-w-0 flex-1">
          <TxRow
            title={tx.title}
            subtitle={subtitle}
            amount={tx.amount}
            type={tx.type}
            occurredAt={tx.occurred_at}
            colorIndex={colorIndex}
          />
        </div>
        <span className="mt-2 shrink-0 p-1 text-neutral-300">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </span>
      </button>

      {expanded && canEditItems && (
        <p className="mb-1 ml-5 text-[10px] text-neutral-400">
          Нажмите на позицию, чтобы изменить категорию
        </p>
      )}

      {expanded && hasItems && tx.items && tx.items.length > 0 && (
        <ul className="mb-1 ml-5 space-y-0 border-l border-neutral-200 pl-3">
          {tx.items.map((item, i) => (
            <li key={item.id ?? i}>
              {item.id ? (
                <button
                  type="button"
                  onClick={() => onEditItem(item as TransactionItem, txType)}
                  className="flex w-full items-center justify-between gap-2 py-2 text-left text-xs active:bg-neutral-100"
                >
                  <span className="min-w-0 flex-1 truncate text-neutral-600">{item.raw_name}</span>
                  <span className="flex shrink-0 items-center gap-1">
                    {item.category?.name && (
                      <span className="max-w-[100px] truncate text-[10px] text-brand">{item.category.name}</span>
                    )}
                    <span className="font-medium tabular-nums">{formatMoney(item.amount)}</span>
                    <ChevronRight size={12} className="text-neutral-300" />
                  </span>
                </button>
              ) : (
                <div className="flex justify-between gap-2 py-2 text-xs">
                  <span className="truncate text-neutral-600">{item.raw_name}</span>
                  <span className="shrink-0 font-medium tabular-nums">{formatMoney(item.amount)}</span>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {expanded && (
        <div className="flex justify-end pb-1 pr-1">
          <Button variant="ghost" size="sm" className="h-7 text-red-500" onClick={onDelete}>
            Удалить
          </Button>
        </div>
      )}
    </div>
  );
}
