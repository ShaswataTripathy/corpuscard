from pathlib import Path

from corpuscard.diff import diff_summaries
from corpuscard.loader import load_manifest
from corpuscard.schema import PubliclyAvailableDataset

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_manifest.yaml"


def _find(changes, kind, path_contains):
    return [c for c in changes if c.kind == kind and path_contains in c.path]


def test_no_diff_between_identical_manifests():
    old = load_manifest(EXAMPLE)
    new = load_manifest(EXAMPLE)
    assert diff_summaries(old, new) == []


def test_diff_detects_scalar_change():
    old = load_manifest(EXAMPLE)
    new = load_manifest(EXAMPLE)
    new.last_update = "01/03/2027"
    changes = diff_summaries(old, new)
    match = _find(changes, "changed", "last_update")
    assert len(match) == 1
    assert match[0].old == "14/09/2026"
    assert match[0].new == "01/03/2027"


def test_diff_detects_added_dataset_by_key_not_index():
    old = load_manifest(EXAMPLE)
    new = load_manifest(EXAMPLE)
    new.data_sources.publicly_available_datasets.large_datasets.append(
        PubliclyAvailableDataset(identifier_or_name="New Corpus", link="https://example.com/new-corpus")
    )
    changes = diff_summaries(old, new)
    match = _find(changes, "added", "large_datasets[identifier_or_name=New Corpus]")
    assert len(match) == 1


def test_diff_detects_nested_change_inside_keyed_list_entry():
    old = load_manifest(EXAMPLE)
    new = load_manifest(EXAMPLE)
    for m in new.general_information.modalities:
        if m.modality.value == "text":
            m.size_range = "More than 10 trillion tokens"
    changes = diff_summaries(old, new)
    match = _find(changes, "changed", "modalities[modality=text].size_range")
    assert len(match) == 1
    assert match[0].new == "More than 10 trillion tokens"


def test_diff_detects_boolean_flip():
    old = load_manifest(EXAMPLE)
    new = load_manifest(EXAMPLE)
    new.data_sources.crawled_data.crawlers_used = False
    changes = diff_summaries(old, new)
    match = _find(changes, "changed", "crawled_data.crawlers_used")
    assert len(match) == 1
    assert match[0].old is True and match[0].new is False
