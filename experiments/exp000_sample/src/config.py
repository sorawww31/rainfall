import os
from dataclasses import dataclass, field
from typing import Optional

from utils.env import EnvConfig


@dataclass
class LgbmParams:
    objective: str = "binary"
    metric: str = "auc"
    boosting_type: str = "gbdt"
    n_estimators: int = 1000
    learning_rate: float = 0.01
    num_leaves: int = 12
    max_depth: int = 4
    min_child_samples: int = 20  # 一つのleafに含まれる最小データ数
    max_bin: int = 255  # 特徴量のbinningの数。大きくすると学習が遅くなるが、精度は上がる傾向にある
    min_child_weight: float = 0.1  # Hessianが小さくなりすぎないようにするためのHessianの最小値
    min_split_gain: float = (
        0.0  # leafを分割する際の最小gain。大きくすると過学習を抑えられるが、学習が進まなくなることもある
    )
    subsample_for_bin: int = 2000  # binningのためのサンプル数。大きくすると学習が遅くなるが、精度は上がる傾向にある
    subsample: float = 0.6  # baggingする時のデータのサンプリングレート
    subsample_freq: int = 3  # baggingを行う頻度。1にすると毎回baggingする。0にするとbaggingしない。 n iterationごとにbaggingする場合はnを指定する。
    colsample_bytree: float = 0.8  # baggingする時の特徴量のサンプリングレート。0.8にすると、毎回80%の特徴量をランダムに選んで学習する。 これは特徴量の割愛になる
    feature_fraction_bynode = 0.9  # nodeごとに特徴量をsampling
    reg_alpha: float = 0.2  # L1正則化の強さ。Gradientの正則化。大きくすると学習が遅くなるが、精度は上がる傾向にある
    reg_lambda: float = 0.1  # 0-1の間で softmax - softmax^2 くらい。 一回の更新を抑える Hessianの正則化。大きくすると学習が遅くなるが、精度は上がる傾向にある


@dataclass
class ExpConfig:
    name: str = ""
    debug: bool = False
    seed: int = 0
    seeds: list[int] = field(default_factory=lambda: [42])

    n_splits: int = 6
    folds: list = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])

    classifier_model: str = "lgbm"
    lgbm_params: LgbmParams = field(default_factory=LgbmParams)
    wandb_project_name: Optional[str] = os.getenv("COMPETITION", "kaggle_template")
    wandb_mode: str = "disabled"

    train_csv_path: str = "competitions/playground-series-s5e3/train.csv"
    test_csv_path: str = "competitions/playground-series-s5e3/test.csv"


@dataclass
class Config:
    env: EnvConfig = field(default_factory=EnvConfig)
    exp: ExpConfig = field(default_factory=ExpConfig)
