"""融合预测。

修复原 ``blend_c`` / ``blend_r`` 的两个问题：
1. 原 ``models`` 列表是 ``[stack, xgb, lgb, hist, en]`` 共 5 个，但融合只用了前 4 个，
   第 5 个基模型 ``en``（回归 ElasticNet / 分类 KNN）**被训练却从未参与融合**。
2. 权重 ``(1-alpha)/3`` 的分母写死为 3，与实际基模型数量耦合，扩展即出错。

这里统一为：``pred = alpha * stack + (1 - alpha) * mean(base_models)``，
其中 base_models 为全部非元基模型，权重定义清晰、与模型数量解耦。
"""
from __future__ import annotations

import numpy as np

from .models import CLASSIFICATION


def _mean_base_proba(base_models: dict, X) -> np.ndarray:
    probas = [m.predict_proba(X) for m in base_models.values()]
    return np.mean(probas, axis=0)


def _mean_base_pred(base_models: dict, X) -> np.ndarray:
    preds = [np.asarray(m.predict(X)) for m in base_models.values()]
    return np.mean(preds, axis=0)


def blend_proba(stack_model, base_models: dict, X, alpha: float = 0.5) -> np.ndarray:
    """分类：返回融合后的类别概率矩阵。"""
    return alpha * stack_model.predict_proba(X) + (1 - alpha) * _mean_base_proba(base_models, X)


def blend_classify(stack_model, base_models: dict, X, alpha: float = 0.5) -> np.ndarray:
    return np.argmax(blend_proba(stack_model, base_models, X, alpha), axis=1)


def blend_regress(stack_model, base_models: dict, X, alpha: float = 0.5) -> np.ndarray:
    return alpha * np.asarray(stack_model.predict(X)) + (1 - alpha) * _mean_base_pred(base_models, X)


def blend_predict(task: str, stack_model, base_models: dict, X, alpha: float = 0.5) -> np.ndarray:
    if task == CLASSIFICATION:
        return blend_classify(stack_model, base_models, X, alpha)
    return blend_regress(stack_model, base_models, X, alpha)
