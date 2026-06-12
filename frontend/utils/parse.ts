import Papa from 'papaparse'
import * as XLSX from 'xlsx'
import type { Row } from '~/types'

/** Parse an uploaded CSV/TSV/Excel file into rows (client-side only). */
export function parseFile(file: File): Promise<Row[]> {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (['csv', 'tsv', 'txt'].includes(ext)) {
    return new Promise((resolve, reject) => {
      Papa.parse<Row>(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (res) => (res.data.length ? resolve(res.data) : reject(new Error('文件里没有可解析的数据行。'))),
        error: () => reject(new Error('CSV 解析失败，请检查文件格式。')),
      })
    })
  }
  if (['xlsx', 'xls'].includes(ext)) {
    return file.arrayBuffer().then((buf) => {
      const wb = XLSX.read(buf, { type: 'array' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const json = XLSX.utils.sheet_to_json<Row>(ws, { defval: null })
      if (!json.length) throw new Error('这个工作表是空的。')
      return json
    })
  }
  return Promise.reject(new Error('目前支持 CSV、TSV 和 Excel（.xlsx / .xls）。'))
}

export function exportProfileJson(fileName: string, summary: object) {
  const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${fileName.replace(/\.[^.]+$/, '')}_profile.json`
  a.click()
}
