# Where: tools/download_dataset.py
# What: Kaggle の各種リソースを input/ 配下へダウンロードする CLI。
# Why: datasets / competitions / kernels / models / notebook outputs を一つの入口で安全に取得し、展開後の配置を揃えるため。

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from dotenv import load_dotenv

load_dotenv()

import kagglehub
import kagglehub.clients as kagglehub_clients
import requests
from kagglehub.config import get_cache_folder

RESOURCE_ALIASES = {
    "d": "dataset",
    "dataset": "dataset",
    "datasets": "dataset",
    "c": "competition",
    "competition": "competition",
    "competitions": "competition",
    "k": "kernel",
    "kernel": "kernel",
    "kernels": "kernel",
    "m": "model",
    "model": "model",
    "models": "model",
    "ko": "notebook_output",
    "o": "notebook_output",
    "output": "notebook_output",
    "notebook-output": "notebook_output",
}

KAGGLEHUB_DOWNLOADERS: dict[str, Callable[..., str]] = {
    "dataset": kagglehub.dataset_download,
    "competition": kagglehub.competition_download,
    "model": kagglehub.model_download,
    "notebook_output": kagglehub.notebook_output_download,
}
KAGGLEHUB_CONNECT_TIMEOUT_ENV = "KAGGLEHUB_CONNECT_TIMEOUT_SECONDS"
KAGGLEHUB_READ_TIMEOUT_ENV = "KAGGLEHUB_READ_TIMEOUT_SECONDS"
KAGGLEHUB_MAX_ATTEMPTS_ENV = "KAGGLEHUB_DOWNLOAD_MAX_ATTEMPTS"
KAGGLEHUB_RETRY_WAIT_ENV = "KAGGLEHUB_DOWNLOAD_RETRY_WAIT_SECONDS"
DEFAULT_READ_TIMEOUT_SECONDS = 10
DEFAULT_MAX_ATTEMPTS = 4
DEFAULT_RETRY_WAIT_SECONDS = 5
RETRYABLE_DOWNLOAD_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    TimeoutError,
)


class DownloadRuntimeConfig(NamedTuple):
    connect_timeout_seconds: int
    read_timeout_seconds: int
    max_attempts: int
    retry_wait_seconds: int


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def input_root() -> Path:
    return project_root() / "input"


def parse_env_int(name: str, default: int, *, minimum: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as err:
        raise SystemExit(f"{name} must be an integer, got: {raw_value}") from err
    if value < minimum:
        raise SystemExit(f"{name} must be >= {minimum}, got: {value}")
    return value


def load_download_runtime_config() -> DownloadRuntimeConfig:
    return DownloadRuntimeConfig(
        connect_timeout_seconds=parse_env_int(
            KAGGLEHUB_CONNECT_TIMEOUT_ENV,
            kagglehub_clients.DEFAULT_CONNECT_TIMEOUT,
            minimum=1,
        ),
        read_timeout_seconds=parse_env_int(KAGGLEHUB_READ_TIMEOUT_ENV, DEFAULT_READ_TIMEOUT_SECONDS, minimum=1),
        max_attempts=parse_env_int(KAGGLEHUB_MAX_ATTEMPTS_ENV, DEFAULT_MAX_ATTEMPTS, minimum=1),
        retry_wait_seconds=parse_env_int(KAGGLEHUB_RETRY_WAIT_ENV, DEFAULT_RETRY_WAIT_SECONDS, minimum=0),
    )


def apply_kagglehub_timeouts(config: DownloadRuntimeConfig) -> None:
    # kagglehub 1.0.0 hard-codes a 15s read timeout for resumed downloads.
    kagglehub_clients.DEFAULT_CONNECT_TIMEOUT = config.connect_timeout_seconds
    kagglehub_clients.DEFAULT_READ_TIMEOUT = config.read_timeout_seconds


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Kaggle resources into the repository input/ tree.",
    )
    parser.add_argument(
        "resource",
        help="Resource kind: d(dataset), c(competition), k(kernel), m(model), ko(notebook-output)",
    )
    parser.add_argument("handle", help="Kaggle handle, for example sorawww31/rare-3threshold")
    parser.add_argument(
        "-f",
        "--file",
        dest="resource_path",
        default=None,
        help="Optional file path inside the Kaggle resource.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download and overwrite existing local files.",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        action="store_true",
        help="When resource=k, also generate kernel-metadata.json like `kaggle kernels pull -m`.",
    )
    return parser.parse_args(argv)


def canonical_resource(name: str) -> str:
    try:
        return RESOURCE_ALIASES[name.lower()]
    except KeyError as err:
        supported = ", ".join(sorted(RESOURCE_ALIASES))
        raise SystemExit(f"Unsupported resource '{name}'. Supported aliases: {supported}") from err


def print_equivalent_cli(
    resource: str,
    handle: str,
    resource_path: str | None,
    metadata: bool,
) -> None:
    if resource == "dataset":
        command = ["kaggle", "datasets", "download", handle]
        if resource_path:
            command.extend(["--file", resource_path])
        else:
            command.append("--unzip")
    elif resource == "competition":
        command = ["kaggle", "competitions", "download", handle]
        if resource_path:
            command.extend(["--file", resource_path])
    elif resource == "kernel":
        command = ["kaggle", "kernels", "pull", handle]
        if metadata:
            command.append("--metadata")
    elif resource == "model":
        if len(handle.split("/")) == 5:
            command = ["kaggle", "models", "instances", "versions", "download", handle, "--untar"]
        else:
            command = ["python", "-c", "import kagglehub; kagglehub.model_download(...)"]
    else:
        command = ["kaggle", "kernels", "output", handle]

    print(f"Equivalent command: {shlex.join(command)}")
    if resource in {"competition", "model", "notebook_output"} and resource_path is None:
        print("This wrapper expands archives into input/ automatically.")


def ensure_empty_target(target: Path, force: bool) -> None:
    if not target.exists():
        return
    if not force:
        raise FileExistsError(f"{target} already exists. Re-run with --force to replace it.")
    remove_path(target)


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def mirror_path(source: Path, target: Path, force: bool) -> Path:
    ensure_empty_target(target, force)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=False)
    else:
        shutil.copy2(source, target)
    return target


def _strip_version_path(parts: tuple[str, ...], *, version_index: int, version_marker: str | None) -> tuple[str, ...]:
    # kagglehub caches versioned resources under `versions/<n>` or a bare version folder.
    # The repository tree keeps only the resource root, so we drop that cache-only segment.
    if version_marker is None:
        if len(parts) > version_index:
            return parts[:version_index] + parts[version_index + 1 :]
        return parts

    if len(parts) > version_index + 1 and parts[version_index] == version_marker:
        return parts[:version_index] + parts[version_index + 2 :]
    return parts


def kagglehub_target_path(resource: str, cache_path: Path) -> Path:
    cache_root = Path(get_cache_folder()).resolve()
    relative = cache_path.resolve().relative_to(cache_root)

    if resource == "dataset":
        # kagglehub: datasets/<owner>/<dataset>/versions/<n>/...
        parts = relative.parts
        if len(parts) < 3 or parts[0] != "datasets":
            raise ValueError(f"Unexpected dataset cache layout: {relative}")
        parts = _strip_version_path(parts, version_index=3, version_marker="versions")
        return input_root() / Path(*parts)

    if resource == "competition":
        return input_root() / relative

    if resource == "model":
        # kagglehub: models/<owner>/<model>/<framework>/<variation>/<n>/...
        parts = relative.parts
        if len(parts) < 6 or parts[0] != "models":
            raise ValueError(f"Unexpected model cache layout: {relative}")
        parts = _strip_version_path(parts, version_index=5, version_marker=None)
        return input_root() / Path(*parts)

    if resource == "notebook_output":
        # kagglehub keeps notebook outputs under notebooks/<owner>/<slug>/output/.
        # The repository tree uses input/notebook-outputs/... instead.
        parts = relative.parts
        if len(parts) < 4 or parts[0] != "notebooks" or parts[3] != "output":
            raise ValueError(f"Unexpected notebook output cache layout: {relative}")
        parts = _strip_version_path(parts, version_index=4, version_marker="versions")
        return input_root() / Path("notebook-outputs", *parts[1:3], *parts[4:])

    return input_root() / relative


def download_with_kagglehub(
    resource: str,
    handle: str,
    resource_path: str | None,
    force: bool,
    runtime_config: DownloadRuntimeConfig,
) -> Path:
    apply_kagglehub_timeouts(runtime_config)
    downloader = KAGGLEHUB_DOWNLOADERS[resource]
    # Re-running the same download lets kagglehub resume from the partial archive in cache.
    for attempt in range(1, runtime_config.max_attempts + 1):
        try:
            downloaded = Path(
                downloader(
                    handle,
                    path=resource_path,
                    force_download=force,
                )
            )
            target = kagglehub_target_path(resource, downloaded)
            return mirror_path(downloaded, target, force)
        except RETRYABLE_DOWNLOAD_ERRORS as err:
            if attempt == runtime_config.max_attempts:
                raise
            print(
                "Transient download error on attempt "
                f"{attempt}/{runtime_config.max_attempts}: {err}. "
                f"Retrying in {runtime_config.retry_wait_seconds}s..."
            )
            time.sleep(runtime_config.retry_wait_seconds)

    raise RuntimeError("Unreachable retry state in download_with_kagglehub().")


def parse_owner_and_slug(handle: str) -> tuple[str, str]:
    parts = handle.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"Expected <owner>/<slug> handle, got: {handle}")
    return parts[0], parts[1]


def download_kernel(handle: str, metadata: bool, force: bool) -> Path:
    from kaggle.api.kaggle_api_extended import KaggleApi

    owner, slug = parse_owner_and_slug(handle)
    target_dir = input_root() / "notebooks" / owner / slug
    if force and target_dir.exists():
        remove_path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    api = KaggleApi()
    api.authenticate()
    downloaded = api.kernels_pull(handle, path=str(target_dir), metadata=metadata, quiet=False)
    return Path(downloaded)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    resource = canonical_resource(args.resource)
    runtime_config = load_download_runtime_config()
    if resource == "kernel" and args.resource_path is not None:
        raise SystemExit("--file is not supported for kernel pulls.")
    if resource != "kernel" and args.metadata:
        raise SystemExit("--metadata is only supported when resource=k.")

    print_equivalent_cli(resource, args.handle, args.resource_path, args.metadata)

    if resource == "kernel":
        downloaded_path = download_kernel(args.handle, metadata=args.metadata, force=args.force)
    else:
        downloaded_path = download_with_kagglehub(
            resource=resource,
            handle=args.handle,
            resource_path=args.resource_path,
            force=args.force,
            runtime_config=runtime_config,
        )

    print(f"Downloaded to: {downloaded_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
