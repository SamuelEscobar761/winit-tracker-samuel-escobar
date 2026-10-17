import { FileSearch } from 'lucide-react'
import type { JobSnapshot, PersonView } from '../../shared/api/api-types'
import { pluralize } from '../../shared/lib/format'
import { EmptyState } from '../../shared/ui/empty-state'
import { SkeletonRows } from '../../shared/ui/skeleton-rows'
import { buildCaseRows, type CaseRow } from '../report/case-row'
import { CasesTable } from '../report/cases-table'

interface AllResultsProps {
  job: JobSnapshot
  results: Record<number, PersonView>
  onOpenCase: (row: CaseRow) => void
}

export function AllResults({ job, results, onOpenCase }: AllResultsProps) {
  const rows = buildCaseRows(Object.values(results))
  const finished = job.progress.finished === job.progress.total

  return (
    <div className="min-h-0 flex-1 overflow-y-auto p-3">
      <section className="overflow-hidden rounded-2xl bg-white pt-4 shadow-card ring-1 ring-slate-200/70">
        <p className="px-4 pb-3 text-xs text-slate-500">
          {pluralize(rows.length, 'case')} from {pluralize(job.progress.finished, 'person', 'people')} finished of{' '}
          {job.progress.total}. Without a date of birth in the CSV no match is confirmed.
        </p>
        {rows.length > 0 && <CasesTable rows={rows} onOpen={onOpenCase} />}
        {rows.length === 0 && finished && (
          <EmptyState icon={<FileSearch size={20} />} title="No cases found" hint="No searched person has cases on the portal." />
        )}
        {rows.length === 0 && !finished && <SkeletonRows count={4} />}
      </section>
    </div>
  )
}
