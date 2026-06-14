import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import * as data from "@/api/data-service";
import { ApiError, type Account } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { subscribeAccountsChanged } from "@/lib/data-events";

type AccountsContextValue = {
  accounts: Account[];
  loading: boolean;
  error: string;
  fromCache: boolean;
  refresh: () => Promise<void>;
  primaryAccount: Account | null;
};

const AccountsContext = createContext<AccountsContextValue | null>(null);

export function AccountsProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fromCache, setFromCache] = useState(false);
  const inflight = useRef<Promise<void> | null>(null);
  const hasLoaded = useRef(false);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) return;

    if (inflight.current) {
      await inflight.current;
      return;
    }

    const task = (async () => {
      const showSpinner = !hasLoaded.current;
      if (showSpinner) setLoading(true);
      setError("");
      try {
        const res = await data.getAccounts();
        setAccounts(res.accounts);
        setFromCache(res.fromCache);
        hasLoaded.current = true;
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить счета");
      } finally {
        if (showSpinner) setLoading(false);
      }
    })();

    inflight.current = task.finally(() => {
      inflight.current = null;
    });
    await inflight.current;
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) {
      hasLoaded.current = false;
      setAccounts([]);
      setError("");
      setFromCache(false);
      return;
    }
    void refresh();
  }, [isAuthenticated, refresh]);

  useEffect(() => {
    if (!isAuthenticated) return;
    return subscribeAccountsChanged(() => {
      void refresh();
    });
  }, [isAuthenticated, refresh]);

  const value = useMemo(
    () => ({
      accounts,
      loading,
      error,
      fromCache,
      refresh,
      primaryAccount: accounts[0] ?? null,
    }),
    [accounts, loading, error, fromCache, refresh]
  );

  return <AccountsContext.Provider value={value}>{children}</AccountsContext.Provider>;
}

export function useAccounts() {
  const ctx = useContext(AccountsContext);
  if (!ctx) throw new Error("useAccounts outside AccountsProvider");
  return ctx;
}
