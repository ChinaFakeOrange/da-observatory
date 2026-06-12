<script setup lang="ts">
import { makeSampleData } from '~/utils/sample'
import { buildProfile } from '~/utils/profile'
import { parseFile } from '~/utils/parse'
import { fmt } from '~/utils/stats'
import { useApi, type JobStatus, type TrainParams } from '~/composables/useApi'
import type { Row } from '~/types'
import { Upload, Play, ArrowLeft, CheckCircle2, XCircle, Loader2, Sparkles } from 'lucide-vue-next'

const { t } = useI18n()
const api = useApi()
const rows = ref<Row[]>(makeSampleData())
const profile = computed(() => buildProfile(rows.value)!)
const fileInput = ref<HTMLInputElement | null>(null)

const task = ref<'Regression' | 'Classification'>('Regression')
const target = ref<string>('总价')
const metric = ref<string>('RMSE')
const nTrials = ref<number>(5)
const metaWeight = ref<number>(0.5)
const solveCollinearity = ref<boolean>(true)
const balance = ref<boolean>(false)

const REG_METRICS = ['RMSE', 'MAE', 'MSE', 'R2']
const CLF_METRICS = ['F1', 'AUC', 'ACC']
const metrics = computed(() => (task.value === 'Regression' ? REG_METRICS : CLF_METRICS))
watch(task, () => { metric.value = metrics.value[0] })

const status = ref<JobStatus | null>(null)
const running = ref(false)
const err = ref<string | null>(null)
const modelId = ref<string | null>(null)
const datasetId = ref<string | null>(null)
const predictions = ref<{ columns: string[]; data: Row[] } | null>(null)

const targetProfile = computed(() => profile.value.profiles.find((p) => p.name === target.value))
const result = computed(() => status.value?.result as Record<string, any> | null)
// 进度文案按 status 本地化，不依赖后端的中文消息
const statusText = computed(() => (status.value ? t('status.' + status.value.status) : ''))

async function onPick(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (!f) return
  try {
    rows.value = await parseFile(f)
    target.value = profile.value.columns[profile.value.columns.length - 1]
  } catch (e2) { err.value = (e2 as Error).message }
}

async function run() {
  err.value = null; predictions.value = null; running.value = true
  status.value = { job_id: '', status: 'queued', progress: 0, message: '', model_id: null, result: null }
  try {
    const dsId = await api.uploadDataset(rows.value)
    datasetId.value = dsId
    const params: TrainParams = {
      task: task.value, target: target.value, metric: metric.value,
      drop_columns: [], n_trials: nTrials.value, meta_weight: metaWeight.value,
      test_ratio: 0.25, balance: balance.value, solve_collinearity: solveCollinearity.value, auto_feature: false,
    }
    const jobId = await api.startTraining(dsId, params)
    for (let i = 0; i < 600; i++) {
      const s = await api.pollJob(jobId)
      status.value = s
      if (s.status === 'succeeded') { modelId.value = s.model_id; break }
      if (s.status === 'failed') { err.value = s.message || t('status.failed'); break }
      await new Promise((r) => setTimeout(r, 1200))
    }
  } catch (e) {
    err.value = (e as Error)?.message ?? t('train.connectFail')
  } finally { running.value = false }
}

async function runPredict() {
  if (!modelId.value || !datasetId.value) return
  try {
    const res = await api.predict(modelId.value, datasetId.value)
    predictions.value = { columns: res.columns, data: res.data.slice(0, 30) }
  } catch (e) { err.value = (e as Error).message }
}
</script>

<template>
  <div class="shell">
    <header class="head">
      <div>
        <NuxtLink to="/" class="back"><ArrowLeft :size="14" /> {{ t('nav.back') }}</NuxtLink>
        <h1>{{ t('train.h1') }}</h1>
        <p class="sub">{{ t('train.sub') }}</p>
      </div>
      <div class="hactions">
        <LangToggle />
        <button class="btn" @click="fileInput?.click()"><Upload :size="15" /> {{ t('btn.changeData') }}</button>
        <input ref="fileInput" type="file" accept=".csv,.tsv,.txt,.xlsx,.xls" hidden @change="onPick" />
      </div>
    </header>

    <div class="grid">
      <div class="card cfg">
        <div class="cap">{{ t('train.cfg') }}</div>
        <div class="field">
          <span>{{ t('train.taskType') }}</span>
          <div class="seg">
            <button :class="{ on: task === 'Regression' }" @click="task = 'Regression'">{{ t('train.regression') }}</button>
            <button :class="{ on: task === 'Classification' }" @click="task = 'Classification'">{{ t('train.classification') }}</button>
          </div>
        </div>
        <AppSelect v-model="target" :label="t('sel.target')" :options="profile.columns" class="mb" />
        <AppSelect v-model="metric" :label="t('train.metric')" :options="metrics" class="mb" />
        <div class="field">
          <span>{{ t('train.trials') }} · <b class="mono">{{ nTrials }}</b></span>
          <input v-model.number="nTrials" type="range" min="1" max="25" />
        </div>
        <div class="field">
          <span>{{ t('train.metaWeight') }} · <b class="mono">{{ metaWeight.toFixed(2) }}</b></span>
          <input v-model.number="metaWeight" type="range" min="0" max="1" step="0.05" />
        </div>
        <label class="check"><input v-model="solveCollinearity" type="checkbox" /> {{ t('train.collinearity') }}</label>
        <label class="check"><input v-model="balance" type="checkbox" /> {{ t('train.robust') }}</label>
        <button class="btn btn-primary run" :disabled="running" @click="run">
          <Loader2 v-if="running" :size="16" class="spin" /><Play v-else :size="16" />
          {{ running ? t('train.running') : t('train.start') }}
        </button>
        <p class="note">{{ t('train.targetNote', { target, type: targetProfile?.type === 'numeric' ? t('type.numeric') : t('type.categorical') }) }}</p>
      </div>

      <div class="result">
        <div v-if="err" class="alert"><XCircle :size="16" /> {{ err }}</div>

        <div v-if="status && status.status !== 'succeeded' && !err" class="card prog">
          <Loader2 :size="18" class="spin" />
          <div>
            <div class="pmsg">{{ statusText }}</div>
            <div class="pbar"><div class="pfill" :style="{ width: (status.progress * 100) + '%' }" /></div>
          </div>
        </div>

        <div v-if="status?.status === 'succeeded' && result" class="card">
          <div class="rhead"><CheckCircle2 :size="18" color="var(--accent)" /> {{ t('train.done') }} · {{ t('train.modelLabel') }} <span class="mono">{{ modelId }}</span></div>

          <div class="metrics">
            <template v-if="result.task === 'Regression'">
              <div class="m"><span>{{ t('m.testR2') }}</span><b class="mono">{{ fmt(result.metrics.test_r2, 3) }}</b></div>
              <div class="m"><span>{{ t('m.rmse') }}</span><b class="mono">{{ fmt(result.metrics.test_rmse) }}</b></div>
              <div class="m"><span>{{ t('m.mae') }}</span><b class="mono">{{ fmt(result.metrics.test_mae) }}</b></div>
              <div class="m"><span>{{ t('m.trainR2') }}</span><b class="mono">{{ fmt(result.metrics.train_r2, 3) }}</b></div>
            </template>
            <template v-else>
              <div class="m"><span>{{ t('m.testAcc') }}</span><b class="mono">{{ fmt(result.metrics.test_accuracy, 3) }}</b></div>
              <div class="m"><span>{{ t('m.macroF1') }}</span><b class="mono">{{ fmt(result.metrics.macro_f1, 3) }}</b></div>
              <div class="m"><span>{{ t('m.trainAcc') }}</span><b class="mono">{{ fmt(result.metrics.train_accuracy, 3) }}</b></div>
            </template>
          </div>

          <RegressionScatter v-if="result.task === 'Regression' && result.scatter" :points="result.scatter" />
          <RocCurves v-else-if="result.task === 'Classification' && result.roc" :curves="result.roc" />

          <button class="btn run2" @click="runPredict"><Sparkles :size="15" /> {{ t('train.predictNow') }}</button>
        </div>

        <div v-if="predictions" class="card">
          <div class="cap">{{ t('train.predTitle') }}</div>
          <DataTable :rows="predictions.data" :columns="predictions.columns" :limit="30" />
        </div>

        <div v-if="!status && !err" class="placeholder">
          <Play :size="22" color="var(--faint)" />
          <p>{{ t('train.placeholder') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 26px; flex-wrap: wrap; }
.hactions { display: flex; gap: 10px; align-items: center; }
.back { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--muted); margin-bottom: 8px; }
h1 { margin: 0; font-family: var(--font-display); font-weight: 700; font-size: 28px; letter-spacing: -0.02em; }
.sub { margin: 5px 0 0; color: var(--muted); font-size: 13.5px; }
.grid { display: grid; grid-template-columns: 300px 1fr; gap: 22px; align-items: start; }
.cap { font-size: 12px; color: var(--faint); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 16px; }
.field { margin-bottom: 16px; font-size: 12px; color: var(--faint); font-weight: 600; }
.field > span { display: block; margin-bottom: 7px; }
.field b { color: var(--accent-deep); }
.seg { display: flex; gap: 0; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.seg button { flex: 1; padding: 8px; background: var(--surface); border: none; font-size: 13px; color: var(--muted); font-weight: 500; }
.seg button.on { background: var(--accent); color: #fff; font-weight: 600; }
input[type=range] { width: 100%; accent-color: var(--accent); }
.mb { margin-bottom: 16px; }
.check { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--ink); margin-bottom: 12px; }
.check input { accent-color: var(--accent); }
.run { width: 100%; justify-content: center; margin-top: 8px; }
.run2 { margin-top: 18px; }
.note { font-size: 12px; color: var(--faint); margin: 12px 0 0; }
.alert { display: flex; align-items: center; gap: 8px; padding: 12px 14px; background: var(--warn-soft); border: 1px solid #f0cbb3; border-radius: 9px; color: var(--warn); font-size: 13.5px; margin-bottom: 16px; }
.prog { display: flex; align-items: center; gap: 14px; }
.pmsg { font-size: 14px; font-weight: 500; margin-bottom: 8px; }
.pbar { height: 7px; width: 280px; max-width: 60vw; background: var(--line-soft); border-radius: 4px; overflow: hidden; }
.pfill { height: 100%; background: var(--accent); transition: width 0.4s; }
.rhead { display: flex; align-items: center; gap: 9px; font-size: 15px; font-weight: 600; margin-bottom: 18px; }
.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 12px; margin-bottom: 22px; }
.m { background: var(--surface-2); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
.m span { display: block; font-size: 12px; color: var(--faint); margin-bottom: 5px; }
.m b { font-size: 20px; }
.mono { font-family: var(--font-mono); }
.placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; height: 320px; color: var(--faint); text-align: center; font-size: 14px; line-height: 1.6; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 880px) { .grid { grid-template-columns: 1fr; } }
</style>
