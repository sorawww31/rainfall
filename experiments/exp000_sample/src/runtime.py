# Where: experiments/exp021_dist/src/runtime.py
# What: Shared bootstrap for run.py / notebook / launch.py (cfg compose, output init, logger, wandb, seed loop, DDP setup).
# Why: 3 つの入口で重複していた副作用を 1 箇所に集め、DDP で rank 判定前に副作用が走らないようにする。
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

import wandb
from omegaconf import OmegaConf

from src.config import Config
from src.train import train
from utils.logger import get_logger
from utils.timing import trace


def build_cfg(
    exp_choice: str,
    overrides: list[str] | None = None,
    *,
    config_dir: str | Path,
    config_name: str = "config",
    job_name: str = "notebook",
) -> Config:
    """Hydra compose で cfg を作る。notebook / launch.py から使う。"""
    from hydra import compose, initialize_config_dir

    overrides = list(overrides or [])
    if not any(x.startswith("exp=") for x in overrides):
        overrides = [f"exp={exp_choice}", *overrides]

    with initialize_config_dir(
        version_base=None,
        config_dir=str(config_dir),
        job_name=job_name,
    ):
        cfg = compose(config_name=config_name, overrides=overrides)

    return cast(Config, cfg)


def build_experiment_name(
    experiment_dir_name: str,
    exp_choice: str,
    config_name: str,
) -> str:
    """exp_choice と cfg.exp.name が一致する場合は重複 suffix を付けない。"""
    base_name = f"{experiment_dir_name}/{exp_choice}"
    normalized_config_name = (config_name or "").strip()
    if normalized_config_name in ("", exp_choice):
        return base_name
    return f"{base_name}_{normalized_config_name}"


def init_debug(cfg: Config) -> None:
    """デバッグモードで上書きしたい設定値をまとめて上書きする。"""
    if cfg.exp.debug:
        cfg.exp.name = "debug"
        cfg.exp.seeds = [0, 1]
        cfg.exp.folds = [0]
        cfg.exp.epochs = 2
        cfg.exp.optimizer.batch_size = 25
        cfg.exp.train_only = False


def _init_output_dir(cfg: Config, exp_name: str) -> Path:
    output_dir = Path(cfg.env.output_dir) / exp_name
    cfg.env.exp_output_dir = output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _log_config(cfg: Config, logger: logging.Logger) -> None:
    logger.info(
        "\nConfig: %s",
        json.dumps(OmegaConf.to_container(cfg, resolve=True), default=str, indent=4),
    )


def _save_config(cfg: Config, logger: logging.Logger) -> None:
    config_path = Path(cfg.env.exp_output_dir) / "config.yaml"
    OmegaConf.save(cfg.exp, config_path)
    logger.info(f"Config saved to: {config_path}")



def run_experiment(
    cfg: Config,
    exp_name: str,
    *,
    overrides: list[str] | None = None,
) -> None:
    """run.py / notebookから共通で呼ぶ実験エントリ。
    """

    output_dir = _init_output_dir(cfg, exp_name)
    logger = get_logger(__name__, output_dir)
    logger.info(
        "Start experiment: exp_name=%s, exp_choice=%s, config_name=%s",
        exp_name,
        cfg.exp.name,
        cfg.exp.name,
    )
    _log_config(cfg, logger)
    _save_config(cfg, logger)
    if cfg.exp.debug:
        logger.info("Debug MODE!!!")


    with trace("Finish ALL Tasks", logger):
        for seed in cfg.exp.seeds:
            wandb.init(  # type: ignore[attr-defined]
                project=cfg.exp.wandb_project_name,
                name=f"{exp_name}_{seed}",
                notes=", ".join(overrides or []),
                config=cast(
                    dict[str, Any],
                    OmegaConf.to_container(cfg.exp, resolve=True),
                ),
                mode="disabled" if cfg.exp.debug else cfg.exp.wandb_mode,
            )
            cfg.exp.seed = seed
            with trace(f"Finish Tasks with seed={seed}", logger):
                train(cfg, logger)
            wandb.finish()
