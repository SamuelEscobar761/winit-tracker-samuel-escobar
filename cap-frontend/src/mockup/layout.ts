import type { Job } from './sim'

export type Layout = 2 | 4

// 2 panes: one list per side. 4 panes: top lists get ceil(N/2) jobs, bottom lists the rest.
export const splitJobs = (jobs: Job[], layout: Layout): Job[][] =>
  layout === 2 ? [jobs] : [jobs.slice(0, Math.ceil(jobs.length / 2)), jobs.slice(Math.ceil(jobs.length / 2))]
