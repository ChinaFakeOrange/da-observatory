<script setup lang="ts">
import type { ColumnProfile } from '~/types'
import { fmt } from '~/utils/stats'
const props = defineProps<{ profile: ColumnProfile }>()
const { t } = useI18n()
const W = 560, H = 280, m = { t: 16, r: 16, b: 40, l: 48 }
const iw = W - m.l - m.r, ih = H - m.t - m.b
const min = computed(() => props.profile.min ?? 0)
const max = computed(() => props.profile.max ?? 1)
const maxN = computed(() => Math.max(...(props.profile.bins ?? []).map((b) => b.n), 1))
const x = (v: number) => ((v - min.value) / (max.value - min.value || 1)) * iw
const y = (n: number) => ih - (n / maxN.value) * ih
const yTicks = computed(() => { const step = maxN.value / 4; return [0, 1, 2, 3, 4].map((i) => Math.round(i * step)) })
const xTicks = computed(() => [0, 1, 2, 3, 4, 5].map((i) => min.value + (i / 5) * (max.value - min.value)))
</script>

<template>
  <svg width="100%" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="t('aria.histogram', { name: profile.name })">
    <g :transform="`translate(${m.l},${m.t})`">
      <g v-for="t in yTicks" :key="t" :transform="`translate(0,${y(t)})`">
        <line :x2="iw" stroke="var(--line-soft)" />
        <text :x="-10" dy="0.32em" text-anchor="end" font-size="11" fill="var(--faint)" font-family="var(--font-mono)">{{ t }}</text>
      </g>
      <rect v-for="(b, i) in profile.bins" :key="i" :x="x(b.x0)" :y="y(b.n)"
        :width="Math.max(1, x(b.x1) - x(b.x0) - 1.5)" :height="ih - y(b.n)" rx="1.5" fill="var(--accent)" opacity="0.9">
        <title>{{ `[${fmt(b.x0)}, ${fmt(b.x1)})  n=${b.n}` }}</title>
      </rect>
      <text v-for="(t, i) in xTicks" :key="i" :x="x(t)" :y="ih + 24" text-anchor="middle" font-size="11"
        fill="var(--faint)" font-family="var(--font-mono)">{{ fmt(t, 0) }}</text>
      <line :y2="ih" stroke="var(--line)" />
      <line :x1="0" :x2="iw" :y1="ih" :y2="ih" stroke="var(--line)" />
    </g>
  </svg>
</template>
