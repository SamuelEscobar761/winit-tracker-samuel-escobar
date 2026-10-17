import { ExternalLink, Lock } from 'lucide-react'
import type { LaneStatus } from '../../shared/api/api-types'
import { shortJobId } from '../../shared/lib/format'
import { DotsMenu } from '../../shared/ui/dots-menu'
import { laneLabel } from '../report/lane-label'
import { LiveFrame } from './live-frame'
import { useAddressLabel } from './use-address-label'
import { useLaneSocket, type SocketState } from './use-lane-socket'

interface ScraperCardProps {
  lane: number | null
  slot: number
  isHovered: boolean
  onHover: (slot: number | null) => void
  onPopOut?: (lane: number) => void
}

function describeStatus(status: LaneStatus | null, state: SocketState, lane: number | null): string {
  if (lane === null) return 'Waiting for a free worker (other jobs are using them)'
  if (state !== 'open') return state === 'connecting' ? 'Connecting…' : 'Reconnecting to the live view…'
  if (status?.awaiting_captcha) return 'Your turn: solve the CAPTCHA in the page above'
  if (status?.job_id) return `Live · job ${shortJobId(status.job_id)} · person ${(status.person_index ?? 0) + 1}`
  return 'Idle · no person assigned'
}

function StatusBar({ text, isWaiting, isLive }: { text: string; isWaiting: boolean; isLive: boolean }) {
  return (
    <div
      role="status"
      className={`flex items-center gap-2 px-3 py-1.5 text-[11px] ${isWaiting ? 'bg-amber-400 text-amber-950' : 'bg-slate-800 text-slate-300'}`}
    >
      <span className={`size-1.5 rounded-full ${isWaiting ? 'bg-amber-900' : isLive ? 'animate-pulse bg-emerald-400' : 'bg-slate-500'}`} />
      {text}
    </div>
  )
}

export function ScraperCard({ lane, slot, isHovered, onHover, onPopOut }: ScraperCardProps) {
  const socket = useLaneSocket(lane)
  const address = useAddressLabel()
  const awaitingCaptcha = socket.status?.awaiting_captcha ?? false
  const isLive = socket.state === 'open' && socket.status?.job_id != null

  return (
    <article
      onMouseEnter={() => onHover(slot)}
      onMouseLeave={() => onHover(null)}
      aria-label={`Live view ${laneLabel(slot)}`}
      className={`relative flex h-full flex-col overflow-hidden rounded-2xl bg-slate-900 shadow-card ring-1 transition ${isHovered ? 'ring-indigo-400' : 'ring-slate-900/10'}`}
    >
      <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 pl-16">
        <Lock size={11} className="text-slate-400" />
        <span className="flex-1 truncate rounded bg-slate-700 px-2 py-0.5 font-mono text-[10px] text-slate-300">
          {address}
        </span>
        <span className="w-7" />
      </div>
      <span className="absolute left-2 top-1.5 z-10 rounded-md bg-black/35 px-1.5 py-0.5 font-mono text-xs font-medium text-white backdrop-blur-sm">
        {laneLabel(slot)}
      </span>
      <div className="absolute right-1.5 top-1 z-10">
        {onPopOut && lane !== null && (
          <DotsMenu
            dark
            items={[{ label: 'Open in separate tab', icon: <ExternalLink size={14} />, onClick: () => onPopOut(lane) }]}
          />
        )}
      </div>
      <div className="relative min-h-0 flex-1 overflow-hidden">
        <LiveFrame
          imageRef={socket.imageRef}
          frameSize={socket.frameSize}
          hasFrame={socket.hasFrame}
          isInteractive={awaitingCaptcha}
          onInput={socket.sendInput}
          placeholder={lane === null ? 'Waiting for a free worker…' : 'Waiting for the first frame…'}
        />
      </div>
      <StatusBar text={describeStatus(socket.status, socket.state, lane)} isWaiting={awaitingCaptcha} isLive={isLive} />
    </article>
  )
}
