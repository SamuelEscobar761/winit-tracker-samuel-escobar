import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import type { RawCase } from '../../shared/api/api-types'
import type { RawCaseState } from './use-raw-case'

type Tab = 'search' | 'detail'

function selectedJson(raw: RawCase, tab: Tab): string {
  const value = tab === 'search' ? raw.search_item : raw.detail_response
  return value ? JSON.stringify(value, null, 2) : 'This case has no detail response.'
}

function sourceLine(raw: RawCase, tab: Tab): string {
  const url = tab === 'search' ? raw.search_source_url : raw.detail_source_url
  const when = tab === 'search' ? raw.search_scraped_at : raw.detail_scraped_at
  return url ? `Source: ${url}${when ? ` · scraped_at ${when}` : ''}` : 'No source recorded.'
}

function TabButton({ tab, current, onSelect, label }: { tab: Tab; current: Tab; onSelect: (tab: Tab) => void; label: string }) {
  const isActive = tab === current
  return (
    <button
      type="button"
      onClick={() => onSelect(tab)}
      aria-pressed={isActive}
      className={`rounded-md px-2.5 py-1 text-xs font-medium ${isActive ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'}`}
    >
      {label}
    </button>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button
      type="button"
      onClick={copy}
      className="ml-auto inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
    >
      {copied ? <Check size={13} /> : <Copy size={13} />} {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

export function RawSourcePanel({ state }: { state: RawCaseState }) {
  const [tab, setTab] = useState<Tab>('search')
  if (state.status === 'loading') return <p className="animate-pulse text-xs text-slate-500">Loading the raw source…</p>
  if (state.status === 'error') return <p className="text-xs text-rose-400">The raw source is not available.</p>
  const text = selectedJson(state.raw, tab)

  return (
    <>
      <div className="mb-3 flex items-center gap-1">
        <TabButton tab="search" current={tab} onSelect={setTab} label="Search result" />
        <TabButton tab="detail" current={tab} onSelect={setTab} label="Case details" />
        <CopyButton text={text} />
      </div>
      <pre className="min-h-0 flex-1 overflow-auto whitespace-pre-wrap font-mono text-xs leading-relaxed">{text}</pre>
      <p className="mt-3 break-all text-[11px] text-slate-500">{sourceLine(state.raw, tab)}</p>
    </>
  )
}
