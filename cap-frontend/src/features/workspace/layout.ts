export type Layout = 2 | 4

export function splitSlots<T>(slots: T[], layout: Layout): T[][] {
  if (layout === 2) return [slots]
  const topCount = Math.ceil(slots.length / 2)
  return [slots.slice(0, topCount), slots.slice(topCount)]
}
