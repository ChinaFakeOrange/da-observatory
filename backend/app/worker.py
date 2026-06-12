"""ARQ worker 入口。

启动方式：``arq app.worker.WorkerSettings``
worker 独立于 API 进程运行，消费 Redis 队列里的训练任务。
"""
from __future__ import annotations

from arq.connections import RedisSettings

from .config import settings
from .jobs import run_training_task


class WorkerSettings:
    functions = [run_training_task]
    redis_settings = RedisSettings.from_dsn(settings.redis_dsn)
    # 训练耗时较长，放宽单任务超时（秒）；按需调整
    job_timeout = 60 * 30
    max_jobs = 4
    keep_result = settings.job_ttl_seconds
