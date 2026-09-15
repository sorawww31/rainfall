import os
from dataclasses import dataclass, field
from typing import Optional

from utils.env import EnvConfig


@dataclass
class LgbmParams:
    objective: str = "binary"
    metric: str = "auc"
    n_estimators: int = 3000
    learning_rate: float = 0.01
    num_leaves: int = 31
    max_depth: int = -1
    min_child_samples: int = 20
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_alpha: float = 0.0
    reg_lambda: float = 0.0


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
