import type { Bin, Cell } from '~/types'

export const isBlank = (v: Cell): boolean =>
  v === null || v === undefined || v === '' || (typeof v === 'number' && Number.isNaN(v))

export function ascending(a: number, b: number): number {
  return a - b
}

export function mean(arr: number[]): number {
  if (!arr.length) return NaN
  return arr.reduce((s, v) => s + v, 0) / arr.length
}

export function deviation(arr: number[]): number {
  if (arr.length < 2) return 0
  const m = mean(arr)
  const v = arr.reduce((s, x) => s + (x - m) ** 2, 0) / (arr.length - 1)
  return Math.sqrt(v)
}

/** quantile on an already-sorted ascending array (linear interpolation). */
export function quantileSorted(sorted: number[], q: number): number {
  if (!sorted.length) return NaN
  const pos = (sorted.length - 1) * q
  const base = Math.floor(pos)
  const rest = pos - base
  return sorted[base + 1] !== undefined
    ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
    : sorted[base]
}

/** Equal-width histogram bins over [min, max]. */
export function histogram(values: number[], thresholds = 14): Bin[] {
  if (!values.length) return []
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (min === max) return [{ x0: min, x1: max, n: values.length }]
  const step = (max - min) / thresholds
  const bins: Bin[] = Array.from({ length: thresholds }, (_, i) => ({
    x0: min + i * step,
    x1: min + (i + 1) * step,
    n: 0,
  }))
  for (const v of values) {
    let idx = Math.floor((v - min) / step)
    if (idx >= thresholds) idx = thresholds - 1
    if (idx < 0) idx = 0
    bins[idx].n++
  }
  return bins
}

export function pearson(pairs: [number, number][]): number {
  const n = pairs.length
  if (n < 3) return NaN
  const mx = mean(pairs.map((p) => p[0]))
  const my = mean(pairs.map((p) => p[1]))
  let num = 0
  let dx = 0
  let dy = 0
  for (const [x, y] of pairs) {
    num += (x - mx) * (y - my)
    dx += (x - mx) ** 2
    dy += (y - my) ** 2
  }
  const den = Math.sqrt(dx * dy)
  return den === 0 ? NaN : num / den
}

export const fmt = (v: number | null | undefined, d = 2): string => {
  if (v == null || Number.isNaN(v)) return '—'
  const a = Math.abs(v)
  if (a >= 10000) return v.toLocaleString('en-US', { maximumFractionDigits: 0 })
  if (a >= 100) return v.toLocaleString('en-US', { maximumFractionDigits: 1 })
  return v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })
}

export const pct = (v: number): string => `${(v * 100).toFixed(1)}%`
