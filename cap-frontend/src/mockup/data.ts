// MOCKUP ONLY — all names, case numbers and details below are invented.
export type Confidence = 'confirmed' | 'probable' | 'possible'
export type CaseType = 'Traffic' | 'Civil' | 'Criminal' | 'Probate'
export type CaseStatus = 'Open' | 'Closed' | 'Disposed'

export interface CaseRecord {
  caseNumber: string
  type: CaseType
  title: string
  status: CaseStatus
  filingDate: string
  nextHearing: string | null
  location: string
  parties: { name: string; role: string; dob?: string }[]
  charges: { code: string; description: string; severity: string }[]
  hearings: { date: string; time: string; dept: string; type: string; past: boolean }[]
  confidence: Confidence
  reasons: string[]
  limited?: boolean // criminal: only register/calendar online (CRC 2.503)
}

export interface Script {
  captcha?: boolean
  error?: boolean
  total?: number // total matches on CAP when more than we keep
  cases: CaseRecord[]
}

const SB = 'San Bernardino Justice Center'
const RC = 'Rancho Cucamonga District'

const c = (
  caseNumber: string,
  type: CaseType,
  title: string,
  status: CaseStatus,
  filingDate: string,
  nextHearing: string | null,
  location: string,
  confidence: Confidence,
  reasons: string[],
  role = 'Defendant',
  extra: Partial<CaseRecord> = {},
): CaseRecord => ({
  caseNumber,
  type,
  title,
  status,
  filingDate,
  nextHearing,
  location,
  parties: [{ name: title.split(' v. ').pop() ?? title, role }],
  charges: [],
  hearings: nextHearing
    ? [
        { date: filingDate, time: '08:30', dept: 'S14', type: 'Arraignment', past: true },
        { date: nextHearing, time: '09:00', dept: 'S14', type: 'Hearing', past: false },
      ]
    : [{ date: filingDate, time: '08:30', dept: 'S14', type: 'Arraignment', past: true }],
  confidence,
  reasons,
  ...extra,
})

const NO_DOB = 'No date of birth provided: cannot be confirmed'

const smith: CaseRecord[] = [
  c('TVI2501877', 'Traffic', 'People v. Smith, John Allen', 'Open', '2026-08-12', '2026-11-04', SB, 'probable',
    ['Name matches exactly', 'Party role is defendant', NO_DOB],
    'Defendant', { charges: [{ code: 'VC 22350', description: 'Unsafe speed for conditions', severity: 'Infraction' }] }),
  c('CIVSB2412903', 'Civil', 'Midway Credit v. Smith, John', 'Open', '2026-03-02', '2026-12-10', SB, 'possible',
    ['Name matches', 'Common name: 48 other John Smith records', NO_DOB]),
  c('FWV2401122', 'Criminal', 'People v. Smith, John M', 'Disposed', '2025-02-19', null, RC, 'possible',
    ['Name matches', 'Middle initial differs from other candidates', NO_DOB], 'Defendant',
    { limited: true, charges: [{ code: 'PC 484', description: 'Petty theft', severity: 'Misdemeanor' }] }),
  c('TVI2307744', 'Traffic', 'People v. Smith, John', 'Closed', '2023-07-30', null, RC, 'possible',
    ['Name matches', 'Filed in a different district than the others', NO_DOB]),
  c('CIVRS2218820', 'Civil', 'Smith, John v. Pacific Rentals', 'Closed', '2022-05-11', null, SB, 'possible',
    ['Name matches', 'Party role is plaintiff, not defendant', NO_DOB], 'Plaintiff'),
  c('PROSB2200319', 'Probate', 'Estate of Smith, John Robert', 'Closed', '2022-01-14', null, SB, 'possible',
    ['Name matches a deceased party: likely a different person', NO_DOB], 'Decedent'),
]

const pedro: CaseRecord[] = [
  c('TVI2602310', 'Traffic', 'People v. Rodríguez, Pedro', 'Open', '2026-09-03', '2026-10-28', RC, 'probable',
    ['Accent-insensitive name match (Rodriguez / Rodríguez)', 'Listed as "RODRIGUEZ PEDRO" in the source', NO_DOB],
    'Defendant', { charges: [{ code: 'VC 21453', description: 'Red light violation', severity: 'Infraction' }] }),
  c('CIVDS2519004', 'Civil', 'Rodriguez, Pedro v. Inland Auto Group', 'Open', '2025-11-20', '2027-01-15', SB, 'possible',
    ['Name order reversed in source', 'Plaintiff role', NO_DOB], 'Plaintiff'),
  c('TVI2410551', 'Traffic', 'People v. Rodriguez, Pedro J', 'Closed', '2024-10-02', null, RC, 'possible',
    ['Middle initial present only in this case', NO_DOB]),
]

const carlos: CaseRecord[] = [
  c('TVI2603001', 'Traffic', 'People v. Mendoza, Carlos', 'Open', '2026-09-21', '2026-11-18', SB, 'probable',
    ['Name matches exactly', NO_DOB]),
  c('TVI2504120', 'Traffic', 'People v. Mendoza, Carlos E', 'Disposed', '2025-04-08', null, SB, 'possible',
    ['Name matches', 'Middle initial present only in this case', NO_DOB]),
]

const luis: CaseRecord[] = [
  c('CIVSB2601554', 'Civil', 'Valley Finance v. Hernandez, Luis', 'Open', '2026-06-09', '2026-12-02', SB, 'possible',
    ['Name matches', NO_DOB]),
]

export const SCRIPTS: Record<string, Script> = {
  'john smith': { cases: smith, total: 48 },
  'pedro rodriguez': { cases: pedro },
  'carlos mendoza': { cases: carlos },
  'luis hernandez': { captcha: true, cases: luis },
  'ana torres': { error: true, cases: [] },
  'maria gonzalez': { cases: [] },
}

export const foldName = (first: string, last: string) =>
  `${first} ${last}`
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .trim()
    .replace(/\s+/g, ' ')
    .toLowerCase()

export const rawFor = (k: CaseRecord) =>
  `<div class="case-summary" data-case="${k.caseNumber}">
  <h2>${k.title}</h2>
  <table class="info">
    <tr><th>Case Number</th><td>${k.caseNumber}</td></tr>
    <tr><th>Case Type</th><td>${k.type}</td></tr>
    <tr><th>Filing Date</th><td>${k.filingDate.split('-').reverse().join('/')}</td></tr>
    <tr><th>Status</th><td>${k.status}</td></tr>
    <tr><th>Location</th><td>${k.location}</td></tr>
  </table>
  ${k.parties.map((p) => `<li class="party">${p.name.toUpperCase()} — ${p.role}</li>`).join('\n  ')}
  ${k.hearings.map((h) => `<tr class="hearing"><td>${h.date}</td><td>${h.time}</td><td>${h.dept}</td><td>${h.type}</td></tr>`).join('\n  ')}
</div>`

export const SAMPLE_CSV = `first_name,last_name,date_of_birth,external_ref
John,Smith,,DRV-1001
Pedro,Rodriguez,,DRV-1002
# your validator must reject or flag the rows below gracefully
,Smith,,DRV-1003
Pedro;Rodriguez,,DRV-1004
J0hn,Smith,31/02/1990,DRV-1005
  maria , GONZALEZ ,,DRV-1006
Luis,Hernandez,,DRV-1007
Ana,Torres,,DRV-1008
Carlos,Mendoza,,DRV-1009
John,Smith,,DRV-1010`
