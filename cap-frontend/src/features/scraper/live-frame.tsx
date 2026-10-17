import type { KeyboardEvent, MouseEvent, RefObject } from 'react'
import type { InputEvent } from '../../shared/api/api-types'
import { keyToInput, toFrameCoordinates, type FrameSize } from './frame-input'

interface LiveFrameProps {
  imageRef: RefObject<HTMLImageElement | null>
  frameSize: RefObject<FrameSize>
  hasFrame: boolean
  isInteractive: boolean
  onInput: (event: InputEvent) => void
  placeholder: string
}

export function LiveFrame({ imageRef, frameSize, hasFrame, isInteractive, onInput, placeholder }: LiveFrameProps) {
  const handleClick = (event: MouseEvent<HTMLDivElement>) => {
    const image = imageRef.current
    if (!isInteractive || !image) return
    const point = toFrameCoordinates(event, image.getBoundingClientRect(), frameSize.current)
    if (point) onInput({ type: 'click', ...point })
  }
  const handleKey = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!isInteractive) return
    const input = keyToInput(event.key, event.ctrlKey || event.metaKey || event.altKey)
    if (!input) return
    event.preventDefault()
    onInput(input)
  }

  return (
    <div
      role="application"
      aria-label="Live browser view"
      tabIndex={isInteractive ? 0 : -1}
      onClick={handleClick}
      onKeyDown={handleKey}
      className={`absolute inset-0 flex items-center justify-center bg-slate-950 outline-none ${isInteractive ? 'cursor-pointer ring-2 ring-inset ring-amber-400 focus:ring-4' : ''}`}
    >
      <img
        ref={imageRef}
        alt="Live view of the portal browser"
        draggable={false}
        className={`max-h-full max-w-full select-none object-contain ${hasFrame ? '' : 'hidden'}`}
      />
      {!hasFrame && <p className="text-xs text-slate-400">{placeholder}</p>}
    </div>
  )
}
