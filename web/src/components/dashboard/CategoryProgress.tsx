type Props = { name: string; amount: string; percent: number };

export function CategoryProgress({ name, amount, percent }: Props) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <div>
          <div className="text-sm font-medium">{name}</div>
          <div className="mt-1 text-xs text-neutral-500">{percent}% от расходов</div>
        </div>
        <div className="text-sm font-semibold">{amount}</div>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-neutral-100">
        <div className="h-full rounded-full bg-neutral-900 transition-all" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
