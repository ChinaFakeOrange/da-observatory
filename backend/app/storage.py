"""模型与数据集的持久化。

修复：原代码到处写死 ``ml_saved\\model`` 这类 Windows 路径，并用 ``os.chdir("da")``
切换工作目录。这里统一用 ``pathlib`` + 配置目录，跨平台且无副作用。
"""
from __future__ import annotations

import uuid
from pathlib import Path

import joblib
import pandas as pd

from .config import settings


def _dataset_path(dataset_id: str) -> Path:
    d = settings.data_dir / "datasets"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{dataset_id}.parquet"


def save_dataset(df: pd.DataFrame) -> str:
    dataset_id = uuid.uuid4().hex[:12]
    df.to_parquet(_dataset_path(dataset_id))
    return dataset_id


def load_dataset(dataset_id: str) -> pd.DataFrame:
    path = _dataset_path(dataset_id)
    if not path.exists():
        raise FileNotFoundError(f"数据集不存在: {dataset_id}")
    return pd.read_parquet(path)


def save_model(artifact: dict) -> str:
    model_id = ("clf" if artifact["task"] == "Classification" else "reg") + "_" + uuid.uuid4().hex[:8]
    joblib.dump(artifact, settings.model_dir / f"{model_id}.pkl")
    return model_id


def load_model(model_id: str) -> dict:
    path = settings.model_dir / f"{model_id}.pkl"
    if not path.exists():
        raise FileNotFoundError(f"模型不存在: {model_id}")
    return joblib.load(path)


def list_models() -> list[str]:
    return sorted(p.stem for p in settings.model_dir.glob("*.pkl"))


def delete_model(model_id: str) -> bool:
    path = settings.model_dir / f"{model_id}.pkl"
    if path.exists():
        path.unlink()
        return True
    return False
