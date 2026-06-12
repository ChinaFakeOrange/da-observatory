export type Cell = string | number | null

export interface Row {
  [key: string]: Cell
}

export interface Bin {
  x0: number
  x1: number
  n: number
}

export interface ColumnProfile {
  name: string
  type: 'numeric' | 'categorical'
  count: number
  missing: number
  missingPct: number
  unique: number
  // numeric
  values?: number[]
  min?: number
  max?: number
  mean?: number
  std?: number
  median?: number
  q25?: number
  q75?: number
  bins?: Bin[]
  outliers?: number
  // categorical
  top?: { k: string; n: number }[]
}

export interface DatasetProfile {
  rows: Row[]
  columns: string[]
  profiles: ColumnProfile[]
  numericCols: string[]
  categoricalCols: string[]
  corr: Record<string, Record<string, number>>
  stats: {
    nRows: number
    nCols: number
    nNumeric: number
    nCategorical: number
    missingPct: number
    duplicates: number
  }
}

export interface QualityFlag {
  level: 'warn' | 'ok'
  code: 'highMissing' | 'constant' | 'idLike' | 'outliers' | 'duplicates' | 'ok'
  params?: Record<string, string | number>
}
