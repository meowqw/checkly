export type Period = "day" | "week" | "month";

/** Локальная дата YYYY-MM-DD (без сдвига UTC). */
export function toApiDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Границы периода в ISO UTC для фильтра API (учитывает локальный часовой пояс). */
export function toApiDateTimeRange(from: Date, to: Date): { from: string; to: string } {
  return { from: from.toISOString(), to: to.toISOString() };
}

/** Значение для input[type=datetime-local] в локальном времени. */
export function toDateTimeLocalValue(d = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** datetime-local → ISO UTC для API. */
export function fromDateTimeLocalValue(value: string): string {
  return new Date(value).toISOString();
}

/** Парсинг даты с API (naive datetime считаем UTC). */
export function parseApiDateTime(iso: string): Date {
  const hasTimezone = iso.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(iso);
  if (iso.includes("T") && !hasTimezone) {
    return new Date(`${iso}Z`);
  }
  return new Date(iso);
}

export function getPeriodRange(period: Period): { from: Date; to: Date; label: string } {
  const to = new Date();
  const from = new Date();

  if (period === "day") {
    from.setHours(0, 0, 0, 0);
    to.setHours(23, 59, 59, 999);
    return {
      from,
      to,
      label: to.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" }),
    };
  }

  if (period === "week") {
    from.setDate(from.getDate() - 6);
    from.setHours(0, 0, 0, 0);
    to.setHours(23, 59, 59, 999);
    const f = from.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
    const t = to.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
    return { from, to, label: `${f} – ${t}` };
  }

  from.setDate(1);
  from.setHours(0, 0, 0, 0);
  to.setHours(23, 59, 59, 999);
  const f = from.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
  const t = to.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
  return { from, to, label: `${f} – ${t}` };
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
