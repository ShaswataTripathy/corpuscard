"""
Fleet-wide freshness tracking: scan a directory of manifests and report which
ones are overdue for their Article 53 update (the Explanatory Notice's own
cadence is at least every six months — point 29).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .loader import load_manifest
from .validate import parse_last_update

_MANIFEST_EXTENSIONS = (".yaml", ".yml", ".json")
_UPDATE_INTERVAL_DAYS = 183


@dataclass
class ManifestStatus:
    path: Path
    model_names: list[str]
    last_update: str
    days_since_update: int | None
    overdue: bool
    load_error: str | None = None


def scan_directory(directory: str | Path, *, today: date | None = None) -> list[ManifestStatus]:
    directory = Path(directory)
    today = today or date.today()
    results: list[ManifestStatus] = []

    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _MANIFEST_EXTENSIONS:
            continue
        try:
            summary = load_manifest(path)
        except Exception as e:  # noqa: BLE001 - report any load failure, not just validation errors
            results.append(
                ManifestStatus(
                    path=path, model_names=[], last_update="", days_since_update=None,
                    overdue=False, load_error=str(e),
                )
            )
            continue

        parsed = parse_last_update(summary.last_update)
        days = (today - parsed).days if parsed else None
        results.append(
            ManifestStatus(
                path=path,
                model_names=summary.general_information.model_identification.versioned_model_names,
                last_update=summary.last_update,
                days_since_update=days,
                overdue=days is not None and days > _UPDATE_INTERVAL_DAYS,
            )
        )

    return results
