"""模型调参与 Stacking 融合。

相比原 ``Classifier`` 类的修复/改进：
- 原实现把 CV 最后一折拟合出的 estimator 直接当作"最佳模型"存下来（best_model =
  self.model），既容易在 pickle 时出问题，也只在一折上 fit 过。这里改为只保存
  **最佳超参数**，再用全量数据重建并拟合，干净且可序列化。
- 去掉散落的 ``sys.exit`` 与裸 ``except``；调参异常会向上抛出由 API 统一处理。
"""
from __future__ import annotations

import numpy as np
import optuna
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier, XGBRegressor

optuna.logging.set_verbosity(optuna.logging.WARNING)

CLASSIFICATION = "Classification"
REGRESSION = "Regression"


def _xgb_params(trial):
    return dict(
        learning_rate=trial.suggest_float("learning_rate", 5e-3, 0.3, log=True),
        n_estimators=trial.suggest_int("n_estimators", 100, 1500),
        max_depth=trial.suggest_int("max_depth", 3, 11),
        min_child_weight=trial.suggest_int("min_child_weight", 1, 7),
        gamma=trial.suggest_float("gamma", 0, 1),
        subsample=trial.suggest_float("subsample", 0.5, 1.0),
        colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
        verbosity=0,
    )


def _lgb_params(trial):
    return dict(
        num_leaves=trial.suggest_int("num_leaves", 3, 64),
        learning_rate=trial.suggest_float("learning_rate", 5e-3, 0.3, log=True),
        n_estimators=trial.suggest_int("n_estimators", 100, 1500),
        min_child_samples=trial.suggest_int("min_child_samples", 10, 100),
        colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
        reg_alpha=trial.suggest_float("reg_alpha", 1e-9, 10.0, log=True),
        reg_lambda=trial.suggest_float("reg_lambda", 1e-9, 10.0, log=True),
        verbosity=-1,
    )


def _hist_params(trial):
    return dict(
        l2_regularization=trial.suggest_float("l2_regularization", 1e-4, 100, log=True),
        learning_rate=trial.suggest_float("learning_rate", 5e-3, 0.3, log=True),
        max_iter=trial.suggest_int("max_iter", 100, 1500),
        max_depth=trial.suggest_int("max_depth", 3, 11),
        min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 15),
    )


def _knn_params(trial):
    return dict(
        n_neighbors=trial.suggest_int("n_neighbors", 5, 60),
        weights=trial.suggest_categorical("weights", ["uniform", "distance"]),
        metric=trial.suggest_categorical("metric", ["minkowski", "euclidean", "manhattan"]),
    )


def _enet_params(trial):
    return dict(
        alpha=trial.suggest_float("alpha", 1e-6, 1.0, log=True),
        l1_ratio=trial.suggest_float("l1_ratio", 1e-3, 1.0),
        max_iter=trial.suggest_int("max_iter", 500, 8000),
    )


class AutoTuner:
    """对四个基模型分别调参，返回拟合好的 estimator 字典。"""

    def __init__(self, X, y, task: str, scorer, n_trials: int = 5, maximize: bool = True):
        self.X, self.y = X.reset_index(drop=True), y.reset_index(drop=True)
        self.task = task
        self.scorer = scorer
        self.n_trials = n_trials
        self.direction = "maximize" if maximize else "minimize"
        self.kf = KFold(n_splits=3, shuffle=True, random_state=42)

    def _cv_score(self, build_estimator) -> float:
        scores = []
        for tr, te in self.kf.split(self.X):
            est = build_estimator()
            est.fit(self.X.iloc[tr], self.y.iloc[tr])
            scores.append(self.scorer(est, self.X.iloc[te], self.y.iloc[te]))
        return float(np.mean(scores))

    def _optimize(self, suggest, ctor) -> object:
        def objective(trial):
            params = suggest(trial)
            return self._cv_score(lambda: ctor(params))

        study = optuna.create_study(direction=self.direction)
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)
        best = ctor(study.best_params)
        best.fit(self.X, self.y)
        return best

    def run(self) -> dict[str, object]:
        is_clf = self.task == CLASSIFICATION
        models: dict[str, object] = {}
        models["xgb"] = self._optimize(
            _xgb_params, lambda p: (XGBClassifier if is_clf else XGBRegressor)(**p)
        )
        models["lgb"] = self._optimize(
            _lgb_params, lambda p: (LGBMClassifier if is_clf else LGBMRegressor)(**p)
        )
        models["hist"] = self._optimize(
            _hist_params,
            lambda p: (HistGradientBoostingClassifier if is_clf else HistGradientBoostingRegressor)(**p),
        )
        if is_clf:
            models["aux"] = self._optimize(_knn_params, lambda p: KNeighborsClassifier(**p))
        else:
            models["aux"] = self._optimize(_enet_params, lambda p: ElasticNet(**p))
        return models


class StackingModel:
    """用基模型的预测作为元模型的输入。"""

    def __init__(self, base_models: dict, meta_model, task: str):
        self.base_models = base_models
        self.meta_model = meta_model
        self.task = task
        self.keys = list(base_models.keys())

    def _stack_features(self, X) -> np.ndarray:
        cols = []
        for k in self.keys:
            m = self.base_models[k]
            if self.task == CLASSIFICATION:
                cols.append(m.predict_proba(X))
            else:
                cols.append(np.asarray(m.predict(X)).reshape(-1, 1))
        return np.concatenate(cols, axis=1)

    def fit(self, X, y):
        for m in self.base_models.values():
            m.fit(X, y)
        self.meta_model.fit(self._stack_features(X), y)
        return self

    def predict(self, X):
        return self.meta_model.predict(self._stack_features(X))

    def predict_proba(self, X):
        return self.meta_model.predict_proba(self._stack_features(X))
