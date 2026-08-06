export default function Skeleton({ className = "" }) {
  return <div className={`animate-pulse rounded-xl bg-ink-100 ${className}`} />;
}

export function DestinationCardSkeleton() {
  return (
    <div className="card overflow-hidden">
      <Skeleton className="h-48 w-full rounded-none" />
      <div className="space-y-3 p-4">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-4 w-full" />
      </div>
    </div>
  );
}
