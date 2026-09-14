"""Loads a TrainingSummary from a YAML or JSON manifest file."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .schema import TrainingSummary


def load_manifest(path: str | Path) -> TrainingSummary:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(text)
    elif path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported manifest extension: {path.suffix} (use .yaml, .yml, or .json)")
    return TrainingSummary.model_validate(data)
