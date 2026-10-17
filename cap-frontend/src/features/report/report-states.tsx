import { FileSearch, ShieldAlert, WifiOff } from 'lucide-react'
import { EmptyState } from '../../shared/ui/empty-state'
import { SkeletonRows } from '../../shared/ui/skeleton-rows'

export function CaptchaBanner() {
  return (
    <div
      role="alert"
      className="mx-4 mb-3 flex items-start gap-2 rounded-xl bg-amber-50 p-3 text-xs text-amber-800 ring-1 ring-amber-200"
    >
      <ShieldAlert size={16} className="mt-0.5 shrink-0" />
      <span>
        <b>CAPTCHA required.</b> This worker is paused until you solve it in its live view.
      </span>
    </div>
  )
}

export function QueuedState() {
  return <SkeletonRows count={3} />
}

export function NoCasesState() {
  return (
    <EmptyState
      icon={<FileSearch size={20} />}
      title="No cases found"
      hint="The portal returned no cases that belong to these people."
    />
  )
}

export function PortalFailureState() {
  return (
    <EmptyState
      tone="red"
      icon={<WifiOff size={20} />}
      title="The portal is not responding"
      hint="Every search on this worker failed. Use “Retry failed” once the portal is back."
    />
  )
}
