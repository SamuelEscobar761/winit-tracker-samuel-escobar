export type Route =
  | { name: 'home' }
  | { name: 'job'; jobId: string }
  | { name: 'live'; lane: number }
  | { name: 'rules' }

const JOB_PATTERN = /^#\/job\/([A-Za-z0-9_-]+)$/
const LIVE_PATTERN = /^#\/live\/(\d+)$/

export function parseRoute(hash: string): Route {
  if (hash === '#/rules') return { name: 'rules' }
  const job = JOB_PATTERN.exec(hash)
  if (job) return { name: 'job', jobId: job[1] }
  const live = LIVE_PATTERN.exec(hash)
  if (live) return { name: 'live', lane: Number(live[1]) }
  return { name: 'home' }
}

export const jobHash = (jobId: string) => `#/job/${jobId}`
export const liveHash = (lane: number) => `#/live/${lane}`
export const RULES_HASH = '#/rules'
