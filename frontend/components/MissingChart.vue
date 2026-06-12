<script setup lang="ts">
import type { ColumnProfile } from '~/types'
import { pct } from '~/utils/stats'
const props = defineProps<{ profiles: ColumnProfile[] }>()
const { t } = useI18n()
const data = computed(() => props.profiles.map((p) => ({ name: p.name, pct: p.missingPct })).sort((a, b) => b.pct - a.pct))
const W = 560, rowH = 30, mL = 96, mR = 56
const H = computed(() => data.value.length * rowH + 12)
const maxP = computed(() => Math.max(0.001, ...data.value.map((d) => d.pct)))
const bw = (p: number) => (p > 0 ? Math.max(2, (p / maxP.value) * (W - mL - mR)) : 0)
const fill = (p: number) => (p > 0.3 ? 'var(--warn)' : p > 0 ? '#d98a4e' : 'var(--accent)')
</script>

<template>
  <svg width="100%" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="t('aria.missing')">
    <g v-for="(d, i) in data" :key="d.name" :transform="`translate(0,${i * rowH + 8})`">
      <text :x="mL - 12" :y="rowH / 2" dy="0.32em" text-anchor="end" font-size="12.5" fill="var(--ink)">{{ d.name }}</text>
      <rect :x="mL" y="5" :width="W - mL - mR" :height="rowH - 14" rx="3" fill="var(--line-soft)" />
      <rect :x="mL" y="5" :width="bw(d.pct)" :height="rowH - 14" rx="3" :fill="fill(d.pct)" opacity="0.9" />
      <text :x="mL + (W - mL - mR) + 8" :y="rowH / 2" dy="0.32em" font-size="11.5" fill="var(--muted)" font-family="var(--font-mono)">{{ pct(d.pct) }}</text>
    </g>
  </svg>
</template>
