<script setup lang="ts">
import type { Row } from '~/types'
import { ascending, fmt, quantileSorted } from '~/utils/stats'
const props = defineProps<{ rows: Row[]; valueCol: string; groupCol: string }>()
const { t } = useI18n()
const PAL = ['var(--c0)', 'var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)', 'var(--c5)']
const groups = computed(() => {
  const map = new Map<string, number[]>()
  for (const r of props.rows) {
    const g = String(r[props.groupCol])
    const v = Number(r[props.valueCol])
    if (g === 'null' || g === 'undefined' || Number.isNaN(v)) continue
    if (!map.has(g)) map.set(g, [])
    map.get(g)!.push(v)
  }
  return Array.from(map, ([k, vals]) => {
    const s = vals.sort(ascending)
    const q1 = quantileSorted(s, 0.25), q2 = quantileSorted(s, 0.5), q3 = quantileSorted(s, 0.75)
    const iqr = q3 - q1
    const lo = Math.max(s[0], q1 - 1.5 * iqr), hi = Math.min(s[s.length - 1], q3 + 1.5 * iqr)
    return { k, q1, q2, q3, lo, hi, n: vals.length }
  }).sort((a, b) => b.q2 - a.q2).slice(0, 8)
})
const W = 560, H = 320, m = { t: 16, r: 16, b: 48, l: 56 }
const iw = W - m.l - m.r, ih = H - m.t - m.b
const yMin = computed(() => Math.min(...groups.value.map((g) => g.lo)))
const yMax = computed(() => Math.max(...groups.value.map((g) => g.hi)))
const y = (v: number) => ih - ((v - yMin.value) / ((yMax.value - yMin.value) || 1)) * ih
const bandW = computed(() => iw / Math.max(groups.value.length, 1))
const boxW = computed(() => Math.min(54, bandW.value * 0.5))
const cx = (i: number) => i * bandW.value + bandW.value / 2
const yTicks = computed(() => [0, 1, 2, 3, 4].map((i) => yMin.value + (i / 4) * (yMax.value - yMin.value)))
</script>

<template>
  <svg width="100%" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="t('aria.boxplot', { value: valueCol, group: groupCol })">
    <g :transform="`translate(${m.l},${m.t})`">
      <g v-for="(t, i) in yTicks" :key="i" :transform="`translate(0,${y(t)})`">
        <line :x2="iw" stroke="var(--line-soft)" />
        <text :x="-10" dy="0.32em" text-anchor="end" font-size="11" fill="var(--faint)" font-family="var(--font-mono)">{{ fmt(t, 0) }}</text>
      </g>
      <g v-for="(g, i) in groups" :key="g.k">
        <line :x1="cx(i)" :x2="cx(i)" :y1="y(g.hi)" :y2="y(g.lo)" stroke="var(--muted)" stroke-width="1" />
        <line :x1="cx(i) - boxW / 3" :x2="cx(i) + boxW / 3" :y1="y(g.hi)" :y2="y(g.hi)" stroke="var(--muted)" />
        <line :x1="cx(i) - boxW / 3" :x2="cx(i) + boxW / 3" :y1="y(g.lo)" :y2="y(g.lo)" stroke="var(--muted)" />
        <rect :x="cx(i) - boxW / 2" :y="y(g.q3)" :width="boxW" :height="Math.max(1, y(g.q1) - y(g.q3))"
          rx="3" :fill="PAL[i % PAL.length]" opacity="0.22" :stroke="PAL[i % PAL.length]" stroke-width="1.5" />
        <line :x1="cx(i) - boxW / 2" :x2="cx(i) + boxW / 2" :y1="y(g.q2)" :y2="y(g.q2)" :stroke="PAL[i % PAL.length]" stroke-width="2" />
        <text :x="cx(i)" :y="ih + 18" text-anchor="middle" font-size="11.5" fill="var(--ink)">
          {{ g.k.length > 6 ? g.k.slice(0, 6) + '…' : g.k }}
        </text>
        <text :x="cx(i)" :y="ih + 33" text-anchor="middle" font-size="10" fill="var(--faint)" font-family="var(--font-mono)">n={{ g.n }}</text>
      </g>
    </g>
  </svg>
</template>
