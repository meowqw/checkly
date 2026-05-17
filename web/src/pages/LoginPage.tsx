import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ReceiptText } from "lucide-react";
import { ApiError } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-100 p-4">
      <Card className="w-full max-w-md rounded-3xl">
        <CardContent className="p-8">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-neutral-900 text-white">
              <ReceiptText size={22} />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Checkly</h1>
              <p className="text-sm text-neutral-500">учёт расходов</p>
            </div>
          </div>

          <div className="mb-6 inline-flex rounded-2xl border border-neutral-200 bg-neutral-50 p-1">
            {(["login", "register"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={cn(
                  "rounded-xl px-4 py-2 text-sm transition",
                  tab === t ? "bg-white font-medium shadow-sm" : "text-neutral-500"
                )}
              >
                {t === "login" ? "Вход" : "Регистрация"}
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
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
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "..." : tab === "login" ? "Войти" : "Создать аккаунт"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm text-neutral-500">{label}</span>
      {children}
    </label>
  );
}
