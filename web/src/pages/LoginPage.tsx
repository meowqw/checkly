import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ReceiptText } from "lucide-react";
import { ApiError, api } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login: doLogin, register } = useAuth();
  const navigate = useNavigate();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (tab === "login") await doLogin(login, password);
      else await register(email, login, password);

      const { accounts } = await api.accounts();
      if (accounts.length === 0) {
        navigate("/accounts", { state: { needsAccount: true }, replace: true });
      } else {
        navigate("/");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col overflow-x-hidden bg-white px-4 pb-safe-b pt-12">
      <div className="mx-auto w-full max-w-sm flex-1 animate-page-in">
        <div className="mb-10 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand text-white">
            <ReceiptText size={20} />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Checkly</h1>
            <p className="text-xs text-neutral-400">учёт расходов</p>
          </div>
        </div>

        <div className="mb-6 flex border-b border-neutral-100">
          {(["login", "register"] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={cn(
                "relative flex-1 py-2.5 text-sm font-medium transition",
                tab === t ? "text-brand" : "text-neutral-400"
              )}
            >
              {t === "login" ? "Вход" : "Регистрация"}
              {tab === t && (
                <span className="absolute inset-x-4 -bottom-px h-0.5 rounded-full bg-brand" />
              )}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={submit} className="space-y-4">
          {tab === "register" && (
            <Field label="Email">
              <input
                className="input-field"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </Field>
          )}
          <Field label="Логин">
            <input
              className="input-field"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              required
              minLength={2}
            />
          </Field>
          <Field label="Пароль">
            <input
              className="input-field"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </Field>
          <Button type="submit" variant="brand" className="w-full" size="lg" disabled={loading}>
            {loading ? "..." : tab === "login" ? "Войти" : "Создать аккаунт"}
          </Button>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-neutral-500">{label}</span>
      {children}
    </label>
  );
}
