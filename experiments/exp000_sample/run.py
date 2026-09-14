# Where: experiments/exp021_dist/run.py
# What: Hydra entrypoint for exp021 training runs; delegates bootstrap to src.runtime.
# Why: DDP 対応 bootstrap を runtime へ寄せ、CLI/notebook/launch.py で責務を共有する。
# ruff: noqa: E402
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリを sys.path に追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "../../")
sys.path.append(os.path.normpath(project_root))

import hydra
from dotenv import load_dotenv
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig
from src.config import Config, ExpConfig
from src.runtime import build_experiment_name, init_debug, run_experiment

from utils.env import EnvConfig  # noqa: E402

load_dotenv()

cs = ConfigStore.instance()
cs.store(name="default", group="env", node=EnvConfig)
cs.store(name="default", group="exp", node=ExpConfig)


@hydra.main(version_base=None, config_path=".", config_name="config")
def main(cfg: Config) -> None:
    init_debug(cfg)
    exp_name = build_experiment_name(
        experiment_dir_name=Path(sys.argv[0]).parent.name,
        exp_choice=HydraConfig.get().runtime.choices["exp"],
        config_name=cfg.exp.name,
    )
    run_experiment(
        cfg,
        exp_name,
        overrides=list(HydraConfig.get().overrides.task),
    )


if __name__ == "__main__":
    main()
