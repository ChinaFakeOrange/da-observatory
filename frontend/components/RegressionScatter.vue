<script setup lang="ts">
import { fmt } from '~/utils/stats'
const props = defineProps<{ points: { actual: number; pred: number }[] }>()
const W = 520, H = 360, m = { t: 16, r: 16, b: 44, l: 56 }
const iw = W - m.l - m.r, ih = H - m.t - m.b
const all = computed(() => props.points.flatMap((p) => [p.actual, p.pred]))
const lo = computed(() => Math.min(...all.value))
const hi = computed(() => Math.max(...all.value))
const sx = (v: number) => ((v - lo.value) / ((hi.value - lo.value) || 1)) * iw
const sy = (v: number) => ih - ((v - lo.value) / ((hi.value - lo.value) || 1)) * ih
const ticks = computed(() => [0, 1, 2, 3, 4].map((i) => lo.value + (i / 4) * (hi.value - lo.value)))
const { t } = useI18n()
</script>

<template>
  <div>
    <div class="cap">{{ t('chart.predVsActual') }}</div>
    <svg width="100%" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="t('chart.predVsActual')">
      <g :transform="`translate(${m.l},${m.t})`">
        <g v-for="(t, i) in ticks" :key="i" :transform="`translate(0,${sy(t)})`">
          <line :x2="iw" stroke="var(--line-soft)" />
          <text :x="-10" dy="0.32em" text-anchor="end" font-size="11" fill="var(--faint)" font-family="var(--font-mono)">{{ fmt(t, 0) }}</text>
        </g>
        <text v-for="(t, i) in ticks" :key="'x' + i" :x="sx(t)" :y="ih + 22" text-anchor="middle" font-size="11" fill="var(--faint)" font-family="var(--font-mono)">{{ fmt(t, 0) }}</text>
        <line :x1="sx(lo)" :y1="sy(lo)" :x2="sx(hi)" :y2="sy(hi)" stroke="var(--ink)" stroke-dasharray="5 4" opacity="0.6" />
        <circle v-for="(p, i) in points" :key="i" :cx="sx(p.actual)" :cy="sy(p.pred)" r="3.6" fill="var(--accent)" opacity="0.55" />
        <text :x="iw / 2" :y="ih + 40" text-anchor="middle" font-size="12" fill="var(--muted)">{{ t('chart.actual') }}</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.cap { font-size: 12px; color: var(--faint); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }
</style>
