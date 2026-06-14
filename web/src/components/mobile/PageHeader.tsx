type Props = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
};

export function PageHeader({ title, subtitle, action }: Props) {
  return (
    <header className="mb-4 flex items-start justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-lg font-semibold tracking-tight md:text-2xl">{title}</h1>
        {subtitle && <p className="mt-0.5 text-xs text-neutral-500 md:text-sm">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}
