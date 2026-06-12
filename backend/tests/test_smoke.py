"""不依赖 Redis 的纯流程冒烟测试：训练 + 预测，回归与分类各一。"""
from app.ml.pipeline import TrainConfig, predict_pipeline, train_pipeline
from app.ml.models import CLASSIFICATION, REGRESSION
from tests.conftest import make_df


def test_regression_pipeline():
    df = make_df()
    cfg = TrainConfig(task=REGRESSION, target="总价", metric="RMSE", n_trials=2, solve_collinearity=True)
    res = train_pipeline(df, cfg)
    assert res["task"] == REGRESSION
    assert res["metrics"]["test_r2"] > 0.5          # 总价 ~ 单价×面积，应当高度可学
    assert len(res["scatter"]) > 0
    # 预测口径一致（不再对预测集 refit scaler）
    out = predict_pipeline(res["artifact"], df.drop(columns=["总价"]).head(5))
    assert "预测结果" in out.columns and len(out) == 5


def test_classification_pipeline():
    df = make_df()
    cfg = TrainConfig(task=CLASSIFICATION, target="装修", metric="F1", n_trials=2)
    res = train_pipeline(df, cfg)
    assert res["task"] == CLASSIFICATION
    assert "macro_f1" in res["metrics"]
    assert len(res["roc"]) >= 1                      # 每类一条 ROC
    assert all("auc" in c for c in res["roc"])


def test_blend_uses_all_base_models():
    """回归原 bug：第 5 个基模型曾被忽略；现在 base 应包含 4 个且都参与融合。"""
    df = make_df()
    res = train_pipeline(df, TrainConfig(task=REGRESSION, target="总价", n_trials=2))
    base = res["artifact"]["base"]
    assert set(base.keys()) == {"xgb", "lgb", "hist", "aux"}
