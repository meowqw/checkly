/** Тонкий индикатор фонового обновления (не блокирует контент). */
export function RefreshBar({ active }: { active: boolean }) {
  if (!active) return null;
  return (
    <div
      className="mb-3 h-0.5 overflow-hidden rounded-full bg-neutral-100"
      role="status"
      aria-label="Обновление"
    >
      <div className="h-full w-1/3 animate-shimmer rounded-full bg-brand" />
    </div>
  );
}
