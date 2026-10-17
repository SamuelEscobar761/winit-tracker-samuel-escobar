import { describe, expect, it } from 'vitest'
import { keyToInput, toFrameCoordinates } from './frame-input'

const rect = { left: 100, top: 50, width: 400, height: 250 }
const frame = { width: 800, height: 500 }

describe('toFrameCoordinates', () => {
  it('scales a click on the shown image to the frame pixels', () => {
    expect(toFrameCoordinates({ clientX: 300, clientY: 175 }, rect, frame)).toEqual({ x: 400, y: 250 })
    expect(toFrameCoordinates({ clientX: 100, clientY: 50 }, rect, frame)).toEqual({ x: 0, y: 0 })
  })

  it('refuses to guess when the image or frame has no size yet', () => {
    expect(toFrameCoordinates({ clientX: 1, clientY: 1 }, { ...rect, width: 0 }, frame)).toBeNull()
    expect(toFrameCoordinates({ clientX: 1, clientY: 1 }, rect, { width: 0, height: 0 })).toBeNull()
  })
})

describe('keyToInput', () => {
  it('turns printable characters into text', () => {
    expect(keyToInput('a', false)).toEqual({ type: 'text', text: 'a' })
  })

  it('forwards the allowed named keys and the space', () => {
    expect(keyToInput('Enter', false)).toEqual({ type: 'key', key: 'Enter' })
    expect(keyToInput(' ', false)).toEqual({ type: 'key', key: ' ' })
  })

  it('ignores shortcuts and unknown keys', () => {
    expect(keyToInput('c', true)).toBeNull()
    expect(keyToInput('F12', false)).toBeNull()
    expect(keyToInput('Shift', false)).toBeNull()
  })
})
