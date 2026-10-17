import { useEffect, useState } from 'react'
import type { JobListItem } from '../../shared/api/api-types'
import { jobsApi } from '../../shared/api/jobs-api'
import { pluralize, shortJobId } from '../../shared/lib/format'
import { jobHash } from '../../shared/routing/hash-route'
import { navigate } from '../../shared/routing/use-hash-route'
import { Badge } from '../../shared/ui/badge'
import type { Tone } from '../../shared/ui/tone'

const STATE_TONES: Record<JobListItem['state'], Tone> = {
  queued: 'slate',
  running: 'indigo',
  completed: 'green',
  cancelled: 'red',
}

export function RecentJobs() {
  const [jobs, setJobs] = useState<JobListItem[]>([])

  useEffect(() => {
    jobsApi
      .list()
      .then(setJobs)
      .catch(() => setJobs([]))
  }, [])

  if (jobs.length === 0) return null
  return (
    <section className="mt-6 rounded-3xl bg-white p-5 shadow-card ring-1 ring-slate-200/70">
      <h2 className="text-sm font-semibold text-slate-900">Recent jobs</h2>
      <ul className="mt-3 divide-y divide-slate-100">
        {jobs.slice(0, 6).map((job) => (
          <li key={job.job_id}>
            <button
              type="button"
              onClick={() => navigate(jobHash(job.job_id))}
              className="flex w-full items-center gap-3 py-2 text-left text-sm hover:bg-slate-50"
            >
              <span className="font-mono text-xs text-slate-500">{shortJobId(job.job_id)}</span>
              <span className="text-slate-700">{pluralize(job.total_people, 'person', 'people')}</span>
              <span className="text-xs text-slate-400">{job.progress.percent}%</span>
              <span className="ml-auto">
                <Badge tone={STATE_TONES[job.state]}>{job.state}</Badge>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
