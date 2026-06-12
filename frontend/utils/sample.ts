import type { Row } from '~/types'

/** Deterministic synthetic 二手房 dataset — mixed types, real correlations, some missingness. */
export function makeSampleData(n = 260): Row[] {
  let s = 20240611
  const rnd = () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff
    return s / 0x7fffffff
  }
  const gauss = () => {
    let u = 0
    let v = 0
    while (u === 0) u = rnd()
    while (v === 0) v = rnd()
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v)
  }
  const pick = <T>(arr: T[]): T => arr[Math.floor(rnd() * arr.length)]
  const districts = ['浦东', '徐汇', '静安', '黄浦', '长宁', '杨浦', '闵行']
  const orient = ['朝南', '朝北', '南北通透', '朝东', '朝西']
  const deco = ['精装', '简装', '毛坯', '豪装']
  const base: Record<string, number> = { 浦东: 6.8, 徐汇: 9.2, 静安: 10.1, 黄浦: 9.8, 长宁: 8.4, 杨浦: 6.2, 闵行: 5.1 }
  const rows: Row[] = []
  for (let i = 0; i < n; i++) {
    const district = pick(districts)
    const area = Math.round((52 + Math.abs(gauss()) * 46) * 10) / 10
    const age = Math.max(0, Math.round(2 + Math.abs(gauss()) * 16))
    const bedrooms = Math.min(5, Math.max(1, Math.round(area / 32 + gauss() * 0.5)))
    const floor = Math.max(1, Math.round(3 + rnd() * 28))
    const o = pick(orient)
    const d = pick(deco)
    const decoBump: Record<string, number> = { 毛坯: -0.6, 简装: -0.1, 精装: 0.5, 豪装: 1.3 }
    const orientBump = o === '南北通透' ? 0.5 : o === '朝南' ? 0.3 : o === '朝北' ? -0.4 : 0
    let unit = base[district] + decoBump[d] + orientBump - age * 0.045 + gauss() * 0.55
    unit = Math.max(2.2, Math.round(unit * 100) / 100)
    const total = Math.round(unit * area * 10) / 10
    const row: Row = {
      区域: district,
      面积: area,
      房龄: age,
      卧室数: bedrooms,
      楼层: floor,
      朝向: o,
      装修: d,
      单价: unit,
      总价: total,
    }
    if (rnd() < 0.06) row.房龄 = null
    if (rnd() < 0.09) row.装修 = null
    if (rnd() < 0.03) row.楼层 = null
    rows.push(row)
  }
  return rows
}
