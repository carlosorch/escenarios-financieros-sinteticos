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


def _git_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _git_branch() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
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
            "pandas": pd.__version__,
            **_numpy_info(),
            **_torch_info(),
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
