import { Loader2, WifiOff } from 'lucide-react'
import type { StreamState } from './use-event-stream'
import type { PortalStatus } from './job-events'

interface PortalBannerProps {
  portal: PortalStatus
  stream: StreamState
}

export function PortalBanner({ portal, stream }: PortalBannerProps) {
  if (portal === 'down') {
    return (
      <div role="alert" className="flex items-center gap-2 bg-rose-600 px-4 py-2 text-xs font-medium text-white">
        <WifiOff size={14} /> The portal is down or in maintenance. Searches are paused and resume by themselves.
      </div>
    )
  }
  if (stream === 'reconnecting') {
    return (
      <div role="status" className="flex items-center gap-2 bg-amber-100 px-4 py-1.5 text-xs text-amber-900">
        <Loader2 size={12} className="animate-spin" /> Connection lost. Reconnecting and catching up…
      </div>
    )
  }
  return null
}
