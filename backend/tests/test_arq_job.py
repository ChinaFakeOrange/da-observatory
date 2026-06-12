"""ARQ 任务 + Redis 状态的集成测试。

直接调用 ARQ task（注入真实 Redis 作为 ctx），验证：
- 任务把进度/状态写进 Redis 哈希
- 训练完成后 model 落盘、可被 predict 使用
需要环境变量 DAO_REDIS_DSN 指向一个可用 Redis（CI 用 service container 提供）。
"""
import os
import pytest
from arq import create_pool
from arq.connections import RedisSettings

from app.jobs import get_job, init_job, run_training_task
from app.storage import load_dataset, load_model, save_dataset
from app.ml.pipeline import predict_pipeline
from tests.conftest import make_df

REDIS_DSN = os.environ.get("DAO_REDIS_DSN", "redis://localhost:6379")


@pytest.mark.asyncio
async def test_arq_training_writes_state_and_model():
    redis = await create_pool(RedisSettings.from_dsn(REDIS_DSN))
    try:
        dataset_id = save_dataset(make_df())
        job_id = "testjob123456"
        await init_job(redis, job_id)

        cfg_dict = {
            "task": "Regression", "target": "总价", "metric": "RMSE",
            "drop_columns": [], "n_trials": 2, "meta_weight": 0.5,
            "test_ratio": 0.25, "balance": False, "solve_collinearity": True, "auto_feature": False,
        }
        # 直接执行 task（ctx 注入真实 redis），相当于 worker 跑了一次
        await run_training_task({"redis": redis}, dataset_id, cfg_dict, job_id)

        status = await get_job(redis, job_id)
        assert status["status"] == "succeeded"
        assert status["progress"] == 1.0
        assert status["model_id"]
        assert status["result"]["metrics"]["test_r2"] > 0.5

        # 模型可加载并预测
        artifact = load_model(status["model_id"])
        df = load_dataset(dataset_id).drop(columns=["总价"]).head(5)
        out = predict_pipeline(artifact, df)
        assert "预测结果" in out.columns
    finally:
        await redis.aclose()
