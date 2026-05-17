/** Нормализация строки из QR (URL или query) в формат фискального чека. */
export function normalizeQrPayload(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";

  const tryQuery = (query: string) => {
    const q = query.startsWith("?") ? query.slice(1) : query;
    if (q.includes("t=") && (q.includes("fn=") || q.includes("s="))) return q;
    return null;
  };

  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    try {
      const url = new URL(trimmed);
      const fromSearch = tryQuery(url.search);
      if (fromSearch) return fromSearch;
    } catch {
      /* ignore */
    }
  }

  if (trimmed.includes("?")) {
    const fromQuery = tryQuery(trimmed.split("?").pop() ?? "");
    if (fromQuery) return fromQuery;
  }

  return trimmed;
}

export function isFiscalReceiptQr(value: string): boolean {
  const n = normalizeQrPayload(value);
  return n.includes("t=") && (n.includes("fn=") || n.includes("s="));
}
