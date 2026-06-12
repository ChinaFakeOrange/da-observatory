<script setup lang="ts">
import type { Row } from '~/types'
import { fmt, mean } from '~/utils/stats'
const props = defineProps<{ rows: Row[]; xCol: string; yCol: string; colorCol?: string | null }>()
const PAL = ['var(--c0)', 'var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)', 'var(--c5)']
const W = 560, H = 360, m = { t: 14, r: 16, b: 44, l: 56 }
const iw = W - m.l - m.r, ih = H - m.t - m.b
const pts = computed(() =>
  props.rows
    .map((r) => ({ x: Number(r[props.xCol]), y: Number(r[props.yCol]), c: props.colorCol ? String(r[props.colorCol]) : null }))
    .filter((p) => !Number.isNaN(p.x) && !Number.isNaN(p.y)),
)
const xExtent = computed<[number, number]>(() => [Math.min(...pts.value.map((p) => p.x)), Math.max(...pts.value.map((p) => p.x))])
const yExtent = computed<[number, number]>(() => [Math.min(...pts.value.map((p) => p.y)), Math.max(...pts.value.map((p) => p.y))])
const x = (v: number) => ((v - xExtent.value[0]) / ((xExtent.value[1] - xExtent.value[0]) || 1)) * iw
const y = (v: number) => ih - ((v - yExtent.value[0]) / ((yExtent.value[1] - yExtent.value[0]) || 1)) * ih
const { t } = useI18n()
const cats = computed(() => (props.colorCol ? Array.from(new Set(pts.value.map((p) => p.c))) : []))
const cColor = (c: string | null) => (props.colorCol ? PAL[cats.value.indexOf(c) % PAL.length] : 'var(--accent)')
const trend = computed(() => {
  const p = pts.value
  const mx = mean(p.map((d) => d.x)), my = mean(p.map((d) => d.y))
  let num = 0, den = 0
  for (const d of p) { num += (d.x - mx) * (d.y - my); den += (d.x - mx) ** 2 }
  const slope = den ? num / den : 0, intercept = my - slope * mx
  const [a, b] = xExtent.value
  return { x1: x(a), y1: y(slope * a + intercept), x2: x(b), y2: y(slope * b + intercept) }
})
const yTicks = computed(() => [0, 1, 2, 3, 4].map((i) => yExtent.value[0] + (i / 4) * (yExtent.value[1] - yExtent.value[0])))
const xTicks = computed(() => [0, 1, 2, 3, 4, 5].map((i) => xExtent.value[0] + (i / 5) * (xExtent.value[1] - xExtent.value[0])))
</script>

<template>
  <div v-if="!pts.length" class="empty">{{ t('chart.noPairs') }}</div>
  <div v-else>
    <svg width="100%" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="`${xCol} / ${yCol}`">
      <g :transform="`translate(${m.l},${m.t})`">
        <g v-for="(t, i) in yTicks" :key="i" :transform="`translate(0,${y(t)})`">
          <line :x2="iw" stroke="var(--line-soft)" />
          <text :x="-10" dy="0.32em" text-anchor="end" font-size="11" fill="var(--faint)" font-family="var(--font-mono)">{{ fmt(t, 0) }}</text>
        </g>
        <text v-for="(t, i) in xTicks" :key="'x' + i" :x="x(t)" :y="ih + 22" text-anchor="middle"
          font-size="11" fill="var(--faint)" font-family="var(--font-mono)">{{ fmt(t, 0) }}</text>
        <circle v-for="(p, i) in pts" :key="i" :cx="x(p.x)" :cy="y(p.y)" r="3.4" :fill="cColor(p.c)" opacity="0.62" />
        <line :x1="trend.x1" :y1="trend.y1" :x2="trend.x2" :y2="trend.y2" stroke="var(--ink)" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.8" />
        <text :x="iw / 2" :y="ih + 40" text-anchor="middle" font-size="12" fill="var(--muted)">{{ xCol }}</text>
      </g>
    </svg>
    <div v-if="colorCol" class="legend">
      <span v-for="c in cats.slice(0, 10)" :key="c ?? ''" class="leg">
        <span class="dot" :style="{ background: cColor(c) }" />{{ c }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.empty { display: flex; align-items: center; justify-content: center; height: 220px; color: var(--faint); font-size: 13.5px; }
.legend { display: flex; flex-wrap: wrap; gap: 12px; padding-left: 56px; margin-top: 4px; }
.leg { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); }
.dot { width: 9px; height: 9px; border-radius: 2px; }
</style>
