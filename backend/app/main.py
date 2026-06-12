"""FastAPI 入口。

提供：数据上传、异步训练（投递到 ARQ 队列）、任务状态查询、预测、模型管理。
所有错误通过 HTTP 异常返回，不再用 ``sys.exit`` 或裸 ``except`` 吞掉。
"""
from __future__ import annotations

import io
import uuid
from contextlib import asynccontextmanager

import pandas as pd
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .jobs import get_job, init_job
from .ml.pipeline import predict_pipeline
from .schemas import (
    JobAccepted,
    JobStatus,
    PredictRequest,
    TrainRequest,
    UploadResponse,
)
from .storage import delete_model, list_models, load_dataset, load_model, save_dataset


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时建立 ARQ Redis 连接池；关闭时释放
    app.state.redis = await create_pool(RedisSettings.from_dsn(settings.redis_dsn))
    try:
        yield
    finally:
        await app.state.redis.aclose()


app = FastAPI(title="Data Observatory API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_table(filename: str, raw: bytes) -> pd.DataFrame:
    name = filename.lower()
    try:
        if name.endswith((".csv", ".tsv", ".txt")):
            sep = "\t" if name.endswith(".tsv") else ","
            return pd.read_csv(io.BytesIO(raw), sep=sep)
        if name.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"文件解析失败：{exc}") from exc
    raise HTTPException(400, "仅支持 CSV / TSV / Excel 文件。")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/datasets", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> UploadResponse:
    raw = await file.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"文件超过 {settings.max_upload_mb}MB 上限。")
    df = _read_table(file.filename or "data.csv", raw)
    if df.empty:
        raise HTTPException(400, "文件中没有数据。")
    if len(df) > settings.max_rows:
        raise HTTPException(413, f"行数超过 {settings.max_rows} 上限。")
    dataset_id = save_dataset(df)
    return UploadResponse(dataset_id=dataset_id, rows=len(df), columns=df.columns.tolist())


@app.post("/train", response_model=JobAccepted)
async def train(req: TrainRequest, request: Request) -> JobAccepted:
    try:
        df = load_dataset(req.dataset_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    if req.target not in df.columns:
        raise HTTPException(400, f"目标列 {req.target} 不存在。")

    cfg_dict = {
        "task": req.task, "target": req.target, "metric": req.metric,
        "drop_columns": req.drop_columns, "n_trials": min(req.n_trials, settings.max_trials),
        "meta_weight": req.meta_weight, "test_ratio": req.test_ratio,
        "balance": req.balance, "solve_collinearity": req.solve_collinearity,
        "auto_feature": req.auto_feature,
    }
    job_id = uuid.uuid4().hex[:12]
    redis = request.app.state.redis
    await init_job(redis, job_id)
    # 用我们的 job_id 作为 ARQ job id，二者统一便于排查
    await redis.enqueue_job("run_training_task", req.dataset_id, cfg_dict, job_id, _job_id=job_id)
    return JobAccepted(job_id=job_id)


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str, request: Request) -> JobStatus:
    data = await get_job(request.app.state.redis, job_id)
    if not data:
        raise HTTPException(404, "任务不存在。")
    return JobStatus(**data)


@app.post("/predict")
def predict(req: PredictRequest) -> dict:
    try:
        artifact = load_model(req.model_id)
        df = load_dataset(req.dataset_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    result = predict_pipeline(artifact, df)
    return {"rows": len(result), "columns": result.columns.tolist(), "data": result.to_dict("records")}


@app.get("/models")
def models() -> dict:
    return {"models": list_models()}


@app.delete("/models/{model_id}")
def remove_model(model_id: str) -> dict:
    if not delete_model(model_id):
        raise HTTPException(404, "模型不存在。")
    return {"deleted": model_id}
