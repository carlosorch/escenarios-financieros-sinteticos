from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ExperimentConfig


def _repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for path in (current, *current.parents):
        if (path / ".git").exists():
            return path
    return None


def _git_revision() -> str | None:
    repo_root = _repo_root()
    if repo_root is None:
        return None

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _git_branch() -> str | None:
    repo_root = _repo_root()
    if repo_root is None:
        return None

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _torch_info() -> dict[str, Any]:
    try:
        import torch

        return {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda,
            "mps_available": torch.backends.mps.is_available(),
            "mps_built": torch.backends.mps.is_built(),
        }
    except Exception:
        return {}


def _numpy_info() -> dict[str, Any]:
    try:
        import numpy as np

        return {"version": np.__version__}
    except Exception:
        return {}


def build_metadata(
    config: ExperimentConfig,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a serialisable metadata dict for an experiment run."""
    metadata: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "git_revision": _git_revision(),
        "git_branch": _git_branch(),
        "config": {
            field.name: getattr(config, field.name)
            for field in config.__dataclass_fields__.values()
        },
        "libraries": {
            "pandas": {"version": pd.__version__},
            "numpy": _numpy_info(),
            "torch": _torch_info(),
        },
    }
    if extra:
        metadata["extra"] = extra
    return metadata


def write_metadata(
    output_dir: Path,
    config: ExperimentConfig,
    extra: dict[str, Any] | None = None,
) -> None:
    """Write metadata.json into output_dir."""
    metadata = build_metadata(config, extra=extra)
    with (output_dir / "metadata.json").open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, default=str)
