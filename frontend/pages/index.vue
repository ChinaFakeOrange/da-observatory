<script setup lang="ts">
import { makeSampleData } from '~/utils/sample'
import { buildProfile, qualityFlags, targetCorrelations } from '~/utils/profile'
import { parseFile, exportProfileJson } from '~/utils/parse'
import { fmt, pct } from '~/utils/stats'
import type { Row } from '~/types'
import {
  Upload, Download, Layers, AlertTriangle, X,
  BarChart3, GitCompareArrows, ShieldCheck, Table2, Database,
} from 'lucide-vue-next'

const { t } = useI18n()
const rows = ref<Row[]>(makeSampleData())
const fileName = ref<string | null>(null)   // null = 用样本，显示本地化样本名
const tab = ref<'overview' | 'distribution' | 'relationship' | 'quality' | 'table'>('overview')
const activeCol = ref<string | null>(null)
const err = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const displayName = computed(() => fileName.value ?? t('file.sampleName'))
const profile = computed(() => buildProfile(rows.value)!)
const numericCols = computed(() => profile.value.numericCols)
const catCols = computed(() => profile.value.categoricalCols)
const activeProfile = computed(() => profile.value.profiles.find((p) => p.name === activeCol.value) ?? profile.value.profiles[0])

const xCol = ref(''); const yCol = ref(''); const colorCol = ref('')
const boxVal = ref(''); const boxGroup = ref(''); const driverTarget = ref('')

watchEffect(() => {
  const p = profile.value
  if (!p) return
  if (!activeCol.value || !p.columns.includes(activeCol.value)) activeCol.value = p.columns[0]
  if (!numericCols.value.includes(xCol.value)) xCol.value = numericCols.value[0] ?? ''
  if (!numericCols.value.includes(yCol.value)) yCol.value = numericCols.value[1] ?? numericCols.value[0] ?? ''
  if (colorCol.value && !catCols.value.includes(colorCol.value)) colorCol.value = ''
  if (!numericCols.value.includes(boxVal.value)) boxVal.value = numericCols.value[numericCols.value.length - 1] ?? ''
  if (!catCols.value.includes(boxGroup.value)) boxGroup.value = catCols.value[0] ?? ''
  if (!numericCols.value.includes(driverTarget.value)) driverTarget.value = numericCols.value[numericCols.value.length - 1] ?? ''
})

const drivers = computed(() => targetCorrelations(profile.value, driverTarget.value))
const flags = computed(() => qualityFlags(profile.value))

const TABS = computed(() => [
  { id: 'overview', label: t('tab.overview'), icon: Database },
  { id: 'distribution', label: t('tab.distribution'), icon: BarChart3 },
  { id: 'relationship', label: t('tab.relationship'), icon: GitCompareArrows },
  { id: 'quality', label: t('tab.quality'), icon: ShieldCheck },
  { id: 'table', label: t('tab.table'), icon: Table2 },
] as const)

async function handleFile(file: File) {
  err.value = null
  try {
    rows.value = await parseFile(file)
    fileName.value = file.name
  } catch (e) { err.value = (e as Error).message }
}
function onPick(e: Event) { const f = (e.target as HTMLInputElement).files?.[0]; if (f) handleFile(f) }
function onDrop(e: DragEvent) { e.preventDefault(); const f = e.dataTransfer?.files?.[0]; if (f) handleFile(f) }
function doExport() {
  exportProfileJson(displayName.value, {
    file: displayName.value, ...profile.value.stats,
    columns: profile.value.profiles.map((p) => ({
      name: p.name, type: p.type, missing: p.missing, missingPct: p.missingPct, unique: p.unique,
      ...(p.type === 'numeric'
        ? { min: p.min, max: p.max, mean: p.mean, std: p.std, median: p.median, outliers: p.outliers }
        : { topCategories: p.top?.slice(0, 5) }),
    })),
  })
}
function summary(p: typeof profile.value.profiles[number]) {
  if (p.type === 'numeric')
    return [[t('stat.count'), p.count], [t('stat.missing'), `${p.missing} (${pct(p.missingPct)})`],
      [t('stat.mean'), fmt(p.mean)], [t('stat.std'), fmt(p.std)], [t('stat.min'), fmt(p.min)],
      [t('stat.q25'), fmt(p.q25)], [t('stat.median'), fmt(p.median)], [t('stat.q75'), fmt(p.q75)],
      [t('stat.max'), fmt(p.max)], [t('stat.outliers'), p.outliers]]
  return [[t('stat.count'), p.count], [t('stat.missing'), `${p.missing} (${pct(p.missingPct)})`],
    [t('stat.unique'), p.unique], [t('stat.topValue'), p.top?.[0]?.k ?? '—'], [t('stat.topCount'), p.top?.[0]?.n ?? '—']]
}
</script>

<template>
  <div class="shell">
    <header class="head">
      <div>
        <div class="eyebrow"><Layers :size="15" /> Data Observatory</div>
        <h1>{{ t('app.h1') }}</h1>
        <p class="sub">{{ t('app.sub') }}</p>
      </div>
      <div class="actions">
        <LangToggle />
        <NuxtLink to="/train" class="btn"><BarChart3 :size="15" /> {{ t('nav.mlTrain') }}</NuxtLink>
        <button class="btn" @click="doExport"><Download :size="15" /> {{ t('btn.export') }}</button>
        <button class="btn btn-primary" @click="fileInput?.click()"><Upload :size="15" /> {{ t('btn.upload') }}</button>
        <input ref="fileInput" type="file" accept=".csv,.tsv,.txt,.xlsx,.xls" hidden @change="onPick" />
      </div>
    </header>

    <div v-if="err" class="alert">
      <span><AlertTriangle :size="16" /> {{ err }}</span>
      <button class="x" @click="err = null"><X :size="16" /></button>
    </div>

    <div class="filebar" @drop="onDrop" @dragover.prevent>
      <Database :size="16" color="var(--accent)" />
      <span class="fn">{{ displayName }}</span>
      <span class="shape mono">{{ t('file.shape', { n: profile.stats.nRows.toLocaleString(), m: profile.stats.nCols }) }}</span>
      <span class="hint">{{ t('file.dropHint') }}</span>
    </div>

    <KpiStrip :stats="profile.stats" class="kpi-block" />

    <div class="tabs">
      <button v-for="tb in TABS" :key="tb.id" class="tab" :class="{ on: tab === tb.id }" @click="tab = tb.id">
        <component :is="tb.icon" :size="15" />{{ tb.label }}
      </button>
    </div>

    <section v-if="tab === 'overview'">
      <PanelHead :title="t('panel.profile.t')" :subtitle="t('panel.profile.s')" />
      <ColumnProfiler :profiles="profile.profiles" @select="(c) => { activeCol = c; tab = 'distribution' }" />
    </section>

    <section v-else-if="tab === 'distribution'">
      <PanelHead :title="t('panel.dist.t')" :subtitle="t('panel.dist.s')" />
      <div class="chips">
        <button v-for="c in profile.columns" :key="c" class="pchip" :class="{ on: activeCol === c }" @click="activeCol = c">{{ c }}</button>
      </div>
      <div class="grid-side">
        <div class="card">
          <HistogramChart v-if="activeProfile.type === 'numeric'" :profile="activeProfile" />
          <CategoryBars v-else :profile="activeProfile" />
        </div>
        <div class="card">
          <div class="cap">{{ t('stat.title') }}</div>
          <div v-for="([k, v]) in summary(activeProfile)" :key="k" class="srow">
            <span class="muted">{{ k }}</span><span class="mono">{{ v }}</span>
          </div>
        </div>
      </div>
    </section>

    <section v-else-if="tab === 'relationship'">
      <div class="grid-2">
        <div>
          <PanelHead :title="t('panel.corr.t')" :subtitle="t('panel.corr.s')" />
          <div class="card"><CorrHeatmap :cols="numericCols" :corr="profile.corr" /></div>
        </div>
        <div>
          <PanelHead :title="t('panel.drivers.t')" :subtitle="t('panel.drivers.s')" />
          <div class="card">
            <AppSelect v-model="driverTarget" :label="t('sel.target')" :options="numericCols" />
            <div class="drivers">
              <div v-for="d in drivers" :key="d.name" class="drow">
                <span class="dname">{{ d.name }}</span>
                <div class="dbar"><div class="dfill" :style="{ width: Math.abs(d.r) * 100 + '%', background: d.r >= 0 ? 'var(--accent)' : 'var(--warn)' }" /></div>
                <span class="mono dval" :style="{ color: d.r >= 0 ? 'var(--accent-deep)' : 'var(--warn)' }">{{ d.r.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="grid-2 mt">
        <div>
          <PanelHead :title="t('panel.scatter.t')" :subtitle="t('panel.scatter.s')" />
          <div class="card">
            <div class="ctrls">
              <AppSelect v-model="xCol" :label="t('sel.x')" :options="numericCols" />
              <AppSelect v-model="yCol" :label="t('sel.y')" :options="numericCols" />
              <AppSelect v-model="colorCol" :label="t('sel.color')" :options="['', ...catCols]" :blank-label="t('sel.none')" />
            </div>
            <ScatterPlot v-if="xCol && yCol" :rows="rows" :x-col="xCol" :y-col="yCol" :color-col="colorCol || null" />
          </div>
        </div>
        <div>
          <PanelHead :title="t('panel.box.t')" :subtitle="t('panel.box.s')" />
          <div class="card">
            <div class="ctrls">
              <AppSelect v-model="boxVal" :label="t('sel.numCol')" :options="numericCols" />
              <AppSelect v-model="boxGroup" :label="t('sel.groupCol')" :options="catCols" />
            </div>
            <BoxPlot v-if="boxVal && boxGroup" :rows="rows" :value-col="boxVal" :group-col="boxGroup" />
          </div>
        </div>
      </div>
      <div class="mt">
        <PanelHead :title="t('panel.matrix.t')" :subtitle="t('panel.matrix.s')" />
        <div class="card"><ScatterMatrix :rows="rows" :cols="numericCols" :color-col="catCols[0] ?? null" /></div>
      </div>
    </section>

    <section v-else-if="tab === 'quality'">
      <PanelHead :title="t('panel.quality.t')" :subtitle="t('panel.quality.s')" />
      <div class="grid-side">
        <div class="card"><MissingChart :profiles="profile.profiles" /></div>
        <div class="card"><QualityChecklist :flags="flags" /></div>
      </div>
    </section>

    <section v-else>
      <PanelHead :title="t('panel.table.t')" :subtitle="t('panel.table.s', { n: profile.stats.nRows.toLocaleString() })" />
      <DataTable :rows="rows" :columns="profile.columns" :limit="200" />
    </section>
  </div>
</template>

<style scoped>
.head { display: flex; align-items: flex-end; justify-content: space-between; flex-wrap: wrap; gap: 16px; margin-bottom: 22px; }
.eyebrow { display: flex; align-items: center; gap: 9px; color: var(--accent); font-size: 12.5px; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; font-family: var(--font-display); }
h1 { margin: 6px 0 0; font-family: var(--font-display); font-weight: 700; font-size: 30px; letter-spacing: -0.02em; }
.sub { margin: 5px 0 0; color: var(--muted); font-size: 14px; }
.actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.alert { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 11px 14px; margin-bottom: 16px; background: var(--warn-soft); border: 1px solid #f0cbb3; border-radius: 9px; color: var(--warn); font-size: 13.5px; }
.alert span { display: flex; align-items: center; gap: 8px; }
.alert .x { background: none; border: none; color: var(--warn); display: flex; }
.filebar { display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin-bottom: 18px; background: var(--surface); border: 1px solid var(--line); border-radius: 11px; }
.fn { font-weight: 600; font-size: 14px; }
.shape { color: var(--faint); font-size: 13px; }
.hint { margin-left: auto; color: var(--faint); font-size: 12.5px; }
.kpi-block { margin-bottom: 22px; }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--line); margin-bottom: 22px; }
.tab { display: inline-flex; align-items: center; gap: 7px; padding: 11px 15px; background: none; border: none; border-bottom: 2px solid transparent; margin-bottom: -1px; color: var(--muted); font-size: 14px; font-weight: 500; transition: color 0.15s, border-color 0.15s; }
.tab.on { color: var(--ink); font-weight: 600; border-bottom-color: var(--accent); }
.chips, .ctrls { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }
.ctrls { gap: 10px; margin-bottom: 16px; }
.pchip { padding: 6px 13px; border-radius: 8px; font-size: 13px; font-weight: 500; background: var(--surface); color: var(--muted); border: 1px solid var(--line); }
.pchip.on { background: var(--accent); color: #fff; border-color: var(--accent); font-weight: 600; }
.grid-side { display: grid; grid-template-columns: 1fr 280px; gap: 22px; align-items: start; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
.mt { margin-top: 26px; }
.cap { font-size: 12px; color: var(--faint); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }
.srow { display: flex; justify-content: space-between; padding: 7px 0; border-top: 1px solid var(--line-soft); font-size: 13px; }
.muted { color: var(--muted); } .mono { font-family: var(--font-mono); font-weight: 500; }
.drivers { margin-top: 14px; }
.drow { display: grid; grid-template-columns: 88px 1fr 44px; align-items: center; gap: 10px; padding: 6px 0; }
.dname { font-size: 13px; }
.dbar { height: 8px; background: var(--line-soft); border-radius: 4px; overflow: hidden; }
.dfill { height: 100%; border-radius: 4px; }
.dval { font-size: 12px; text-align: right; }
@media (max-width: 880px) { .grid-side, .grid-2 { grid-template-columns: 1fr; } }
</style>
