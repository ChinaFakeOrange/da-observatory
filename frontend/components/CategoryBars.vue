<script setup lang="ts">
import type { ColumnProfile } from '~/types'
const props = defineProps<{ profile: ColumnProfile }>()
const { t } = useI18n()
const PAL = ['var(--c0)', 'var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)', 'var(--c5)']
const W = 560, rowH = 30, mL = 110, mR = 56
const top = computed(() => (props.profile.top ?? []).slice(0, 12))
const H = computed(() => top.value.length * rowH + 12)
const maxN = computed(() => Math.max(...top.value.map((d) => d.n), 1))
const bw = (n: number) => Math.max(2, (n / maxN.value) * (W - mL - mR))
</script>

<template>
  <svg width="100%" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="t('aria.categoryCount', { name: profile.name })">
    <g v-for="(d, i) in top" :key="i" :transform="`translate(0,${i * rowH + 8})`">
      <text :x="mL - 12" :y="rowH / 2" dy="0.32em" text-anchor="end" font-size="12.5" fill="var(--ink)">
        {{ d.k.length > 8 ? d.k.slice(0, 8) + '…' : d.k }}
      </text>
      <rect :x="mL" y="5" :width="bw(d.n)" :height="rowH - 14" rx="3" :fill="PAL[i % PAL.length]" opacity="0.85" />
      <text :x="mL + bw(d.n) + 8" :y="rowH / 2" dy="0.32em" font-size="11.5" fill="var(--muted)" font-family="var(--font-mono)">{{ d.n }}</text>
    </g>
  </svg>
</template>
