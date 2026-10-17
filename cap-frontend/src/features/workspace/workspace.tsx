import { useState } from 'react'
import type { JobEvent, JobSnapshot, PersonView } from '../../shared/api/api-types'
import { liveHash } from '../../shared/routing/hash-route'
import type { CaseRow } from '../report/case-row'
import { ReportCard } from '../report/report-card'
import { ScraperCard } from '../scraper/scraper-card'
import { splitSlots, type Layout } from './layout'
import { PaneList } from './pane-list'

interface Slot {
  slot: number
  lane: number | null
}

interface WorkspaceProps {
  job: JobSnapshot
  events: JobEvent[]
  results: Record<number, PersonView>
  lanes: (number | null)[]
  layout: Layout
  onOpenCase: (row: CaseRow) => void
}

const SECTION_NAMES = ['', ' · top', ' · bottom']

function popOut(lane: number) {
  window.open(`${window.location.pathname}${liveHash(lane)}`, '_blank')
}

export function Workspace({ job, events, results, lanes, layout, onOpenCase }: WorkspaceProps) {
  const [hovered, setHovered] = useState<number | null>(null)
  const slots: Slot[] = lanes.map((lane, slot) => ({ slot, lane }))
  const groups = splitSlots(slots, layout)
  const nameOf = (index: number) => SECTION_NAMES[layout === 2 ? 0 : index + 1]

  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-3 lg:grid-cols-2">
      <div className="flex min-h-0 flex-col gap-3">
        {groups.map((group, index) => (
          <PaneList key={index} title={`Reports${nameOf(index)}`} items={group} keyOf={(item) => item.slot}>
            {({ lane, slot }) => (
              <ReportCard
                lane={lane}
                slot={slot}
                job={job}
                events={events}
                results={results}
                isHovered={hovered === slot}
                onHover={setHovered}
                onOpenCase={onOpenCase}
              />
            )}
          </PaneList>
        ))}
      </div>
      <div className="flex min-h-0 flex-col gap-3">
        {groups.map((group, index) => (
          <PaneList key={index} fit title={`Live scraping${nameOf(index)}`} items={group} keyOf={(item) => item.slot}>
            {({ lane, slot }) => (
              <ScraperCard lane={lane} slot={slot} isHovered={hovered === slot} onHover={setHovered} onPopOut={popOut} />
            )}
          </PaneList>
        ))}
      </div>
    </div>
  )
}
