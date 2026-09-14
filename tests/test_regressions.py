"""Regression tests for issues found in the 2026-09-14 code review."""

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from corpuscard import estimate as estimate_module
from corpuscard.cli import main as cli_main
from corpuscard.diff import diff_summaries
from corpuscard.loader import load_manifest
from corpuscard.render_modelcard import render_model_card
from corpuscard.schema import Modality, ModalityEntry, ModelIdentification, PubliclyAvailableDataset
from corpuscard.validate import validate

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_manifest.yaml"


# --- cli.py: _load_or_die must not crash on non-ValueError failures ---

def test_cli_check_reports_yaml_syntax_error_instead_of_crashing(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("modalities: [unterminated", encoding="utf-8")
    exit_code = cli_main(["check", str(bad)])
    assert exit_code == 1
    assert "Failed to load manifest" in capsys.readouterr().err


def test_cli_check_reports_missing_file_instead_of_crashing(tmp_path, capsys):
    missing = tmp_path / "does_not_exist.yaml"
    exit_code = cli_main(["check", str(missing)])
    assert exit_code == 1
    assert "Failed to load manifest" in capsys.readouterr().err


# --- schema.py: empty-string size_range must not bypass validation ---

def test_modality_entry_rejects_empty_string_size_range():
    with pytest.raises(ValidationError):
        ModalityEntry(modality=Modality.TEXT, size_range="", types_of_content="text")


def test_model_identification_rejects_empty_model_name_list():
    with pytest.raises(ValidationError):
        ModelIdentification(versioned_model_names=[], date_of_placement_on_union_market="01/01/2026")


# --- diff.py: duplicate keys must not silently collapse entries ---

def test_diff_falls_back_to_index_when_dataset_names_collide():
    old = load_manifest(EXAMPLE)
    new = load_manifest(EXAMPLE)
    dup = PubliclyAvailableDataset(identifier_or_name="Common Crawl (filtered snapshot, 2025-06)", link="https://different-url.example")
    new.data_sources.publicly_available_datasets.large_datasets.append(dup)
    changes = diff_summaries(old, new)
    # With a duplicate key present, matching falls back to index-based diffing
    # rather than key-based matching silently dropping one of the two entries.
    assert any(c.path.startswith("data_sources.publicly_available_datasets.large_datasets[2]") for c in changes)


def test_diff_detects_duplicate_count_change_in_scalar_list():
    old = load_manifest(EXAMPLE)
    new = load_manifest(EXAMPLE)
    old.data_sources.crawled_data.crawler_names = ["AcmeBot/1.0", "AcmeBot/1.0"]
    new.data_sources.crawled_data.crawler_names = ["AcmeBot/1.0"]
    changes = diff_summaries(old, new)
    match = [c for c in changes if c.path == "data_sources.crawled_data.crawler_names"]
    assert len(match) == 1
    assert match[0].kind == "removed"
    assert match[0].old == "AcmeBot/1.0"


# --- validate.py: no literal "%%" in output, new checks fire ---

def test_no_literal_double_percent_in_any_finding_message():
    summary = load_manifest(EXAMPLE)
    summary.data_sources.crawled_data.top_domains_file = None
    summary.data_sources.crawled_data.top_domains_summary = None
    findings = validate(summary)
    assert not any("%%" in f.message for f in findings)


def test_validate_flags_open_ended_bin_without_custom_value():
    summary = load_manifest(EXAMPLE)
    for m in summary.general_information.modalities:
        if m.modality == Modality.TEXT:
            m.size_range = "More than 10 trillion tokens"
    findings = validate(summary)
    assert any("open-ended bin" in f.message for f in findings)


def test_validate_flags_short_content_description():
    summary = load_manifest(EXAMPLE)
    for m in summary.general_information.modalities:
        if m.modality == Modality.IMAGE:
            m.types_of_content = "photos"
    findings = validate(summary)
    assert any("very short" in f.message and "image" in f.message for f in findings)


def test_validate_flags_incomplete_user_data_section():
    summary = load_manifest(EXAMPLE)
    summary.data_sources.user_data.model_interaction_data_used = True
    summary.data_sources.user_data.services_or_products_description = None
    summary.data_sources.user_data.modalities_covered = []
    findings = validate(summary)
    assert any(f.section == "2.4" for f in findings)


# --- estimate.py: any tiktoken failure (not just ImportError) falls back cleanly ---

def test_get_tiktoken_encoder_returns_none_when_setup_raises_non_import_error(monkeypatch):
    import sys
    import types

    fake_tiktoken = types.ModuleType("tiktoken")

    def _broken_get_encoding(name):
        raise RuntimeError("network blocked fetching BPE ranks")

    fake_tiktoken.get_encoding = _broken_get_encoding
    monkeypatch.setitem(sys.modules, "tiktoken", fake_tiktoken)

    assert estimate_module._get_tiktoken_encoder("cl100k_base") is None


def test_estimate_falls_back_to_heuristic_when_encoder_unavailable(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("one two three four", encoding="utf-8")
    monkeypatch.setattr(estimate_module, "_get_tiktoken_encoder", lambda name: None)
    result = estimate_module.estimate_text_tokens([str(tmp_path)])
    assert result.method == "heuristic"
    assert result.word_count == 4


def test_estimate_falls_back_when_encode_call_itself_fails(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("one two three four", encoding="utf-8")

    class _BrokenEncoder:
        def encode(self, text):
            raise RuntimeError("boom")

    monkeypatch.setattr(estimate_module, "_get_tiktoken_encoder", lambda name: _BrokenEncoder())
    result = estimate_module.estimate_text_tokens([str(tmp_path)])
    assert result.method == "heuristic"
    assert result.estimated_tokens == round(4 * 1.3)


# --- render_modelcard.py: multi-line dataset description must not corrupt list formatting ---

def test_model_card_cleans_multiline_dataset_description():
    summary = load_manifest(EXAMPLE)
    summary.data_sources.publicly_available_datasets.large_datasets[0].link = None
    summary.data_sources.publicly_available_datasets.large_datasets[0].description = "line one\n  line two\nline three"
    card = render_model_card(summary)
    assert "line one line two line three" in card
    # every dataset bullet must stay on a single line
    for line in card.splitlines():
        if line.startswith("- ") and "line one" in line:
            assert "line two" in line and "line three" in line
