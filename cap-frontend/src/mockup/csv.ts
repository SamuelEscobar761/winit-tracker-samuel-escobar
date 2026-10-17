import { foldName } from './data'

export interface Person {
  id: string
  firstName: string
  lastName: string
  ref: string
  key: string
}

export interface RowReport {
  line: number
  raw: string
  status: 'accepted' | 'normalized' | 'rejected'
  reason?: string
  person?: Person
}

const NAME_RE = /^[\p{L}][\p{L}'’\- ]*$/u
const titleCase = (s: string) =>
  s
    .trim()
    .replace(/\s+/g, ' ')
    .toLowerCase()
    .replace(/(^|[\s'’-])(\p{L})/gu, (_, sep: string, ch: string) => sep + ch.toUpperCase())

const validDob = (s: string) => {
  const m = s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/) ?? s.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!m) return false
  const [d, mo, y] = s.includes('/') ? [+m[1], +m[2], +m[3]] : [+m[3], +m[2], +m[1]]
  const dt = new Date(y, mo - 1, d)
  return dt.getFullYear() === y && dt.getMonth() === mo - 1 && dt.getDate() === d
}

export function validateCsv(text: string): RowReport[] {
  const out: RowReport[] = []
  const seen = new Map<string, number>()
  let headerSeen = false
  text.split(/\r?\n/).forEach((raw, i) => {
    const line = i + 1
    if (!raw.trim() || raw.trim().startsWith('#')) return
    if (!headerSeen) {
      headerSeen = true
      return
    }
    const cols = raw.split(',')
    if (cols.length < 2) {
      const delim = raw.includes(';') ? ';' : 'unknown'
      return void out.push({ line, raw, status: 'rejected', reason: `Wrong delimiter (found "${delim}", expected ",")` })
    }
    const [first, last, dob = '', ref = ''] = cols.map((s) => s.trim())
    const problems: string[] = []
    if (!first) problems.push('first_name is empty')
    else if (!NAME_RE.test(first)) problems.push('first_name has invalid characters')
    if (!last) problems.push('last_name is empty')
    else if (!NAME_RE.test(last)) problems.push('last_name has invalid characters')
    if (dob && !validDob(dob)) problems.push(`date_of_birth "${dob}" is not a real date`)
    if (problems.length) return void out.push({ line, raw, status: 'rejected', reason: problems.join('; ') })

    const key = `${foldName(first, last)}|${dob}`
    if (seen.has(key))
      return void out.push({ line, raw, status: 'rejected', reason: `Duplicate of line ${seen.get(key)}` })
    seen.set(key, line)

    const f = titleCase(first)
    const l = titleCase(last)
    const person: Person = { id: '', firstName: f, lastName: l, ref, key: foldName(f, l) }
    const changed = f !== first || l !== last
    out.push({
      line,
      raw,
      status: changed ? 'normalized' : 'accepted',
      reason: changed ? `"${first} ${last}" → "${f} ${l}"` : undefined,
      person,
    })
  })
  let n = 0
  out.forEach((r) => r.person && (r.person.id = `P-${String(++n).padStart(2, '0')}`))
  return out
}
