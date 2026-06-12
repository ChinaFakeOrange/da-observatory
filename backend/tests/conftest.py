"""测试公用：合成一个带相关性与缺失的小数据集。"""
import random
import pandas as pd


def make_df(n: int = 120, seed: int = 11) -> pd.DataFrame:
    random.seed(seed)
    districts = ["浦东", "徐汇", "静安", "黄浦"]
    deco = ["精装", "简装", "毛坯"]
    base = {"浦东": 6.8, "徐汇": 9.2, "静安": 10.1, "黄浦": 9.8}
    rows = []
    for _ in range(n):
        d = random.choice(districts)
        area = round(52 + abs(random.gauss(0, 1)) * 46, 1)
        age = max(0, round(2 + abs(random.gauss(0, 1)) * 16))
        de = random.choice(deco)
        db = {"毛坯": -0.6, "简装": -0.1, "精装": 0.5}[de]
        unit = max(2.2, round(base[d] + db - age * 0.045 + random.gauss(0, 0.5), 2))
        total = round(unit * area, 1)
        row = {"区域": d, "面积": area, "房龄": age, "装修": de, "单价": unit, "总价": total}
        if random.random() < 0.08:
            row["房龄"] = None
        rows.append(row)
    return pd.DataFrame(rows)
