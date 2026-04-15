import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "skeleton rounded-md bg-muted",
        className
      )}
    />
  );
}

/** Full workout session skeleton card — shown while AI generates a plan */
export function SessionSkeletonCard() {
  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-3 animate-fade-in">
      <div className="flex items-center gap-3">
        <Skeleton className="w-10 h-10 rounded-lg" />
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <div className="space-y-2">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
        <Skeleton className="h-3 w-4/6" />
      </div>
    </div>
  );
}

/** Generating plan skeleton with message */
export function PlanGeneratingSkeleton({ message = "Generating your plan…" }: { message?: string }) {
  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center gap-3 py-2">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse-rest" />
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
      {[...Array(3)].map((_, i) => (
        <SessionSkeletonCard key={i} />
      ))}
    </div>
  );
}

/** Hero stat card skeleton */
export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-2">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-7 w-16" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
}
