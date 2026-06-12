"""数据预处理。

相比原 ``ml_util.py`` 的修复要点：
- 原代码在预测阶段对预测集再次 ``scaler.fit_transform``，造成训练/预测口径不一致
  （数据泄漏）。这里把 impute / 编码 / 缩放 / PCA 的状态全部固化到 ``Preprocessor``
  实例里，预测时只 ``transform``，不再 ``fit``。
- 用 ``sklearn.impute.KNNImputer`` 替换 fancyimpute（去掉一个重依赖，且整体而非逐列填充）。
- 全程不依赖任何 Windows 路径或 ``os.chdir``。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import KNNImputer
from sklearn.preprocessing import RobustScaler, StandardScaler

HIGH_MISSING_THRESHOLD = 0.30  # 训练时缺失超过该比例的列直接剔除
COLLINEARITY_CUTOFF = 0.70


def _missing_ratio(df: pd.DataFrame) -> pd.Series:
    return df.isnull().sum() / max(len(df), 1)


def _calc_drop_by_corr(df: pd.DataFrame, cut: float) -> list[str]:
    """返回因高相关而应当合并/丢弃的列（与原 corrX_new 等价，但更简洁）。"""
    corr = df.corr().abs()
    avg = corr.mean(axis=1)
    cols = list(corr.columns)
    drop: set[str] = set()
    for i in range(len(cols) - 1):
        for j in range(i + 1, len(cols)):
            if corr.iloc[i, j] > cut:
                drop.add(cols[i] if avg.iloc[i] > avg.iloc[j] else cols[j])
    # 收集所有参与高相关的列（用于 PCA 融合）
    involved: set[str] = set()
    for i in range(len(cols) - 1):
        for j in range(i + 1, len(cols)):
            if corr.iloc[i, j] > cut:
                involved.add(cols[i])
                involved.add(cols[j])
    return sorted(involved)


@dataclass
class Preprocessor:
    target_name: str
    use_robust_scaler: bool = False
    solve_collinearity: bool = False

    # 学到的状态（fit 后填充，可被 joblib 序列化）
    feature_columns_: list[str] = field(default_factory=list)
    category_maps_: dict[str, dict] = field(default_factory=dict)
    impute_values_: dict[str, float] = field(default_factory=dict)
    collinear_cols_: list[str] = field(default_factory=list)
    scaler_: object | None = None
    pca_: object | None = None
    _fitted: bool = False

    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        df = df.replace("", np.nan).copy()

        # 1) 训练时剔除高缺失列
        drop_cols = _missing_ratio(df)[_missing_ratio(df) >= HIGH_MISSING_THRESHOLD].index.tolist()
        drop_cols = [c for c in drop_cols if c != self.target_name]
        df = df.drop(columns=drop_cols)

        # 2) 类别列 -> 顺序编码（保存映射）
        #    用 is_numeric_dtype 判定，兼容 pandas 2.x 把字符串列推断为 string dtype 的情况
        for col in df.columns:
            if col == self.target_name:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                cats = sorted(df[col].dropna().astype(str).unique().tolist())
                self.category_maps_[col] = {v: i for i, v in enumerate(cats)}
                df[col] = df[col].astype(str).where(df[col].notna(), np.nan).map(self.category_maps_[col])

        target = df.pop(self.target_name)

        # 3) 缺失填充：数值 KNN，并记录列均值兜底
        self.feature_columns_ = df.columns.tolist()
        for col in df.columns:
            self.impute_values_[col] = float(df[col].mean()) if df[col].notna().any() else 0.0
        imputer = KNNImputer(n_neighbors=5)
        df = pd.DataFrame(imputer.fit_transform(df), columns=self.feature_columns_)

        # 4) 共线性处理（可选）：高相关列用 PCA 融合
        if self.solve_collinearity:
            self.collinear_cols_ = _calc_drop_by_corr(df, COLLINEARITY_CUTOFF)
            df = self._apply_pca_fit(df)

        # 5) 缩放
        self.scaler_ = RobustScaler() if self.use_robust_scaler else StandardScaler()
        df = pd.DataFrame(self.scaler_.fit_transform(df), columns=df.columns)

        self.feature_columns_ = df.columns.tolist()
        self._fitted = True
        return df, target

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise RuntimeError("Preprocessor 尚未 fit。")
        df = df.replace("", np.nan).copy()

        # 类别编码（沿用训练映射；未见过的取值置空，随后被填充）
        for col, mapping in self.category_maps_.items():
            if col in df.columns:
                df[col] = df[col].astype(str).where(df[col].notna(), np.nan).map(mapping)

        # 仅保留训练时用过的原始特征列，缺列补 NaN
        base_cols = list(self.impute_values_.keys())
        for col in base_cols:
            if col not in df.columns:
                df[col] = np.nan
        df = df[base_cols]

        # 用训练时记录的均值填充（transform 阶段不重新学习）
        df = df.fillna(value=self.impute_values_)

        if self.solve_collinearity and self.pca_ is not None:
            df = self._apply_pca_transform(df)

        df = pd.DataFrame(self.scaler_.transform(df), columns=df.columns)
        return df[self.feature_columns_]

    # --- PCA 融合内部实现 ---
    def _apply_pca_fit(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.collinear_cols_:
            return df
        block = df[self.collinear_cols_]
        self.pca_ = PCA(n_components=len(self.collinear_cols_))
        comps = self.pca_.fit_transform(block)
        df = df.drop(columns=self.collinear_cols_).reset_index(drop=True)
        pcadf = pd.DataFrame(comps, columns=[f"pca{i}" for i in range(comps.shape[1])])
        return pd.concat([df, pcadf], axis=1)

    def _apply_pca_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        block = df[self.collinear_cols_]
        comps = self.pca_.transform(block)
        df = df.drop(columns=self.collinear_cols_).reset_index(drop=True)
        pcadf = pd.DataFrame(comps, columns=[f"pca{i}" for i in range(comps.shape[1])])
        return pd.concat([df, pcadf], axis=1)
