"""API 数据模型。"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# 字段名以 model_ 开头（model_id）会触发 pydantic 的 protected namespace 警告，
# 这里显式关闭该保护命名空间，纯粹为了消除启动日志里的无害告警。
class _Base(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


class TrainRequest(_Base):
    dataset_id: str
    task: Literal["Classification", "Regression"]
    target: str
    metric: str = "RMSE"
    drop_columns: list[str] = Field(default_factory=list)
    n_trials: int = Field(default=5, ge=1, le=25)
    meta_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    test_ratio: float = Field(default=0.25, ge=0.05, le=0.6)
    balance: bool = False
    solve_collinearity: bool = False
    auto_feature: bool = False


class JobAccepted(_Base):
    job_id: str
    status: str = "queued"


class JobStatus(_Base):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    progress: float = 0.0
    message: str = ""
    model_id: str | None = None
    result: dict[str, Any] | None = None


class PredictRequest(_Base):
    model_id: str
    dataset_id: str


class UploadResponse(_Base):
    dataset_id: str
    rows: int
    columns: list[str]
