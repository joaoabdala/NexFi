import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

/** Placeholder exibido enquanto o chunk de uma página (lazy) é baixado. */
export function PageFallback({ fullScreen = false }: { fullScreen?: boolean }) {
  return (
    <div
      role="status"
      aria-label="Carregando"
      className={cn("space-y-4", fullScreen && "flex h-screen w-screen flex-col bg-background p-6")}
    >
      <Skeleton className="h-8 w-48" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <Skeleton className="h-64 w-full" />
    </div>
  )
}
