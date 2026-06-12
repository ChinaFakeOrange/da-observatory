"""端到端训练 / 预测流程。

设计原则：后端只负责计算，返回 **JSON 可序列化的指标与图表数据**（ROC 点、混淆矩阵、
预测对照等），由 Nuxt 前端用统一的 SVG 组件绘制。避免在服务端生成 Plotly 图。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from .blend import blend_predict, blend_proba
from .models import CLASSIFICATION, REGRESSION, AutoTuner, StackingModel
from .preprocess import Preprocessor


@dataclass
class TrainConfig:
    task: str  # CLASSIFICATION | REGRESSION
    target: str
    metric: str = "RMSE"  # RMSE/MAE/MSE/R2 或 F1/AUC/ACC
    drop_columns: list[str] | None = None
    n_trials: int = 5
    meta_weight: float = 0.5
    test_ratio: float = 0.25
    balance: bool = False
    solve_collinearity: bool = False
    auto_feature: bool = False


# --- 评分函数 ---
def _make_scorer(task: str, metric: str):
    if task == CLASSIFICATION:
        if metric == "ACC":
            return lambda est, X, y: accuracy_score(y, est.predict(X)), True
        if metric == "AUC":
            def auc(est, X, y):
                proba = est.predict_proba(X)
                n = proba.shape[1]
                if n == 2:
                    return roc_auc_score(y, proba[:, 1])
                return roc_auc_score(y, proba, average="macro", multi_class="ovr")
            return auc, True
        return lambda est, X, y: f1_score(y, est.predict(X), average="macro"), True
    # 回归：返回 (scorer, maximize)
    if metric == "R2":
        return lambda est, X, y: r2_score(y, est.predict(X)), True
    if metric == "MAE":
        return lambda est, X, y: mean_absolute_error(y, est.predict(X)), False
    if metric == "MSE":
        return lambda est, X, y: mean_squared_error(y, est.predict(X)), False
    return lambda est, X, y: float(np.sqrt(mean_squared_error(y, est.predict(X)))), False


def train_pipeline(df: pd.DataFrame, cfg: TrainConfig) -> dict:
    df = df.copy()
    if cfg.drop_columns:
        df = df.drop(columns=[c for c in cfg.drop_columns if c in df.columns])

    pre = Preprocessor(
        target_name=cfg.target,
        use_robust_scaler=cfg.balance,
        solve_collinearity=cfg.solve_collinearity,
    )
    X, y = pre.fit_transform(df)

    # 类别目标编码（兼容 pandas 2.x string dtype）
    label_map = None
    if cfg.task == CLASSIFICATION and not pd.api.types.is_numeric_dtype(y):
        classes = sorted(y.dropna().astype(str).unique().tolist())
        label_map = {c: i for i, c in enumerate(classes)}
        y = y.astype(str).map(label_map)

    scorer, maximize = _make_scorer(cfg.task, cfg.metric)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=cfg.test_ratio, random_state=42)

    tuner = AutoTuner(X_tr, y_tr, cfg.task, scorer, n_trials=cfg.n_trials, maximize=maximize)
    base = tuner.run()

    meta = LogisticRegression(max_iter=1000) if cfg.task == CLASSIFICATION else LinearRegression()
    stack = StackingModel(base, meta, cfg.task).fit(X_tr, y_tr)

    a = cfg.meta_weight
    if cfg.task == CLASSIFICATION:
        result = _classification_report_payload(stack, base, X_tr, y_tr, X_te, y_te, a, label_map)
    else:
        result = _regression_report_payload(stack, base, X_tr, y_tr, X_te, y_te, a)

    artifact = {
        "preprocessor": pre,
        "stack": stack,
        "base": base,
        "task": cfg.task,
        "meta_weight": a,
        "label_map": label_map,
        "feature_columns": pre.feature_columns_,
    }
    result["artifact"] = artifact
    return result


def _classification_report_payload(stack, base, X_tr, y_tr, X_te, y_te, a, label_map):
    y_pred = blend_predict(CLASSIFICATION, stack, base, X_te, a)
    inv = {v: k for k, v in (label_map or {}).items()}
    classes = sorted(np.unique(y_te))
    target_names = [str(inv.get(c, c)) for c in classes]

    report = classification_report(
        y_te, y_pred, labels=classes, target_names=target_names, output_dict=True, zero_division=0
    )
    # ROC（每类一条）
    proba = blend_proba(stack, base, X_te, a)
    roc = []
    y_oh = pd.get_dummies(y_te)
    for idx, c in enumerate(classes):
        if c not in y_oh.columns:
            continue
        fpr, tpr, _ = roc_curve(y_oh[c], proba[:, idx])
        roc.append({
            "label": target_names[idx],
            "auc": float(roc_auc_score(y_oh[c], proba[:, idx])),
            "points": [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr)],
        })
    return {
        "task": CLASSIFICATION,
        "metrics": {
            "train_accuracy": float(accuracy_score(y_tr, blend_predict(CLASSIFICATION, stack, base, X_tr, a))),
            "test_accuracy": float(accuracy_score(y_te, y_pred)),
            "macro_f1": float(f1_score(y_te, y_pred, average="macro")),
        },
        "classification_report": report,
        "roc": roc,
        "classes": target_names,
    }


def _regression_report_payload(stack, base, X_tr, y_tr, X_te, y_te, a):
    pred_te = blend_predict(REGRESSION, stack, base, X_te, a)
    pred_tr = blend_predict(REGRESSION, stack, base, X_tr, a)
    return {
        "task": REGRESSION,
        "metrics": {
            "train_r2": float(r2_score(y_tr, pred_tr)),
            "test_r2": float(r2_score(y_te, pred_te)),
            "test_rmse": float(np.sqrt(mean_squared_error(y_te, pred_te))),
            "test_mae": float(mean_absolute_error(y_te, pred_te)),
        },
        # 预测 vs 实际散点（前端画 OLS 对照）
        "scatter": [{"actual": float(t), "pred": float(p)} for t, p in zip(y_te, pred_te)],
    }


def predict_pipeline(artifact: dict, df: pd.DataFrame) -> pd.DataFrame:
    pre: Preprocessor = artifact["preprocessor"]
    stack = artifact["stack"]
    base = artifact["base"]
    task = artifact["task"]
    a = artifact["meta_weight"]
    label_map = artifact["label_map"]

    X = pre.transform(df)
    out = df.reset_index(drop=True).copy()
    if task == CLASSIFICATION:
        pred = blend_predict(CLASSIFICATION, stack, base, X, a)
        inv = {v: k for k, v in (label_map or {}).items()}
        out["预测结果"] = [inv.get(int(p), int(p)) for p in pred]
        proba = blend_proba(stack, base, X, a)
        for i in range(proba.shape[1]):
            name = inv.get(i, i)
            out[f"概率_{name}"] = proba[:, i]
    else:
        out["预测结果"] = blend_predict(REGRESSION, stack, base, X, a)
    return out
