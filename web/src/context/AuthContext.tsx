import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  api,
  clearAuth,
  getUser,
  setAuth,
  setUnauthorizedHandler,
  type User,
} from "../api/client";
import { clearOfflineData } from "@/lib/offline/db";

type AuthContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  login: (login: string, password: string) => Promise<void>;
  register: (email: string, login: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getUser());

  useEffect(() => {
    setUnauthorizedHandler(() => {
      void clearOfflineData();
      clearAuth();
      setUser(null);
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  const login = useCallback(async (loginName: string, password: string) => {
    await clearOfflineData();
    const res = await api.login({ login: loginName, password });
    setAuth(res.access_token, res.user);
    setUser(res.user);
  }, []);

  const register = useCallback(
    async (email: string, loginName: string, password: string) => {
      await clearOfflineData();
      const res = await api.register({ email, login: loginName, password });
      setAuth(res.access_token, res.user);
      setUser(res.user);
    },
    []
  );

  const logout = useCallback(() => {
    void clearOfflineData();
    clearAuth();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      login,
      register,
      logout,
    }),
    [user, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}
