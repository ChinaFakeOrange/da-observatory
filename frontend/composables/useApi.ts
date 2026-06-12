import type { Row } from '~/types'

export interface JobStatus {
  job_id: string
  status: 'queued' | 'running' | 'succeeded' | 'failed'
  progress: number
  message: string
  model_id: string | null
  result: Record<string, unknown> | null
}

export interface TrainParams {
  task: 'Classification' | 'Regression'
  target: string
  metric: string
  drop_columns: string[]
  n_trials: number
  meta_weight: number
  test_ratio: number
  balance: boolean
  solve_collinearity: boolean
  auto_feature: boolean
}

/** Thin client over the FastAPI ML service. Base URL from runtime config. */
export function useApi() {
  const base = useRuntimeConfig().public.apiBase as string

  async function uploadDataset(rows: Row[]): Promise<string> {
    // serialise rows to CSV in-browser so the backend persists the exact data
    const cols = Object.keys(rows[0] ?? {})
    const csv = [cols.join(',')]
      .concat(rows.map((r) => cols.map((c) => csvCell(r[c])).join(',')))
      .join('\n')
    const form = new FormData()
    form.append('file', new Blob([csv], { type: 'text/csv' }), 'dataset.csv')
    const res = await $fetch<{ dataset_id: string }>(`${base}/datasets`, { method: 'POST', body: form })
    return res.dataset_id
  }

  async function startTraining(datasetId: string, p: TrainParams): Promise<string> {
    const res = await $fetch<{ job_id: string }>(`${base}/train`, {
      method: 'POST',
      body: { dataset_id: datasetId, ...p },
    })
    return res.job_id
  }

  function pollJob(jobId: string): Promise<JobStatus> {
    return $fetch<JobStatus>(`${base}/jobs/${jobId}`)
  }

  async function predict(modelId: string, datasetId: string) {
    return $fetch<{ rows: number; columns: string[]; data: Row[] }>(`${base}/predict`, {
      method: 'POST',
      body: { model_id: modelId, dataset_id: datasetId },
    })
  }

  return { uploadDataset, startTraining, pollJob, predict }
}

function csvCell(v: unknown): string {
  if (v === null || v === undefined) return ''
  const s = String(v)
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}
