"""应用配置。

安全修复：原 ``run.py`` 把 Authing 的 app_secret 明文硬编码在源码里
（``2b8178d4...``），任何拿到代码的人都能拿到密钥。这里所有敏感配置一律走环境变量，
仓库内只保留 ``.env.example`` 模板，真实 ``.env`` 不入库。
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DAO_", extra="ignore")

    # 存储
    data_dir: Path = Path("./var")
    max_upload_mb: int = 50

    # 训练约束（防止用户参数把服务打爆）
    max_trials: int = 25
    max_rows: int = 200_000

    # 任务队列（ARQ + Redis）
    redis_dsn: str = "redis://localhost:6379"
    job_ttl_seconds: int = 86_400  # 任务状态在 Redis 中的保留时长

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # 鉴权（如启用，从环境注入；缺省关闭便于本地开发）
    auth_enabled: bool = False
    auth_jwt_secret: str = ""

    @property
    def model_dir(self) -> Path:
        d = self.data_dir / "models"
        d.mkdir(parents=True, exist_ok=True)
        return d


settings = Settings()
