<script setup lang="ts">
import type { Row } from '~/types'
const props = defineProps<{ rows: Row[]; cols: string[]; colorCol?: string | null }>()
const { t } = useI18n()
const PAL = ['var(--c0)', 'var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)', 'var(--c5)']
const dims = computed(() => props.cols.slice(0, 4))
const cell = 118, pad = 8
const size = computed(() => dims.value.length * cell)
const cats = computed(() => (props.colorCol ? Array.from(new Set(props.rows.map((r) => String(r[props.colorCol!])))) : []))
const cColor = (r: Row) => (props.colorCol ? PAL[cats.value.indexOf(String(r[props.colorCol])) % PAL.length] : 'var(--accent)')
function extent(col: string): [number, number] {
  const v = props.rows.map((r) => Number(r[col])).filter((x) => !Number.isNaN(x))
  return [Math.min(...v), Math.max(...v)]
}
const exts = computed(() => Object.fromEntries(dims.value.map((c) => [c, extent(c)])) as Record<string, [number, number]>)
function px(col: string, v: number) { const [a, b] = exts.value[col]; return pad + ((v - a) / ((b - a) || 1)) * (cell - 2 * pad) }
function py(col: string, v: number) { const [a, b] = exts.value[col]; return cell - pad - ((v - a) / ((b - a) || 1)) * (cell - 2 * pad) }
const pairs = computed(() => {
  const out: { gi: number; gj: number; diag: boolean; xCol: string; yCol: string }[] = []
  dims.value.forEach((yCol, gi) => dims.value.forEach((xCol, gj) => out.push({ gi, gj, diag: gi === gj, xCol, yCol })))
  return out
})
</script>

<template>
  <svg width="100%" :viewBox="`0 0 ${size + 70} ${size + 24}`" role="img" :aria-label="t('aria.scatterMatrix')">
    <g transform="translate(60,8)">
      <g v-for="(p, k) in pairs" :key="k" :transform="`translate(${p.gj * cell},${p.gi * cell})`">
        <rect :width="cell - 2" :height="cell - 2" rx="4" fill="var(--surface-2)" stroke="var(--line)" />
        <template v-if="p.diag">
          <text :x="(cell - 2) / 2" :y="(cell - 2) / 2" dy="0.32em" text-anchor="middle"
            font-size="13" font-weight="600" fill="var(--ink)" font-family="var(--font-display)">{{ p.xCol }}</text>
        </template>
        <template v-else>
          <circle v-for="(r, ri) in rows" :key="ri" :cx="px(p.xCol, Number(r[p.xCol]))" :cy="py(p.yCol, Number(r[p.yCol]))"
            r="2" :fill="cColor(r)" opacity="0.5" />
        </template>
      </g>
    </g>
  </svg>
</template>
