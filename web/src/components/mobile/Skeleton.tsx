import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-lg bg-neutral-100", className)} />;
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-5" aria-hidden>
      <div>
        <Skeleton className="mb-2 h-3 w-24" />
        <Skeleton className="h-9 w-40" />
        <div className="mt-3 flex gap-4">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-28" />
        </div>
      </div>
      <Skeleton className="h-9 w-full" />
      <div className="space-y-3">
        <Skeleton className="h-3 w-20" />
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-2.5 w-full flex-1" />
            <Skeleton className="h-3 w-12" />
          </div>
        ))}
      </div>
      <div className="space-y-2">
        <Skeleton className="h-3 w-28" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-start gap-3 py-2">
            <Skeleton className="h-2.5 w-2.5 shrink-0 rounded-full" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-4 w-3/5" />
              <Skeleton className="h-3 w-2/5" />
            </div>
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function TxRowsOnlySkeleton() {
  return (
    <div className="space-y-4" aria-hidden>
      {[1, 2].map((g) => (
        <div key={g}>
          <Skeleton className="mb-2 h-3 w-16" />
          <div className="space-y-1 rounded-xl bg-neutral-50/50 p-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-start gap-3 py-2">
                <Skeleton className="h-2.5 w-2.5 shrink-0 rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-4/5" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
                <Skeleton className="h-4 w-14" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function TxListSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-4" aria-hidden>
      <div className="grid grid-cols-3 gap-2 rounded-xl bg-neutral-50 p-3">
        <Skeleton className="h-10" />
        <Skeleton className="h-10" />
        <Skeleton className="h-10" />
      </div>
      <Skeleton className="h-9 w-full" />
      <div className="flex gap-2">
        <Skeleton className="h-7 w-14 rounded-full" />
        <Skeleton className="h-7 w-20 rounded-full" />
        <Skeleton className="h-7 w-16 rounded-full" />
      </div>
      {[1, 2].map((g) => (
        <div key={g}>
          <Skeleton className="mb-2 h-3 w-16" />
          <div className="space-y-1 rounded-xl bg-neutral-50/50 p-2">
            {Array.from({ length: Math.ceil(rows / 2) }, (_, i) => (
              <div key={i} className="flex items-start gap-3 py-2">
                <Skeleton className="h-2.5 w-2.5 shrink-0 rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-4/5" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
                <Skeleton className="h-4 w-14" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function CategoryListSkeleton() {
  return (
    <div className="space-y-3" aria-hidden>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="rounded-xl border border-neutral-100 p-3">
          <div className="flex items-center gap-3">
            <Skeleton className="h-10 w-10 shrink-0 rounded-xl" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function FormSkeleton() {
  return (
    <div className="space-y-4" aria-hidden>
      <Skeleton className="h-12 w-48" />
      <Skeleton className="h-10 w-full" />
      <div className="grid grid-cols-3 gap-2">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-11 w-full rounded-xl" />
    </div>
  );
}
