<script setup lang="ts">
import type { ColumnProfile } from '~/types'
const props = defineProps<{ profile: ColumnProfile; w?: number; h?: number }>()
const W = props.w ?? 132
const H = props.h ?? 30
const PAL = ['var(--c0)', 'var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)', 'var(--c5)']
const numericBars = computed(() => {
  if (props.profile.type !== 'numeric' || !props.profile.bins?.length) return []
  const max = Math.max(...props.profile.bins.map((b) => b.n)) || 1
  const bw = W / props.profile.bins.length
  return props.profile.bins.map((b, i) => ({
    x: i * bw + 0.6, y: H - (b.n / max) * (H - 2), w: bw - 1.2, h: (b.n / max) * (H - 2),
  }))
})
const catBars = computed(() => {
  const top = (props.profile.top ?? []).slice(0, 5)
  const max = Math.max(...top.map((d) => d.n)) || 1
  const bw = W / 5
  return top.map((d, i) => ({
    x: i * bw + 1, y: H - (d.n / max) * (H - 2), w: bw - 2, h: (d.n / max) * (H - 2), fill: PAL[i % PAL.length],
  }))
})
</script>

<template>
  <svg :width="W" :height="H" aria-hidden="true">
    <template v-if="profile.type === 'numeric'">
      <rect v-for="(b, i) in numericBars" :key="i" :x="b.x" :y="b.y" :width="b.w" :height="b.h"
        rx="0.8" fill="var(--accent)" opacity="0.85" />
    </template>
    <template v-else>
      <rect v-for="(b, i) in catBars" :key="i" :x="b.x" :y="b.y" :width="b.w" :height="b.h"
        rx="1.2" :fill="b.fill" opacity="0.82" />
    </template>
  </svg>
</template>
