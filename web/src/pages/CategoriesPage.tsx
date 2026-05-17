import { useEffect, useMemo, useState } from "react";
import { api, type Category } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [filter, setFilter] = useState<"expense" | "income">("expense");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .categories()
      .then((r) => setCategories(r.categories))
      .finally(() => setLoading(false));
  }, []);

  const roots = useMemo(
    () => categories.filter((c) => c.type === filter),
    [categories, filter]
  );

  return (
    <>
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Категории</h1>
        <p className="mt-1 text-neutral-500">Категории и подкатегории отдельно</p>
      </header>

      <div className="mb-4 inline-flex rounded-2xl border border-neutral-200 bg-white p-1">
        <FilterBtn active={filter === "expense"} onClick={() => setFilter("expense")}>
          Расходы
        </FilterBtn>
        <FilterBtn active={filter === "income"} onClick={() => setFilter("income")}>
          Доходы
        </FilterBtn>
      </div>

      {loading ? (
        <p className="text-neutral-500">Загрузка...</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {roots.map((cat) => (
            <Card key={cat.id} className="rounded-3xl">
              <CardContent>
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{cat.name}</span>
                  <Badge>категория</Badge>
                </div>
                {cat.children && cat.children.length > 0 ? (
                  <ul className="mt-4 space-y-2 border-t border-neutral-100 pt-4">
                    {cat.children.map((ch) => (
                      <li
                        key={ch.id}
                        className="flex items-center justify-between rounded-xl bg-neutral-50 px-3 py-2 text-sm"
                      >
                        <span className="text-neutral-700">{ch.name}</span>
                        <span className="text-xs text-neutral-400">подкатегория</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-xs text-neutral-400">Нет подкатегорий</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}

function FilterBtn({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-xl px-4 py-2 text-sm transition ${
        active ? "bg-neutral-900 text-white" : "text-neutral-500 hover:text-neutral-900"
      }`}
    >
      {children}
    </button>
  );
}
