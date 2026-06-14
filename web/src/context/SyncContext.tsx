import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { isOnline, subscribeOnline } from "@/lib/connectivity";
import { queueLength, setQueueChangeListener } from "@/lib/offline/queue";
import { prefetchCoreData, processSyncQueue } from "@/api/data-service";
import { useAuth } from "@/context/AuthContext";

type SyncContextValue = {
  online: boolean;
  pendingCount: number;
  syncing: boolean;
  lastSyncAt: number | null;
  refreshPending: () => Promise<void>;
  syncNow: () => Promise<void>;
};

const SyncContext = createContext<SyncContextValue | null>(null);

export function SyncProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [online, setOnline] = useState(isOnline());
  const [pendingCount, setPendingCount] = useState(0);
  const [syncing, setSyncing] = useState(false);
  const [lastSyncAt, setLastSyncAt] = useState<number | null>(null);

  const refreshPending = useCallback(async () => {
    setPendingCount(await queueLength());
  }, []);

  const syncNow = useCallback(async () => {
    if (!isOnline()) return;
    setSyncing(true);
    try {
      await processSyncQueue();
      await prefetchCoreData();
      setLastSyncAt(Date.now());
    } finally {
      await refreshPending();
      setSyncing(false);
    }
  }, [refreshPending]);

  useEffect(() => {
    setQueueChangeListener(() => {
      void refreshPending();
    });
    return () => setQueueChangeListener(null);
  }, [refreshPending]);

  useEffect(() => {
    if (!isAuthenticated) return;
    void refreshPending();
    if (isOnline()) {
      void prefetchCoreData().then(() => setLastSyncAt(Date.now()));
    }
    return subscribeOnline((next) => {
      setOnline(next);
      if (next) void syncNow();
    });
  }, [isAuthenticated, refreshPending, syncNow]);

  const value = useMemo(
    () => ({ online, pendingCount, syncing, lastSyncAt, refreshPending, syncNow }),
    [online, pendingCount, syncing, lastSyncAt, refreshPending, syncNow]
  );

  return <SyncContext.Provider value={value}>{children}</SyncContext.Provider>;
}

export function useSync() {
  const ctx = useContext(SyncContext);
  if (!ctx) throw new Error("useSync outside SyncProvider");
  return ctx;
}
