interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-md bg-slate-800 ${className}`}
    />
  );
}

interface CardSkeletonProps {
  count?: number;
}

export function CardSkeleton({ count = 4 }: CardSkeletonProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <Skeleton className="mb-2 h-6 w-6" />
          <Skeleton className="mb-1 h-8 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      ))}
    </div>
  );
}

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableSkeleton({ rows = 5, columns = 6 }: TableSkeletonProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-800">
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i} className="px-4 py-3">
                <Skeleton className="h-4 w-20" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex} className="border-b border-slate-800/50">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <td key={colIndex} className="px-4 py-3">
                  <Skeleton className="h-4 w-full" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface StatCardSkeletonProps {
  count?: number;
}

export function StatCardSkeleton({ count = 4 }: StatCardSkeletonProps) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <Skeleton className="mb-2 h-6 w-6" />
          <Skeleton className="mb-1 h-8 w-16" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

interface ListSkeletonProps {
  count?: number;
}

export function ListSkeleton({ count = 5 }: ListSkeletonProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3">
          <div className="flex-1">
            <Skeleton className="mb-1 h-4 w-1/3" />
            <Skeleton className="h-3 w-1/4" />
          </div>
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
      ))}
    </div>
  );
}

interface ChartSkeletonProps {
  height?: string;
}

export function ChartSkeleton({ height = "h-40" }: ChartSkeletonProps) {
  return (
    <div className={`flex items-end gap-2 ${height}`}>
      {Array.from({ length: 7 }).map((_, i) => (
        <div key={i} className="flex flex-1 flex-col items-center gap-1">
          <Skeleton className="w-full rounded-t" style={{ height: `${Math.random() * 80 + 20}%` }} />
          <Skeleton className="h-3 w-8" />
        </div>
      ))}
    </div>
  );
}

interface BarChartSkeletonProps {
  bars?: number;
}

export function BarChartSkeleton({ bars = 4 }: BarChartSkeletonProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: bars }).map((_, i) => (
        <div key={i}>
          <div className="mb-1 flex justify-between">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-12" />
          </div>
          <Skeleton className="h-2.5 w-full rounded-full" />
        </div>
      ))}
    </div>
  );
}

interface MapSkeletonProps {
  height?: string;
}

export function MapSkeleton({ height = "h-full" }: MapSkeletonProps) {
  return (
    <div className={`flex items-center justify-center ${height} bg-slate-900`}>
      <div className="flex flex-col items-center gap-3">
        <Skeleton className="h-12 w-12 rounded-full" />
        <Skeleton className="h-4 w-32" />
      </div>
    </div>
  );
}
