import { parseApiDateTime } from "@/lib/dates";
import type { Transaction } from "@/api/client";

export const SOURCE_LABELS: Record<string, string> = {
  manual: "Вручную",
  qr_receipt: "QR-чек",
  ocr: "OCR",
  import: "Импорт",
};

export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

export type TransactionListItem = Transaction & {
  title: string;
  account?: { id: string; name: string };
  merchant?: { id?: string; name: string };
  category?: string | null;
  items_count?: number;
  items?: Array<{
    id?: string;
    raw_name: string;
    amount: number;
    category?: { name: string };
  }>;
};

export function groupByDate(transactions: TransactionListItem[]): { label: string; items: TransactionListItem[] }[] {
  const groups = new Map<string, TransactionListItem[]>();
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  for (const tx of transactions) {
    const d = parseApiDateTime(tx.occurred_at);
    const txDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    let label: string;
    if (txDay.getTime() === today.getTime()) label = "Сегодня";
    else if (txDay.getTime() === yesterday.getTime()) label = "Вчера";
    else label = d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });

    if (!groups.has(label)) groups.set(label, []);
    groups.get(label)!.push(tx);
  }

  return [...groups.entries()].map(([label, items]) => ({ label, items }));
}

export function formatFullDate(iso: string): string {
  return parseApiDateTime(iso).toLocaleString("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
