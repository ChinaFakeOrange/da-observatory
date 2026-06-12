<script setup lang="ts">
const props = defineProps<{ cols: string[]; corr: Record<string, Record<string, number>> }>()
const { t } = useI18n()
const cell = computed(() => Math.min(64, Math.floor(440 / Math.max(props.cols.length, 1))))
const labelPad = 92, top = 16
const size = computed(() => props.cols.length * cell.value)
const W = computed(() => size.value + labelPad + 20)
const H = computed(() => size.value + labelPad + top)
// teal sequential ramp
function ramp(t: number): string {
  const stops = [[243, 248, 247], [191, 224, 219], [95, 175, 166], [15, 118, 110], [11, 75, 71]]
  const x = Math.max(0, Math.min(1, t)) * (stops.length - 1)
  const i = Math.floor(x), f = x - i
  const a = stops[i], b = stops[Math.min(i + 1, stops.length - 1)]
  const c = a.map((v, k) => Math.round(v + (b[k] - v) * f))
  return `rgb(${c[0]},${c[1]},${c[2]})`
}
const color = (v: number) => (Number.isNaN(v) ? '#f2f4f6' : ramp((v + 1) / 2))
const cells = computed(() => {
  const out: { i: number; j: number; v: number; rc: string; cc: string }[] = []
  props.cols.forEach((rc, i) =>
    props.cols.forEach((cc, j) => { if (j <= i) out.push({ i, j, v: props.corr[rc][cc], rc, cc }) }),
  )
  return out
})
</script>

<template>
  <div v-if="cols.length < 2" class="empty">{{ t('chart.needTwoNumeric') }}</div>
  <svg v-else width="100%" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="t('panel.corr.t')">
    <g :transform="`translate(${labelPad},${top})`">
      <text v-for="(c, j) in cols" :key="'x' + c"
        :transform="`translate(${j * cell + cell / 2},${size + 14}) rotate(-35)`"
        text-anchor="end" font-size="11.5" fill="var(--muted)">{{ c }}</text>
      <text v-for="(c, i) in cols" :key="'y' + c" :x="-10" :y="i * cell + cell / 2" dy="0.32em"
        text-anchor="end" font-size="11.5" fill="var(--muted)">{{ c }}</text>
      <g v-for="(d, k) in cells" :key="k" :transform="`translate(${d.j * cell},${d.i * cell})`">
        <rect :width="cell - 2" :height="cell - 2" rx="3" :fill="color(d.v)">
          <title>{{ `${d.rc} × ${d.cc}: ${Number.isNaN(d.v) ? '—' : d.v.toFixed(2)}` }}</title>
        </rect>
        <text v-if="cell > 30" :x="(cell - 2) / 2" :y="(cell - 2) / 2" dy="0.32em" text-anchor="middle"
          font-size="10.5" font-family="var(--font-mono)"
          :fill="(d.v + 1) / 2 > 0.62 ? '#eaf4f2' : 'var(--muted)'">{{ Number.isNaN(d.v) ? '' : d.v.toFixed(2) }}</text>
      </g>
    </g>
  </svg>
</template>

<style scoped>
.empty { display: flex; align-items: center; justify-content: center; height: 220px; color: var(--faint); font-size: 13.5px; }
</style>
