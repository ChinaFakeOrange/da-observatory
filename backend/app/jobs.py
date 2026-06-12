"""异步训练任务（ARQ + Redis）。

原 Streamlit 版训练是阻塞式的，长任务会卡死会话。这里用 **ARQ + Redis** 把训练放到独立
worker 进程：

- API 进程通过 ``enqueue_job`` 把任务投递到 Redis 队列，立即返回 ``job_id``；
- worker 进程消费队列、执行训练，并把阶段进度写回 Redis 哈希 ``dao:job:{job_id}``；
- 前端轮询 ``GET /jobs/{id}``，API 进程从同一个 Redis 哈希读状态。

因为 API 与 worker 是两个进程，任务状态必须放在共享存储（Redis），不能再用进程内字典。
训练本身是 CPU 密集的同步函数，放进线程池执行，避免阻塞 worker 的事件循环。
"""
from __future__ import annotations

import asyncio
import json
import traceback
from typing import Any

from .config import settings
from .ml.pipeline import TrainConfig, train_pipeline
from .storage import load_dataset, save_model

JOB_PREFIX = "dao:job:"


def _key(job_id: str) -> str:
    return f"{JOB_PREFIX}{job_id}"


async def set_job(redis, job_id: str, **fields: Any) -> None:
    """把任务状态字段写入 Redis 哈希（值统一序列化为字符串）。"""
    mapping: dict[str, str] = {}
    for k, v in fields.items():
        if v is None:
            mapping[k] = ""
        elif k == "result":
            mapping[k] = json.dumps(v, default=float, ensure_ascii=False)
        else:
            mapping[k] = str(v)
    await redis.hset(_key(job_id), mapping=mapping)
    await redis.expire(_key(job_id), settings.job_ttl_seconds)


async def init_job(redis, job_id: str) -> None:
    await set_job(redis, job_id, status="queued", progress=0.0, message="排队中",
                  model_id=None, result=None)


async def get_job(redis, job_id: str) -> dict | None:
    raw = await redis.hgetall(_key(job_id))
    if not raw:
        return None
    d = {
        (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
        for k, v in raw.items()
    }
    return {
        "job_id": job_id,
        "status": d.get("status", "queued"),
        "progress": float(d.get("progress") or 0.0),
        "message": d.get("message", ""),
        "model_id": d.get("model_id") or None,
        "result": json.loads(d["result"]) if d.get("result") else None,
    }


async def run_training_task(ctx: dict, dataset_id: str, cfg_dict: dict, job_id: str) -> dict:
    """ARQ task：执行一次完整训练。``ctx['redis']`` 由 worker 注入。"""
    redis = ctx["redis"]
    try:
        await set_job(redis, job_id, status="running", progress=0.1, message="加载数据")
        df = load_dataset(dataset_id)

        await set_job(redis, job_id, status="running", progress=0.3, message="调参与训练")
        cfg = TrainConfig(**cfg_dict)
        # CPU 密集，放线程池，避免阻塞 worker 事件循环
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, train_pipeline, df, cfg)

        await set_job(redis, job_id, status="running", progress=0.9, message="保存模型")
        model_id = save_model(result["artifact"])

        clean = {k: v for k, v in result.items() if k != "artifact"}
        await set_job(redis, job_id, status="succeeded", progress=1.0, message="完成",
                      model_id=model_id, result=clean)
        return {"model_id": model_id}
    except Exception as exc:  # noqa: BLE001 — 任务边界：记录并把失败状态写回 Redis
        await set_job(redis, job_id, status="failed", progress=0.0,
                      message=f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise
