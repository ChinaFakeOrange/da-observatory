🌐 Chinese → [README.ch.md](./README.ch.md) ｜ 📦 部署文档（中英）→ [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)
# da-observatory
A production-grade rebuild of the original Streamlit "EDA / AutoML" monolith into a **Nuxt 3 frontend + FastAPI ML backend** two-service architecture. The frontend handles interaction and visualization; the backend handles data persistence, hyper-parameter tuning, training, and prediction.


```
┌─────────────────────────┐         ┌──────────────────────────────┐
│   Nuxt 3 (SSR) frontend  │         │      FastAPI ML backend       │
│                          │         │                              │
│  /        EDA workbench  │  HTTP   │  POST /datasets   upload      │
│  /train   AutoML studio  │ ──────▶ │  POST /train      enqueue job │
│                          │         │  GET  /jobs/{id}  read status │
│  profiles / histograms   │ ◀────── │  POST /predict    inference   │
│  correlation / box plot  │  JSON   │  GET  /models     management  │
│  all charts rendered SVG │  charts └───────────┬──────────────────┘
└─────────────────────────┘                     │ enqueue / read state
                                                ▼
                                  ┌──────────────────────────────┐
                                  │   Redis                       │
                                  │   queue + job-state hashes    │
                                  └─────────────┬─────────────────┘
                                                │ consume / write progress
                                  ┌─────────────▼─────────────────┐
                                  │   ARQ Worker (separate proc)  │
                                  │   tuning + stacking + saving  │
                                  └──────────────────────────────┘
```

Training runs in a **separate ARQ worker process**: the API enqueues a job to Redis and immediately returns a `job_id`; the worker consumes the queue, runs training, and writes stage progress back to Redis; the frontend polls `/jobs/{id}` and the API reads state from the same Redis hash. The API and worker are decoupled and can scale independently.

By design the backend **returns only JSON-serializable metrics and chart data** (ROC points, confusion matrices, predicted-vs-actual scatter), which the frontend draws with a unified set of SVG components. This keeps chart styling consistent and keeps the backend stateless and easy to scale horizontally.

---

## 1. Issues fixed vs. the original

| #    | Original problem                                             | Where             | Fix                                                          |
| ---- | ------------------------------------------------------------ | ----------------- | ------------------------------------------------------------ |
| 1    | **Hardcoded secret** in source (Authing `app_secret`)        | `run.py`          | All sensitive config via env vars; repo only ships `.env.example` |
| 2    | Hardcoded Windows path `ml_saved\\model`                     | `ml_util.py`      | Unified `pathlib` + config dir, cross-platform               |
| 3    | `os.chdir("da")` mutating global cwd                         | `run.py`          | Removed; all paths derive from a config root                 |
| 4    | Bare `except:` / `sys.exit()` swallowing errors everywhere   | many places       | API raises proper HTTP errors; task layer logs and reports failure |
| 5    | **5th base model `en` trained but never used in blending**; weight denominator hardcoded to 3 | `blend_c/blend_r` | Unified to `α·stack + (1-α)·mean(all base models)`, decoupled from model count |
| 6    | **Predict path re-ran `scaler.fit_transform` on the prediction set** (train/predict mismatch — data leakage) | `ml_pred`         | Preprocessing state frozen into `Preprocessor`; predict only `transform`s |
| 7    | Blocking training, long jobs froze the session               | Streamlit         | Switched to **ARQ + Redis** with a separate worker; API returns immediately, frontend polls progress |
| 8    | Heavy `fancyimpute` dependency, slow column-by-column imputation | `dataFrameFill`   | Replaced with `sklearn.KNNImputer`, whole-frame imputation, dependency removed |
| 9    | Model fitted on the last CV fold was saved as the "best model" | `Classifier`      | Store best hyper-params only, then rebuild and fit on full data; serializable |
| 10   | Deprecated `@st.cache_data(experimental_allow_widgets=True)` | EDA               | Replaced with pure frontend functions, no cache side effects |

> Also: pandas 2.x infers string columns as `string` dtype (not `object`), so the original `dtype=='object'` check missed categorical columns. The backend now consistently uses `is_numeric_dtype`, verified by tests.

## 2. EDA expansions

On top of the original "preview / stats / scatter / correlation / missing-map", new additions:

- **Per-column data fingerprint**: a mini distribution chart per column for instant shape reading
- **Grouped box plots**: distribution of a numeric variable across categories (not in the original)
- **Scatter matrix**: pairwise relationships among the first four numeric columns
- **Target drivers**: pick a target column and see influencing variables ranked by correlation strength
- **IQR outlier detection**: folded into the data-quality check
- **Data-quality checklist**: high-missing columns, constant columns, suspected ID columns, duplicate rows, outliers
- **One-click profile JSON export**

---

## 3. Running it

### Option A: Docker Compose (recommended)

Starts 4 services: `redis`, `backend` (API), `worker` (ARQ), `frontend`.

```bash
cp .env.example .env          # first run; adjust ports/URLs as needed
docker compose up --build
# Frontend http://localhost:3000  ·  Backend http://localhost:8000/docs
```

> **Windows users**: install Docker Desktop (WSL2 backend), then run the commands above from the project directory in PowerShell. Run `git config --global core.autocrlf input` first (or rely on the bundled `.gitattributes`) so scripts aren't checked out with CRLF, which breaks container startup. See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md).
>
> `backend` and `worker` share the same `dao-data` volume — that's how the backend reads the models/datasets the worker saves.

### Option B: run services separately

Requires a local Redis (`redis-server`, or `docker run -p 6379:6379 redis:7-alpine`).

**Backend API**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # ensure DAO_REDIS_DSN points to your Redis
uvicorn app.main:app --reload --port 8000
```

**ARQ worker** (new terminal, same venv and env vars)

```bash
cd backend
source .venv/bin/activate
arq app.worker.WorkerSettings
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
# Override the backend URL with NUXT_PUBLIC_API_BASE
```

The frontend ships a deterministic synthetic "second-hand housing" sample dataset, so **the full EDA works without a backend**; the training studio needs the backend online.

---

## 4. Project layout

```
da-observatory/
├── backend/                    FastAPI ML service
│   └── app/
│       ├── main.py             routes: datasets/train/jobs/predict/models (lifespan manages the ARQ pool)
│       ├── config.py           pydantic-settings (env vars, no hardcoded secrets)
│       ├── jobs.py             ARQ task + Redis job-state read/write
│       ├── worker.py           ARQ worker entrypoint (arq app.worker.WorkerSettings)
│       ├── storage.py          dataset / model persistence (pathlib + joblib)
│       └── ml/
│           ├── preprocess.py   Preprocessor (fit/transform, leakage fixed)
│           ├── models.py       AutoTuner + StackingModel
│           ├── blend.py        blending (fixes the ignored-5th-model bug)
│           └── pipeline.py     train/predict flow, returns chart data
├── frontend/                   Nuxt 3 app
│   ├── pages/                  index.vue (EDA) · train.vue (AutoML)
│   ├── components/             19 SVG chart / UI components
│   ├── composables/useApi.ts   backend API client
│   └── utils/                  stats / profile / sample / parse (pure, unit-tested)
├── docker-compose.yml          local build & run (all 4 services)
├── docker-compose.prod.yml     production override (pull prebuilt GHCR images)
└── .github/workflows/          CI (tests) + Deploy (build & push to GHCR)
```

## 5. Tech stack

- **Frontend**: Nuxt 3 · Vue 3 `<script setup>` · TypeScript · native SVG charts · papaparse / xlsx · lucide-vue-next
- **Backend**: FastAPI · ARQ + Redis (job queue) · scikit-learn · XGBoost · LightGBM · Optuna · pandas · joblib

## 6. Production notes (next steps)

- Auth: `config.py` already reserves an `auth_enabled` / JWT switch
- Object storage: the local disk in `storage.py` can be swapped for S3/OSS (worker and API then no longer need a shared volume)
- Worker scaling: `docker compose up --scale worker=N` adds consumers; CPU-bound training already runs in a thread pool to avoid blocking the worker event loop
- Monitoring: hook ARQ's `on_job_start` / `on_job_end` to report metrics and failure alerts

- <img width="1719" height="1200" alt="9ceb08c94a5921c06262ea2e502939bc" src="https://github.com/user-attachments/assets/c53e1cab-7df1-45bd-b3fd-34fe4c43f4d5" />
<img width="1719" height="1200" alt="6504e14e2f7f13cc5a255792b9664494" src="https://github.com/user-attachments/assets/a8497365-2f63-4bb0-9bf4-5607336127f2" />


