import os
from dataclasses import dataclass, field
from typing import Optional

from utils.env import EnvConfig


@dataclass
class ExpConfig:
    name: str = ""
    debug: bool = False
    seed: int = 0
    seeds: list[int] = field(default_factory=lambda: [42])
    learning_rate: float = 0.001
    batch_size: int = 32
    folds: list = field(default_factory=lambda: [0, 1, 2, 3, 4])
    wandb_project_name: Optional[str] = os.getenv("COMPETITION", "kaggle_template")
    wandb_mode: str = "disabled"


@dataclass
class Config:
    env: EnvConfig = field(default_factory=EnvConfig)
    exp: ExpConfig = field(default_factory=ExpConfig)
