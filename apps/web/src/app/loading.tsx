import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <main className="mx-auto max-w-[1280px] px-page py-10" aria-busy="true">
      <p role="status" className="mb-6 text-meta text-muted-foreground">
        正在加载文章…
      </p>
      <Skeleton className="mb-5 h-10 w-1/2" />
      <Skeleton className="mb-10 h-6 w-3/4" />
      <div className="grid grid-cols-1 gap-grid md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-64 rounded-card" />
        ))}
      </div>
    </main>
  );
}
