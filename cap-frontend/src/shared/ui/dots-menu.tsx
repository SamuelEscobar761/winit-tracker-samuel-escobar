import { useEffect, useRef, useState, type ReactNode } from 'react'
import { MoreVertical } from 'lucide-react'

export interface MenuItem {
  label: string
  onClick: () => void
  icon?: ReactNode
}

interface DotsMenuProps {
  items: MenuItem[]
  dark?: boolean
}

function useCloseOnOutsideClick(isOpen: boolean, close: () => void) {
  const containerRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!isOpen) return
    const handle = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) close()
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [isOpen, close])
  return containerRef
}

export function DotsMenu({ items, dark = false }: DotsMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useCloseOnOutsideClick(isOpen, () => setIsOpen(false))
  const tone = dark ? 'text-white/80 hover:bg-white/20' : 'text-slate-500 hover:bg-slate-100'

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-label="Pane menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((open) => !open)}
        className={`grid size-7 place-items-center rounded-md transition ${tone}`}
      >
        <MoreVertical size={16} />
      </button>
      {isOpen && (
        <div className="animate-fade-in absolute right-0 z-20 mt-1 w-52 overflow-hidden rounded-xl bg-white p-1 shadow-pop ring-1 ring-slate-200">
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => {
                setIsOpen(false)
                item.onClick()
              }}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
