import { Link } from "react-router-dom";
import { Wallet } from "lucide-react";
import { Button } from "@/components/ui/button";

type Props = {
  variant?: "banner" | "card";
  showAction?: boolean;
};

export function NoAccountsNotice({ variant = "card", showAction = true }: Props) {
  if (variant === "banner") {
    return (
      <div className="animate-fade-in border-b border-amber-200 bg-amber-50 px-4 py-2.5 text-center text-xs text-amber-900">
        <Wallet size={14} className="mr-1 inline" />
        Без счёта недоступны операции и чеки.{" "}
        <Link to="/accounts" className="font-semibold text-amber-950 underline underline-offset-2">
          Создать счёт
        </Link>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-4">
      <div className="flex items-start gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
          <Wallet size={18} />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-amber-950">Сначала создайте счёт</p>
          <p className="mt-1 text-xs leading-relaxed text-amber-900/90">
            Без счёта нельзя добавлять траты, сканировать чеки и видеть баланс. Создайте хотя бы один
            счёт — например «Наличные» или «Карта».
          </p>
          {showAction && (
            <Link to="/accounts" className="mt-3 inline-block">
              <Button variant="brand" size="sm">
                Перейти к счетам
              </Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
