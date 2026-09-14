"""
Structural diff between two TrainingSummary manifests — the workflow tool
for the Article 53 update cadence (every 6 months, or sooner after a
"materially significant" training-data change; Explanatory Notice, point 29):
know exactly what changed before republishing.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from .schema import TrainingSummary

_MISSING = object()

# Dotted path -> the field used to match entries when diffing a list of dicts
# at that path, so added/removed/changed items are reported by identity
# rather than by list index.
_LIST_KEY_FIELDS = {
    "general_information.modalities": "modality",
    "data_sources.publicly_available_datasets.large_datasets": "identifier_or_name",
}


@dataclass
class Change:
    kind: str  # "added" | "removed" | "changed"
    path: str
    old: Any = None
    new: Any = None

    def __str__(self) -> str:
        if self.kind == "added":
            return f"+ {self.path}: {self.new!r}"
        if self.kind == "removed":
            return f"- {self.path}: {self.old!r}"
        return f"~ {self.path}: {self.old!r} -> {self.new!r}"


def diff_summaries(old: TrainingSummary, new: TrainingSummary) -> list[Change]:
    old_dict = old.model_dump(mode="json")
    new_dict = new.model_dump(mode="json")
    changes: list[Change] = []
    _diff_dict(old_dict, new_dict, "", changes)
    return changes


def _diff_dict(old: dict, new: dict, path: str, changes: list[Change]) -> None:
    for key in sorted(set(old) | set(new)):
        sub_path = f"{path}.{key}" if path else key
        _diff_value(old.get(key, _MISSING), new.get(key, _MISSING), sub_path, changes)


def _diff_value(old: Any, new: Any, path: str, changes: list[Change]) -> None:
    if old is _MISSING:
        changes.append(Change("added", path, new=new))
        return
    if new is _MISSING:
        changes.append(Change("removed", path, old=old))
        return
    if old == new:
        return
    if isinstance(old, dict) and isinstance(new, dict):
        _diff_dict(old, new, path, changes)
        return
    if isinstance(old, list) and isinstance(new, list):
        _diff_list(old, new, path, changes)
        return
    changes.append(Change("changed", path, old=old, new=new))


def _index_diff(old: list, new: list, path: str, changes: list[Change]) -> None:
    for i in range(max(len(old), len(new))):
        _diff_value(
            old[i] if i < len(old) else _MISSING,
            new[i] if i < len(new) else _MISSING,
            f"{path}[{i}]",
            changes,
        )


def _diff_list(old: list, new: list, path: str, changes: list[Change]) -> None:
    key_field = _LIST_KEY_FIELDS.get(path)
    if key_field and all(isinstance(x, dict) and key_field in x for x in old + new):
        old_keys = [x[key_field] for x in old]
        new_keys = [x[key_field] for x in new]
        # If either side has a duplicate key value, key-based matching can't tell entries
        # apart and would silently collapse them - fall back to index comparison instead.
        if len(set(old_keys)) == len(old_keys) and len(set(new_keys)) == len(new_keys):
            old_by_key = {x[key_field]: x for x in old}
            new_by_key = {x[key_field]: x for x in new}
            for key in sorted(set(old_by_key) | set(new_by_key), key=str):
                _diff_value(
                    old_by_key.get(key, _MISSING),
                    new_by_key.get(key, _MISSING),
                    f"{path}[{key_field}={key}]",
                    changes,
                )
            return
        _index_diff(old, new, path, changes)
        return

    try:
        # Counter, not set: a change in how many times a value repeats (e.g. an
        # accidental duplicate crawler name being fixed) is a real change and
        # should show up, not disappear because sets ignore multiplicity.
        old_counts, new_counts = Counter(old), Counter(new)
    except TypeError:
        # Unhashable items with no configured key field: fall back to index comparison.
        _index_diff(old, new, path, changes)
        return
    for item in sorted((old_counts - new_counts).elements(), key=str):
        changes.append(Change("removed", path, old=item))
    for item in sorted((new_counts - old_counts).elements(), key=str):
        changes.append(Change("added", path, new=item))
