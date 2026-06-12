# Data Observatory

> 🌐 English → [README.md](./README.md) ｜ 📦 部署文档（中英）→ [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

把原先的 Streamlit「数据探索分析 / AutoML」单体工具，重做为 **Nuxt 3 前端 + FastAPI ML 后端** 的生产级双服务架构。前端负责交互与可视化，后端负责数据持久化、调参、训练与预测。

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│   Nuxt 3 (SSR) 前端       │         │      FastAPI ML 后端           │
│                          │         │                              │
│  /        EDA 工作台       │  HTTP   │  POST /datasets   上传数据      │
│  /train   AutoML 训练台    │ ──────▶ │  POST /train      投递任务到队列 │
│                          │         │  GET  /jobs/{id}  从 Redis 读状态│
│  逐列画像 / 直方图 / 箱线图  │ ◀────── │  POST /predict    模型预测      │
│  相关性 / 散点矩阵 / 质量体检 │  JSON   │  GET  /models     模型管理      │
│  图表全部前端 SVG 渲染      │  图表数据 └───────────┬──────────────────┘
└─────────────────────────┘                     │ enqueue / 读状态
                                                ▼
                                  ┌──────────────────────────────┐
                                  │   Redis  ◀──┐                 │
                                  │   队列 + 任务状态哈希            │
                                  └─────────────┼─────────────────┘
                                                │ 消费队列 / 写进度
                                  ┌─────────────▼─────────────────┐
                                  │   ARQ Worker（独立进程）         │
                                  │   调参 + Stacking 融合 + 保存模型 │
                                  └──────────────────────────────┘
```

训练放在 **独立的 ARQ worker 进程**：API 把任务投递到 Redis 队列后立即返回 `job_id`，worker 消费队列执行训练，并把阶段进度写回 Redis；前端轮询 `/jobs/{id}`，API 从同一个 Redis 哈希读状态。API 与 worker 解耦，可分别水平扩展。

设计上后端**只返回 JSON 可序列化的指标与图表数据**（ROC 点、混淆矩阵、预测对照散点），由前端用统一的 SVG 组件绘制——既保证图表风格一致，也让后端无状态、易横向扩展。

---

## 一、相比原项目修复的问题

| # | 原问题 | 位置 | 修复 |
|---|--------|------|------|
| 1 | **密钥明文硬编码**（Authing `app_secret`） | `run.py` | 全部敏感配置走环境变量，仓库仅留 `.env.example` |
| 2 | 写死 Windows 路径 `ml_saved\\model` | `ml_util.py` | 统一 `pathlib` + 配置目录，跨平台 |
| 3 | `os.chdir("da")` 改全局工作目录 | `run.py` | 移除，所有路径基于配置根目录 |
| 4 | 满屏裸 `except:` / `sys.exit()` 吞错误 | 多处 | API 层统一抛 HTTP 异常，任务层记录后回报失败 |
| 5 | **第 5 个基模型 `en` 被训练却从未参与融合**；权重分母写死为 3 | `blend_c/blend_r` | 统一为 `α·stack +(1-α)·mean(全部基模型)`，与模型数量解耦 |
| 6 | **预测阶段对预测集再次 `scaler.fit_transform`**（训练/预测口径不一致，数据泄漏） | `ml_pred` | 预处理状态固化进 `Preprocessor`，预测只 `transform` |
| 7 | 训练阻塞式，长任务卡死会话 | Streamlit | 改为 **ARQ + Redis** 独立 worker 进程，API 投递后立即返回，前端轮询进度 |
| 8 | `fancyimpute` 重依赖、逐列填充慢 | `dataFrameFill` | 换 `sklearn.KNNImputer`，整体填充、去依赖 |
| 9 | CV 最后一折拟合的模型当「最佳模型」存盘 | `Classifier` | 只存最佳超参，再用全量数据重建并拟合，可序列化 |
| 10 | 弃用的 `@st.cache_data(experimental_allow_widgets=True)` | EDA | 改为前端纯函数计算，无缓存副作用 |

> 另：pandas 2.x 会把字符串列推断为 `string` dtype（而非 `object`），原代码的 `dtype=='object'` 判断会漏掉类别列。后端统一改用 `is_numeric_dtype` 判定，已在测试中验证。

## 二、EDA 扩充

在原有「预览 / 统计 / 散点 / 相关性 / 缺失图」之外新增：

- **逐列数据指纹**：每列一张微缩分布图，一眼看清形态
- **分组箱线图**：数值变量在不同类别下的分布对比（原版没有）
- **散点矩阵**：前四个数值列两两关系一览
- **目标驱动因素**：选定目标列，按相关性强度排序的影响变量条形榜
- **IQR 离群点检测**：并入数据质量体检
- **数据质量体检清单**：高缺失列、常量列、疑似 ID 列、重复行、离群点
- **一键导出画像 JSON**

---

## 三、运行方式

### 方式 A：Docker Compose（推荐）

启动 4 个服务：`redis`、`backend`（API）、`worker`（ARQ）、`frontend`。

```bash
cp .env.example .env          # 首次运行，按需改端口/地址
docker compose up --build
# 前端 http://localhost:3000  ·  后端 http://localhost:8000/docs
```

> **Windows 用户**：装 Docker Desktop（WSL2 后端）后，在 PowerShell 进入项目目录执行上面的命令即可。务必先 `git config --global core.autocrlf input` 或依赖随附的 `.gitattributes`，避免脚本被检出成 CRLF 导致容器内启动失败。详见 [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)。
>
> backend 与 worker 共用同一个 `dao-data` 卷，worker 训练保存的模型/数据集 backend 才读得到。

### 方式 B：本地分别启动

需要本地有一个 Redis（`redis-server` 或 `docker run -p 6379:6379 redis:7-alpine`）。

**后端 API**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # 按需修改，确认 DAO_REDIS_DSN 指向你的 Redis
uvicorn app.main:app --reload --port 8000
```

**ARQ worker**（新开一个终端，同样的虚拟环境与环境变量）

```bash
cd backend
source .venv/bin/activate
arq app.worker.WorkerSettings
```

**前端**

```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
# 后端地址可用 NUXT_PUBLIC_API_BASE 覆盖
```

前端自带一份确定性合成的「二手房」样本数据，**未连后端也能完整体验 EDA**；训练台需要后端在线。

---

## 四、目录结构

```
da-observatory/
├── backend/                    FastAPI ML 服务
│   └── app/
│       ├── main.py             路由：datasets/train/jobs/predict/models（lifespan 管理 ARQ 连接池）
│       ├── config.py           pydantic-settings（环境变量，无硬编码密钥）
│       ├── jobs.py             ARQ task + Redis 任务状态读写
│       ├── worker.py           ARQ worker 入口（arq app.worker.WorkerSettings）
│       ├── storage.py          数据集 / 模型持久化（pathlib + joblib）
│       └── ml/
│           ├── preprocess.py   Preprocessor（fit/transform，修复泄漏）
│           ├── models.py       AutoTuner + StackingModel
│           ├── blend.py        融合（修复忽略第 5 模型的 bug）
│           └── pipeline.py     train/predict 流程，回传图表数据
└── frontend/                   Nuxt 3 应用
    ├── pages/                  index.vue（EDA）· train.vue（AutoML）
    ├── components/             19 个 SVG 图表 / UI 组件
    ├── composables/useApi.ts   后端 API 客户端
    └── utils/                  stats / profile / sample / parse（纯函数，已单测）

顶层：
├── docker-compose.yml          本地构建并运行全部 4 个服务
├── docker-compose.prod.yml     生产覆盖（拉 GHCR 预构建镜像）
├── .github/workflows/          CI（测试）+ Deploy（构建并推送到 GHCR）
└── docs/DEPLOYMENT.md          中英部署文档（Windows / GitHub / 服务器）
```

## 五、技术栈

- **前端**：Nuxt 3 · Vue 3 `<script setup>` · TypeScript · 原生 SVG 图表 · papaparse / xlsx · lucide-vue-next
- **后端**：FastAPI · ARQ + Redis（任务队列）· scikit-learn · XGBoost · LightGBM · Optuna · pandas · joblib

## 六、生产化建议（后续）

- 鉴权：`config.py` 已预留 `auth_enabled` / JWT 开关
- 对象存储：`storage.py` 的本地落盘可替换为 S3/OSS（worker 与 API 不再依赖共享卷）
- worker 伸缩：`docker compose up --scale worker=N` 即可多开消费者；CPU 密集训练已用线程池避免阻塞 worker 事件循环
- 监控：ARQ 任务可接入 `arq` 的 `on_job_start` / `on_job_end` 钩子上报指标与失败告警
