import type { InputEvent } from '../../shared/api/api-types'

export interface FrameSize {
  width: number
  height: number
}

export interface ViewRect {
  left: number
  top: number
  width: number
  height: number
}

export function toFrameCoordinates(
  point: { clientX: number; clientY: number },
  rect: ViewRect,
  frame: FrameSize,
): { x: number; y: number } | null {
  if (rect.width <= 0 || rect.height <= 0 || frame.width <= 0 || frame.height <= 0) return null
  return {
    x: Math.round(((point.clientX - rect.left) / rect.width) * frame.width),
    y: Math.round(((point.clientY - rect.top) / rect.height) * frame.height),
  }
}

const NAMED_KEYS: ReadonlySet<string> = new Set([
  'Enter',
  'Tab',
  'Backspace',
  'Escape',
  'ArrowUp',
  'ArrowDown',
  'ArrowLeft',
  'ArrowRight',
])

export function keyToInput(key: string, hasModifier: boolean): InputEvent | null {
  if (hasModifier) return null
  if (key === ' ' || NAMED_KEYS.has(key)) return { type: 'key', key }
  if (key.length === 1) return { type: 'text', text: key }
  return null
}
