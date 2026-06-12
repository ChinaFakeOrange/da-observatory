<script setup lang="ts">
import type { DatasetProfile } from '~/types'
import { pct } from '~/utils/stats'
import { Database, Layers, Hash, Type, AlertTriangle, Copy } from 'lucide-vue-next'
const props = defineProps<{ stats: DatasetProfile['stats'] }>()
const { t } = useI18n()
const items = computed(() => [
  { label: t('kpi.rows'), value: props.stats.nRows.toLocaleString(), icon: Database, warn: false },
  { label: t('kpi.cols'), value: props.stats.nCols, icon: Layers, warn: false },
  { label: t('kpi.numeric'), value: props.stats.nNumeric, icon: Hash, warn: false },
  { label: t('kpi.categorical'), value: props.stats.nCategorical, icon: Type, warn: false },
  { label: t('kpi.missing'), value: pct(props.stats.missingPct), icon: AlertTriangle, warn: props.stats.missingPct > 0.05 },
  { label: t('kpi.duplicates'), value: props.stats.duplicates, icon: Copy, warn: props.stats.duplicates > 0 },
])
</script>

<template>
  <div class="kpis">
    <div v-for="k in items" :key="k.label" class="kpi">
      <div class="lbl"><component :is="k.icon" :size="13" />{{ k.label }}</div>
      <div class="val" :style="{ color: k.warn ? 'var(--warn)' : 'var(--ink)' }">{{ k.value }}</div>
    </div>
  </div>
</template>

<style scoped>
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.kpi { background: var(--surface); border: 1px solid var(--line); border-radius: 11px; padding: 14px 16px; }
.lbl { display: flex; align-items: center; gap: 6px; color: var(--faint); font-size: 12px; margin-bottom: 7px; }
.val { font-family: var(--font-mono); font-weight: 700; font-size: 24px; }
</style>
