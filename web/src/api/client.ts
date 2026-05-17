const API_BASE = import.meta.env.VITE_API_URL ?? "";

const TOKEN_KEY = "fm_token";
const USER_KEY = "fm_user";

export type User = { id: string; email: string; login: string };

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): User | null {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

export function setAuth(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new ApiError(data.error ?? data.detail ?? "Ошибка запроса", res.status);
  }
  return data as T;
}

export const api = {
  register: (body: { email: string; login: string; password: string }) =>
    request<{ user: User; access_token: string }>("/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }, false),

  login: (body: { login: string; password: string }) =>
    request<{ user: User; access_token: string }>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }, false),

  accounts: () => request<{ accounts: Account[] }>("/v1/accounts"),
  createAccount: (body: { name: string; balance: number }) =>
    request<{ account: Account }>("/v1/accounts", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateAccount: (id: string, body: { name?: string; balance?: number }) =>
    request<{ account: Account }>(`/v1/accounts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteAccount: (id: string) =>
    request<{ success: boolean }>(`/v1/accounts/${id}`, { method: "DELETE" }),

  categories: (includeChildren = true) =>
    request<{ categories: Category[] }>(
      `/v1/categories?include=${includeChildren ? "children" : ""}`
    ),

  transactions: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ transactions: Transaction[] }>(`/v1/transactions${q}`);
  },
  transaction: (id: string) =>
    request<{ transaction: TransactionDetail }>(`/v1/transactions/${id}`),
  createTransaction: (body: CreateTransactionBody) =>
    request<{ transaction: { id: string; amount: number; source: string } }>(
      "/v1/transactions",
      { method: "POST", body: JSON.stringify(body) }
    ),
  deleteTransaction: (id: string) =>
    request<{ success: boolean }>(`/v1/transactions/${id}`, { method: "DELETE" }),

  scanQr: (body: { account_id: string; qr: string }) =>
    request<{ transaction: TransactionDetail }>("/v1/receipts/qr", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export type Account = { id: string; name: string; balance: number };

export type Category = {
  id: string;
  name: string;
  type: string;
  parent_id?: string | null;
  children?: Category[];
};

export type Transaction = {
  id: string;
  type: string;
  amount: number;
  currency: string;
  occurred_at: string;
  source: string;
  comment?: string | null;
  title?: string;
  account?: { id: string; name: string };
  merchant?: { id?: string; name: string };
  category?: string | null;
  items_count?: number;
  items?: TransactionItem[];
};

export type TransactionItem = {
  id?: string;
  raw_name: string;
  amount: number;
  category_id?: string | null;
  category?: { name: string };
};

export type TransactionDetail = Transaction & {
  merchant?: { id?: string; name: string };
  items?: TransactionItem[];
};

export type CreateTransactionBody = {
  account_id: string;
  type: "expense" | "income";
  amount: number;
  currency: "RUB";
  occurred_at: string;
  category_id?: string;
  comment?: string;
};

export function formatMoney(kopecks: number): string {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(kopecks / 100);
}

export function rublesToKopecks(rubles: number): number {
  return Math.round(rubles * 100);
}

export function flattenCategories(cats: Category[]): Category[] {
  const out: Category[] = [];
  const walk = (list: Category[]) => {
    for (const c of list) {
      out.push(c);
      if (c.children?.length) walk(c.children);
    }
  };
  walk(cats);
  return out;
}
