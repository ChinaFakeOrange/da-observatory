// 轻量 i18n：无第三方依赖，SSR 安全（cookie + useState），支持 {param} 插值。
// 只翻译界面文案；用户数据（列名、类别值）不翻译。
export type Locale = 'zh' | 'en'

type Dict = Record<string, string>

const zh: Dict = {
  // —— 品牌 / 头部 ——
  'app.h1': '数据探索工作台',
  'app.sub': '上传数据，即刻得到逐列画像与可视化分析 · 全程在本地浏览器完成',
  'nav.mlTrain': 'ML 训练',
  'nav.back': '返回工作台',
  'btn.export': '导出画像',
  'btn.upload': '上传数据',
  'btn.changeData': '换数据',
  'file.sampleName': '二手房样本数据.csv',
  'file.shape': '{n} 行 × {m} 列',
  'file.dropHint': '把 CSV / Excel 拖到这里即可替换',
  'file.noBackendNote': '前端自带样本数据，未连后端也能体验 EDA；训练台需要后端在线。',

  // —— KPI ——
  'kpi.rows': '数据行数',
  'kpi.cols': '字段总数',
  'kpi.numeric': '数值列',
  'kpi.categorical': '类别列',
  'kpi.missing': '缺失占比',
  'kpi.duplicates': '重复行',

  // —— Tab ——
  'tab.overview': '总览',
  'tab.distribution': '分布',
  'tab.relationship': '关系',
  'tab.quality': '数据质量',
  'tab.table': '数据表',

  // —— 面板标题/副标题 ——
  'panel.profile.t': '逐列画像',
  'panel.profile.s': '每一列的类型、缺失、唯一值与分布形态——数据的指纹',
  'panel.dist.t': '分布分析',
  'panel.dist.s': '选择字段，查看其分布与统计概要',
  'panel.corr.t': '相关性热力图',
  'panel.corr.s': '数值列之间的皮尔逊相关系数（下三角）',
  'panel.drivers.t': '目标驱动因素',
  'panel.drivers.s': '选定目标，按相关性强度排序的影响变量',
  'panel.scatter.t': '散点关系',
  'panel.scatter.s': '挑选两列查看关系，可按类别着色',
  'panel.box.t': '分组箱线图',
  'panel.box.s': '数值变量在不同类别下的分布对比',
  'panel.matrix.t': '散点矩阵',
  'panel.matrix.s': '前四个数值列的两两关系一览',
  'panel.quality.t': '数据质量',
  'panel.quality.s': '缺失分布、离群点与潜在问题列',
  'panel.table.t': '数据表',
  'panel.table.s': '预览前 200 行 · 共 {n} 行',

  // —— 选择器 ——
  'sel.target': '目标列',
  'sel.x': 'X 轴',
  'sel.y': 'Y 轴',
  'sel.color': '着色',
  'sel.none': '无',
  'sel.numCol': '数值列',
  'sel.groupCol': '分组列',

  // —— 逐列画像表 ——
  'prof.field': '字段',
  'prof.type': '类型',
  'prof.missing': '缺失',
  'prof.unique': '唯一值',
  'prof.dist': '分布',
  'prof.summary': '概要',
  'type.numeric': '数值',
  'type.categorical': '类别',
  'prof.top': 'top: {v}',

  // —— 统计概要 ——
  'stat.title': '统计概要',
  'stat.count': '数量',
  'stat.missing': '缺失',
  'stat.mean': '均值',
  'stat.std': '标准差',
  'stat.min': '最小',
  'stat.q25': '25%',
  'stat.median': '中位数',
  'stat.q75': '75%',
  'stat.max': '最大',
  'stat.outliers': '离群点',
  'stat.unique': '唯一值',
  'stat.topValue': '最高频',
  'stat.topCount': '最高频次',

  // —— 图表内文案 ——
  'chart.needTwoNumeric': '需要至少两个数值列才能计算相关性',
  'chart.noPairs': '选中的两列没有可配对的数值',
  'chart.predVsActual': '预测值 vs 实际值（对角线为理想拟合）',
  'chart.actual': '实际值',
  'chart.roc': 'ROC 曲线（每类一条，越靠左上越好）',
  'chart.fpr': '假阳率 FPR',

  // —— 质量体检 ——
  'quality.title': '体检清单',
  'quality.ok': '未发现明显的数据质量问题',
  'quality.highMissing': '「{name}」缺失 {pct}%，建议考虑剔除',
  'quality.constant': '「{name}」为常量列，对建模无信息量',
  'quality.idLike': '「{name}」疑似 ID 列（取值全不相同）',
  'quality.outliers': '「{name}」存在 {n} 个 IQR 离群点',
  'quality.duplicates': '存在 {n} 行完全重复',

  // —— 训练台 ——
  'train.h1': 'AutoML 训练台',
  'train.sub': 'XGBoost · LightGBM · HistGBM + 第四基模型，Optuna 调参后做 Stacking 融合',
  'train.cfg': '训练配置',
  'train.taskType': '任务类型',
  'train.regression': '回归',
  'train.classification': '分类',
  'train.metric': '评估指标',
  'train.trials': '调参轮数',
  'train.metaWeight': '元模型权重 α',
  'train.collinearity': '共线性处理（PCA）',
  'train.robust': '稳健缩放（抗离群）',
  'train.start': '开始训练',
  'train.running': '训练中…',
  'train.targetNote': '目标列「{target}」当前类型：{type}',
  'train.placeholder': '配置好左侧参数后点击「开始训练」，后端将完成调参、融合并回传指标与图表',
  'train.connectFail': '无法连接后端，请确认 API 服务已启动。',

  // 状态（按 status 本地化，避免依赖后端中文消息）
  'status.queued': '排队中',
  'status.running': '调参与训练中…',
  'status.succeeded': '完成',
  'status.failed': '失败',

  'train.done': '训练完成',
  'train.modelLabel': '模型',
  'm.testR2': '测试 R²',
  'm.rmse': 'RMSE',
  'm.mae': 'MAE',
  'm.trainR2': '训练 R²',
  'm.testAcc': '测试准确率',
  'm.macroF1': 'Macro F1',
  'm.trainAcc': '训练准确率',
  'train.predictNow': '用该模型预测当前数据',
  'train.predTitle': '预测结果（前 30 行）',

  // —— 无障碍 aria-label（屏幕阅读器用）——
  'aria.boxplot': '{value} 按 {group} 分组的箱线图',
  'aria.categoryCount': '{name} 类别计数',
  'aria.histogram': '{name} 直方图',
  'aria.missing': '缺失值占比',
  'aria.scatterMatrix': '散点矩阵',
}

const en: Dict = {
  'app.h1': 'Data Exploration Workbench',
  'app.sub': 'Upload data for instant per-column profiling and visual analysis · all in your browser',
  'nav.mlTrain': 'ML Training',
  'nav.back': 'Back to workbench',
  'btn.export': 'Export profile',
  'btn.upload': 'Upload data',
  'btn.changeData': 'Change data',
  'file.sampleName': 'sample_housing.csv',
  'file.shape': '{n} rows × {m} cols',
  'file.dropHint': 'Drag a CSV / Excel file here to replace',
  'file.noBackendNote': 'A sample dataset is bundled — EDA works without a backend; the training studio needs the backend online.',

  'kpi.rows': 'Rows',
  'kpi.cols': 'Columns',
  'kpi.numeric': 'Numeric',
  'kpi.categorical': 'Categorical',
  'kpi.missing': 'Missing %',
  'kpi.duplicates': 'Duplicates',

  'tab.overview': 'Overview',
  'tab.distribution': 'Distribution',
  'tab.relationship': 'Relationships',
  'tab.quality': 'Data quality',
  'tab.table': 'Data table',

  'panel.profile.t': 'Column profiles',
  'panel.profile.s': 'Type, missingness, unique values and shape for every column — the data fingerprint',
  'panel.dist.t': 'Distribution analysis',
  'panel.dist.s': 'Pick a column to inspect its distribution and summary stats',
  'panel.corr.t': 'Correlation heatmap',
  'panel.corr.s': 'Pearson correlation between numeric columns (lower triangle)',
  'panel.drivers.t': 'Target drivers',
  'panel.drivers.s': 'Pick a target; variables ranked by correlation strength',
  'panel.scatter.t': 'Scatter relationship',
  'panel.scatter.s': 'Pick two columns; color by a category',
  'panel.box.t': 'Grouped box plot',
  'panel.box.s': 'Distribution of a numeric variable across categories',
  'panel.matrix.t': 'Scatter matrix',
  'panel.matrix.s': 'Pairwise relationships among the first four numeric columns',
  'panel.quality.t': 'Data quality',
  'panel.quality.s': 'Missingness, outliers and potentially problematic columns',
  'panel.table.t': 'Data table',
  'panel.table.s': 'Previewing the first 200 of {n} rows',

  'sel.target': 'Target',
  'sel.x': 'X axis',
  'sel.y': 'Y axis',
  'sel.color': 'Color by',
  'sel.none': 'None',
  'sel.numCol': 'Numeric',
  'sel.groupCol': 'Group by',

  'prof.field': 'Field',
  'prof.type': 'Type',
  'prof.missing': 'Missing',
  'prof.unique': 'Unique',
  'prof.dist': 'Distribution',
  'prof.summary': 'Summary',
  'type.numeric': 'numeric',
  'type.categorical': 'categorical',
  'prof.top': 'top: {v}',

  'stat.title': 'Summary statistics',
  'stat.count': 'Count',
  'stat.missing': 'Missing',
  'stat.mean': 'Mean',
  'stat.std': 'Std',
  'stat.min': 'Min',
  'stat.q25': '25%',
  'stat.median': 'Median',
  'stat.q75': '75%',
  'stat.max': 'Max',
  'stat.outliers': 'Outliers',
  'stat.unique': 'Unique',
  'stat.topValue': 'Top value',
  'stat.topCount': 'Top count',

  'chart.needTwoNumeric': 'At least two numeric columns are needed to compute correlation',
  'chart.noPairs': 'The two selected columns have no pairable numbers',
  'chart.predVsActual': 'Predicted vs actual (diagonal = perfect fit)',
  'chart.actual': 'Actual',
  'chart.roc': 'ROC curves (one per class; closer to top-left is better)',
  'chart.fpr': 'False positive rate (FPR)',

  'quality.title': 'Checklist',
  'quality.ok': 'No obvious data-quality issues found',
  'quality.highMissing': '"{name}" is {pct}% missing — consider dropping it',
  'quality.constant': '"{name}" is constant — no signal for modeling',
  'quality.idLike': '"{name}" looks like an ID column (all values distinct)',
  'quality.outliers': '"{name}" has {n} IQR outliers',
  'quality.duplicates': '{n} fully duplicated rows',

  'train.h1': 'AutoML Studio',
  'train.sub': 'XGBoost · LightGBM · HistGBM + a 4th base model; Optuna tuning then stacking',
  'train.cfg': 'Training config',
  'train.taskType': 'Task type',
  'train.regression': 'Regression',
  'train.classification': 'Classification',
  'train.metric': 'Metric',
  'train.trials': 'Tuning trials',
  'train.metaWeight': 'Meta weight α',
  'train.collinearity': 'Collinearity handling (PCA)',
  'train.robust': 'Robust scaling (outlier-resistant)',
  'train.start': 'Start training',
  'train.running': 'Training…',
  'train.targetNote': 'Target "{target}" current type: {type}',
  'train.placeholder': 'Configure the options on the left and click "Start training"; the backend tunes, blends and returns metrics & charts',
  'train.connectFail': 'Cannot reach the backend — make sure the API service is running.',

  'status.queued': 'Queued',
  'status.running': 'Tuning & training…',
  'status.succeeded': 'Done',
  'status.failed': 'Failed',

  'train.done': 'Training complete',
  'train.modelLabel': 'model',
  'm.testR2': 'Test R²',
  'm.rmse': 'RMSE',
  'm.mae': 'MAE',
  'm.trainR2': 'Train R²',
  'm.testAcc': 'Test accuracy',
  'm.macroF1': 'Macro F1',
  'm.trainAcc': 'Train accuracy',
  'train.predictNow': 'Predict current data with this model',
  'train.predTitle': 'Predictions (first 30 rows)',

  'aria.boxplot': '{value} box plot grouped by {group}',
  'aria.categoryCount': '{name} category counts',
  'aria.histogram': '{name} histogram',
  'aria.missing': 'Missing value ratio',
  'aria.scatterMatrix': 'Scatter matrix',
}

const messages: Record<Locale, Dict> = { zh, en }

export function useLocale() {
  const cookie = useCookie<Locale>('dao_locale', {
    default: () => 'zh',
    maxAge: 60 * 60 * 24 * 365,
    sameSite: 'lax',
  })
  const locale = useState<Locale>('dao_locale', () => cookie.value)
  function setLocale(l: Locale) {
    locale.value = l
    cookie.value = l
  }
  return { locale, setLocale }
}

export function useI18n() {
  const { locale, setLocale } = useLocale()
  function t(key: string, params?: Record<string, string | number>): string {
    let s = messages[locale.value][key] ?? messages.zh[key] ?? key
    if (params) for (const k in params) s = s.replaceAll(`{${k}}`, String(params[k]))
    return s
  }
  return { locale, setLocale, t }
}
