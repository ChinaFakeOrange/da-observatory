<script setup lang="ts">
interface Curve { label: string; auc: number; points: { fpr: number; tpr: number }[] }
const props = defineProps<{ curves: Curve[] }>()
const PAL = ['var(--c0)', 'var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)', 'var(--c5)']
const W = 520, H = 380, m = { t: 16, r: 16, b: 44, l: 48 }
const iw = W - m.l - m.r, ih = H - m.t - m.b
const path = (c: Curve) =>
  c.points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.fpr * iw} ${ih - p.tpr * ih}`).join(' ')
const ticks = [0, 0.25, 0.5, 0.75, 1]
const { t } = useI18n()
</script>

<template>
  <div>
    <div class="cap">{{ t('chart.roc') }}</div>
    <svg width="100%" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="t('chart.roc')">
      <g :transform="`translate(${m.l},${m.t})`">
        <g v-for="t in ticks" :key="'y' + t" :transform="`translate(0,${ih - t * ih})`">
          <line :x2="iw" stroke="var(--line-soft)" />
          <text :x="-10" dy="0.32em" text-anchor="end" font-size="10.5" fill="var(--faint)" font-family="var(--font-mono)">{{ t }}</text>
        </g>
        <text v-for="t in ticks" :key="'x' + t" :x="t * iw" :y="ih + 20" text-anchor="middle" font-size="10.5" fill="var(--faint)" font-family="var(--font-mono)">{{ t }}</text>
        <line :x1="0" :y1="ih" :x2="iw" :y2="0" stroke="var(--faint)" stroke-dasharray="4 4" opacity="0.5" />
        <path v-for="(c, i) in curves" :key="c.label" :d="path(c)" fill="none" :stroke="PAL[i % PAL.length]" stroke-width="2" />
        <text :x="iw / 2" :y="ih + 38" text-anchor="middle" font-size="12" fill="var(--muted)">{{ t('chart.fpr') }}</text>
      </g>
    </svg>
    <div class="legend">
      <span v-for="(c, i) in curves" :key="c.label" class="leg">
        <span class="dot" :style="{ background: PAL[i % PAL.length] }" />{{ c.label }} · AUC {{ c.auc.toFixed(2) }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.cap { font-size: 12px; color: var(--faint); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }
.legend { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px; }
.leg { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); font-family: var(--font-mono); }
.dot { width: 9px; height: 9px; border-radius: 2px; }
</style>
