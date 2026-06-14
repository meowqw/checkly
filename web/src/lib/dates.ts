export type Period = "day" | "week" | "month";

export type PeriodRange = { from: Date; to: Date; label: string; anchor: Date };

/** Понедельник той же календарной недели. */
function startOfWeekMonday(d: Date): Date {
  const date = new Date(d);
  date.setHours(0, 0, 0, 0);
  const weekday = date.getDay();
  const daysFromMonday = weekday === 0 ? 6 : weekday - 1;
  date.setDate(date.getDate() - daysFromMonday);
  return date;
}

function endOfWeekSunday(d: Date): Date {
  const end = startOfWeekMonday(d);
  end.setDate(end.getDate() + 6);
  end.setHours(23, 59, 59, 999);
  return end;
}

function formatDayLabel(d: Date): string {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const day = new Date(d);
  day.setHours(0, 0, 0, 0);
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const formatted = d.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  if (day.getTime() === today.getTime()) return `Сегодня · ${formatted}`;
  if (day.getTime() === yesterday.getTime()) return `Вчера · ${formatted}`;
  return formatted;
}

function formatWeekLabel(from: Date, to: Date): string {
  const f = from.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
  const t = to.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
  return `${f} – ${t}`;
}

function formatMonthLabel(from: Date, to: Date): string {
  if (from.getMonth() === to.getMonth() && from.getFullYear() === to.getFullYear()) {
    return from.toLocaleDateString("ru-RU", { month: "long", year: "numeric" });
  }
  const f = from.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
  const t = to.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
  return `${f} – ${t}`;
}

/** Календарный период относительно anchor (по умолчанию — сегодня). */
export function getPeriodRange(period: Period, anchor: Date = new Date()): PeriodRange {
  const ref = new Date(anchor);
  ref.setHours(12, 0, 0, 0);

  if (period === "day") {
    const from = new Date(ref);
    from.setHours(0, 0, 0, 0);
    const to = new Date(ref);
    to.setHours(23, 59, 59, 999);
    return { from, to, label: formatDayLabel(from), anchor: from };
  }

  if (period === "week") {
    const from = startOfWeekMonday(ref);
    const to = endOfWeekSunday(ref);
    return { from, to, label: formatWeekLabel(from, to), anchor: from };
  }

  const from = new Date(ref.getFullYear(), ref.getMonth(), 1, 0, 0, 0, 0);
  const to = new Date(ref.getFullYear(), ref.getMonth() + 1, 0, 23, 59, 59, 999);
  const monthAnchor = new Date(ref.getFullYear(), ref.getMonth(), 1, 0, 0, 0, 0);
  return { from, to, label: formatMonthLabel(from, to), anchor: monthAnchor };
}

/** Сдвиг anchor на предыдущий/следующий период. */
export function shiftPeriodAnchor(period: Period, anchor: Date, delta: -1 | 1): Date {
  const next = new Date(anchor);
  if (period === "day") {
    next.setDate(next.getDate() + delta);
  } else if (period === "week") {
    next.setDate(next.getDate() + delta * 7);
  } else {
    next.setMonth(next.getMonth() + delta);
  }
  return next;
}

/** Можно ли листать вперёд (ещё не текущий период). */
export function canGoPeriodNext(period: Period, anchor: Date): boolean {
  const { anchor: currentAnchor } = getPeriodRange(period, new Date());
  const { anchor: viewAnchor } = getPeriodRange(period, anchor);
  return viewAnchor.getTime() < currentAnchor.getTime();
}

/** Локальная дата YYYY-MM-DD. */
export function toApiDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Границы периода — локальные календарные даты (бэкенд учитывает X-Timezone). */
export function toApiDateTimeRange(from: Date, to: Date): { from: string; to: string } {
  return { from: toApiDate(from), to: toApiDate(to) };
}

/** Парсинг границы периода из кэша (YYYY-MM-DD или ISO). */
export function parseRangeBound(value: string, kind: "start" | "end"): number {
  if (value.includes("T")) {
    return parseApiDateTime(value).getTime();
  }
  const [y, m, d] = value.split("-").map(Number);
  if (kind === "start") {
    return new Date(y, m - 1, d, 0, 0, 0, 0).getTime();
  }
  return new Date(y, m - 1, d, 23, 59, 59, 999).getTime();
}

/** Значение для input[type=datetime-local] в локальном времени. */
export function toDateTimeLocalValue(d = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** datetime-local → naive local ISO для API (без UTC-сдвига). */
export function toApiDateTimeLocal(value: string): string {
  return value.length === 16 ? `${value}:00` : value;
}

/** @deprecated используйте toApiDateTimeLocal */
export function fromDateTimeLocalValue(value: string): string {
  return toApiDateTimeLocal(value);
}

/**
 * Парсинг даты с API.
 * Naive ISO — локальное wall-clock время пользователя.
 * С Z/offset — абсолютный момент времени.
 */
export function parseApiDateTime(iso: string): Date {
  const hasTimezone = iso.endsWith("Z") || /[+-]\d{2}:?\d{2}$/.test(iso);
  if (hasTimezone) {
    return new Date(iso);
  }
  const [datePart, timePart = "00:00:00"] = iso.split("T");
  const [y, m, d] = datePart.split("-").map(Number);
  const [hh, mm, ssRaw] = timePart.split(":");
  const ss = parseInt((ssRaw ?? "0").split(".")[0], 10);
  return new Date(y, m - 1, d, parseInt(hh, 10), parseInt(mm, 10), ss);
}

export function formatTxDate(iso: string): string {
  const d = parseApiDateTime(iso);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const txDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());

  const time = d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  if (txDay.getTime() === today.getTime()) return `Сегодня, ${time}`;
  if (txDay.getTime() === yesterday.getTime()) return `Вчера, ${time}`;
  return d.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getUserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Moscow";
  } catch {
    return "Europe/Moscow";
  }
}
