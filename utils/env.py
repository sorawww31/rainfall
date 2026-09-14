from dataclasses import dataclass, field
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).parent.parent


@dataclass
class EnvConfig:
    input_dir: str | Path = field(default_factory=lambda: str(_project_root() / "input"))
    output_dir: str | Path = field(default_factory=lambda: str(_project_root() / "outputs"))

    # コード内で書き換わります
    exp_output_dir: str | Path = field(default_factory=lambda: str(_project_root() / "outputs"))
