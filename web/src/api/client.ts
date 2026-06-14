import { getUserTimezone } from "@/lib/dates";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

const TOKEN_KEY = "fm_token";
const USER_KEY = "fm_user";

export type User = { id: string; email: string; login: string; timezone: string };

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): User | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    clearAuth();
    return null;
  }
}

export function setAuth(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

type UnauthorizedHandler = () => void;
let onUnauthorized: UnauthorizedHandler | null = null;

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null) {
  onUnauthorized = handler;
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
    "X-Timezone": getUserTimezone(),
    ...(options.headers as Record<string, string>),
  };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  if (!API_BASE && import.meta.env.PROD) {
    throw new ApiError(
      "API не настроен. Пересоберите APK с VITE_API_URL в .env.production.local",
      0
    );
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(
      `Нет связи с сервером${API_BASE ? ` (${API_BASE})` : ""}. Проверьте интернет и что API запущен.`,
      0
    );
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    if (res.status === 401 && auth) {
      clearAuth();
      onUnauthorized?.();
    }
    const detail = data.detail;
    const message =
      data.error ??
      (typeof detail === "string" ? detail : Array.isArray(detail) ? detail[0]?.msg : null) ??
      "Ошибка запроса";
    throw new ApiError(String(message), res.status);
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

  createCategory: (body: CreateCategoryBody) =>
    request<{ category: Category }>("/v1/categories", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateCategory: (id: string, body: UpdateCategoryBody) =>
    request<{ category: Category }>(`/v1/categories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  deleteCategory: (id: string) =>
    request<{ success: boolean }>(`/v1/categories/${id}`, { method: "DELETE" }),

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

  updateTransactionItem: (
    transactionId: string,
    itemId: string,
    body: { category_id: string }
  ) =>
    request<{ transaction: TransactionDetail }>(
      `/v1/transactions/${transactionId}/items/${itemId}`,
      { method: "PATCH", body: JSON.stringify(body) }
    ),

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
  icon?: string | null;
  color?: string | null;
  is_custom?: boolean;
  children?: Category[];
};

export type CreateCategoryBody = {
  name: string;
  type: "expense" | "income";
  parent_id?: string;
  icon?: string;
  color?: string;
};

export type UpdateCategoryBody = {
  name?: string;
  icon?: string;
  color?: string;
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
