interface SkeletonRowsProps {
  count?: number
}

export function SkeletonRows({ count = 3 }: SkeletonRowsProps) {
  return (
    <div className="space-y-2 px-4 pb-5" aria-hidden="true">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="h-8 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  )
}
