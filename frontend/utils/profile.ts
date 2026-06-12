import type { Cell, ColumnProfile, DatasetProfile, QualityFlag, Row } from '~/types'
import {
  ascending,
  deviation,
  histogram,
  isBlank,
  mean,
  pearson,
  quantileSorted,
} from '~/utils/stats'

export function profileColumn(name: string, values: Cell[]): ColumnProfile {
  const present = values.filter((v) => !isBlank(v))
  const missing = values.length - present.length
  const asNum = present.map((v) => (typeof v === 'number' ? v : Number(v)))
  const numericCount = asNum.filter((v) => !Number.isNaN(v)).length
  const numeric = present.length > 0 && numericCount >= present.length * 0.85
  const unique = new Set(present.map(String)).size

  const out: ColumnProfile = {
    name,
    type: numeric ? 'numeric' : 'categorical',
    count: present.length,
    missing,
    missingPct: values.length ? missing / values.length : 0,
    unique,
  }

  if (numeric) {
    const nums = asNum.filter((v) => !Number.isNaN(v)).sort(ascending)
    out.values = nums
    out.min = nums[0]
    out.max = nums[nums.length - 1]
    out.mean = mean(nums)
    out.std = deviation(nums)
    out.median = quantileSorted(nums, 0.5)
    out.q25 = quantileSorted(nums, 0.25)
    out.q75 = quantileSorted(nums, 0.75)
    out.bins = histogram(nums, 14)
    // IQR outlier count
    const iqr = out.q75 - out.q25
    const lo = out.q25 - 1.5 * iqr
    const hi = out.q75 + 1.5 * iqr
    out.outliers = nums.filter((v) => v < lo || v > hi).length
  } else {
    const counts = new Map<string, number>()
    for (const v of present) counts.set(String(v), (counts.get(String(v)) ?? 0) + 1)
    out.top = Array.from(counts, ([k, n]) => ({ k, n })).sort((a, b) => b.n - a.n)
  }
  return out
}

export function buildProfile(rows: Row[]): DatasetProfile | null {
  if (!rows?.length) return null
  const columns = Object.keys(rows[0])
  const profiles = columns.map((c) =>
    profileColumn(c, rows.map((r) => r[c])),
  )
  const numericCols = profiles.filter((p) => p.type === 'numeric').map((p) => p.name)
  const categoricalCols = profiles.filter((p) => p.type === 'categorical').map((p) => p.name)

  const corr: Record<string, Record<string, number>> = {}
  for (const a of numericCols) {
    corr[a] = {}
    for (const b of numericCols) {
      if (a === b) {
        corr[a][b] = 1
        continue
      }
      const pairs = rows
        .map((r) => [Number(r[a]), Number(r[b])] as [number, number])
        .filter(([x, y]) => !Number.isNaN(x) && !Number.isNaN(y))
      corr[a][b] = pearson(pairs)
    }
  }

  const seen = new Set<string>()
  let dup = 0
  for (const r of rows) {
    const k = JSON.stringify(r)
    if (seen.has(k)) dup++
    else seen.add(k)
  }
  const totalCells = rows.length * columns.length
  const missingCells = profiles.reduce((s, p) => s + p.missing, 0)

  return {
    rows,
    columns,
    profiles,
    numericCols,
    categoricalCols,
    corr,
    stats: {
      nRows: rows.length,
      nCols: columns.length,
      nNumeric: numericCols.length,
      nCategorical: categoricalCols.length,
      missingPct: totalCells ? missingCells / totalCells : 0,
      duplicates: dup,
    },
  }
}

/** Drivers of a chosen target column, ranked by absolute correlation. */
export function targetCorrelations(
  profile: DatasetProfile,
  target: string,
): { name: string; r: number }[] {
  if (!profile.numericCols.includes(target)) return []
  return profile.numericCols
    .filter((c) => c !== target)
    .map((c) => ({ name: c, r: profile.corr[target][c] }))
    .filter((d) => !Number.isNaN(d.r))
    .sort((a, b) => Math.abs(b.r) - Math.abs(a.r))
}

export function qualityFlags(profile: DatasetProfile): QualityFlag[] {
  const flags: QualityFlag[] = []
  for (const p of profile.profiles) {
    if (p.missingPct > 0.3)
      flags.push({ level: 'warn', code: 'highMissing', params: { name: p.name, pct: (p.missingPct * 100).toFixed(1) } })
    if (p.unique === 1)
      flags.push({ level: 'warn', code: 'constant', params: { name: p.name } })
    if (p.type === 'categorical' && p.unique === p.count && p.count > 1)
      flags.push({ level: 'warn', code: 'idLike', params: { name: p.name } })
    if (p.type === 'numeric' && (p.outliers ?? 0) > 0)
      flags.push({ level: 'warn', code: 'outliers', params: { name: p.name, n: p.outliers ?? 0 } })
  }
  if (profile.stats.duplicates > 0)
    flags.push({ level: 'warn', code: 'duplicates', params: { n: profile.stats.duplicates } })
  if (!flags.length) flags.push({ level: 'ok', code: 'ok' })
  return flags
}
