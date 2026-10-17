import { useState } from 'react'
import { FileUp, Wand2 } from 'lucide-react'
import { sampleCsvFile } from './sample-csv'

interface DropZoneProps {
  onFile: (file: File) => void
  fileName: string | null
}

export function DropZone({ onFile, fileName }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(event) => {
        event.preventDefault()
        setIsDragging(false)
        const file = event.dataTransfer.files[0]
        if (file) onFile(file)
      }}
      className={`mt-8 flex flex-col items-center gap-2 rounded-3xl border-2 border-dashed bg-white px-6 py-10 text-center shadow-card transition ${isDragging ? 'border-indigo-400 bg-indigo-50/40' : 'border-slate-200'}`}
    >
      <div className="grid size-12 place-items-center rounded-2xl bg-indigo-50 text-indigo-600">
        <FileUp size={22} />
      </div>
      <label className="cursor-pointer text-sm font-semibold text-slate-800 focus-within:underline hover:text-indigo-700">
        {fileName ? fileName : 'Drop your CSV here, or click to browse'}
        <input
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) onFile(file)
          }}
        />
      </label>
      <p className="text-xs text-slate-500">
        Columns: first_name, last_name, date_of_birth (optional), external_ref (optional)
      </p>
      <button
        type="button"
        onClick={() => onFile(sampleCsvFile())}
        className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-700"
      >
        <Wand2 size={13} /> Use sample CSV
      </button>
    </div>
  )
}
