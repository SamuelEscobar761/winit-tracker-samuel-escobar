export const SAMPLE_CSV = `first_name,last_name,date_of_birth,external_ref
John,Smith,,DRV-1001
Pedro,Rodriguez,,DRV-1002
# the next rows are rejected on purpose
,Smith,,DRV-1003
Pedro;Rodriguez,,DRV-1004
J0hn,Smith,31/02/1990,DRV-1005
`

export function sampleCsvFile(): File {
  return new File([SAMPLE_CSV], 'sample-drivers.csv', { type: 'text/csv' })
}
