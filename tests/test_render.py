from pathlib import Path

from corpuscard.loader import load_manifest
from corpuscard.render import render_markdown
from corpuscard.validate import validate

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_manifest.yaml"


def test_load_example_manifest():
    summary = load_manifest(EXAMPLE)
    assert summary.general_information.model_identification.versioned_model_names == [
        "Acme-Base-70B-v1.2"
    ]


def test_render_contains_all_section_headings():
    summary = load_manifest(EXAMPLE)
    md = render_markdown(summary)
    for heading in [
        "## 1. General information",
        "### 1.1. Provider identification",
        "### 1.2. Model identification",
        "### 1.3. Modalities, overall training data size and other characteristics",
        "## 2. List of data sources",
        "### 2.1. Publicly available datasets",
        "### 2.2. Private non-publicly available datasets obtained from third parties",
        "### 2.3. Data crawled and scraped from online sources",
        "### 2.4. User data",
        "### 2.5. Synthetic data",
        "### 2.6. Other sources of data",
        "## 3. Data processing aspects",
        "### 3.1. Respect of reservation of rights from text and data mining exception or limitation",
        "### 3.2. Removal of illegal content",
        "### 3.3. Other information (optional)",
    ]:
        assert heading in md, f"missing heading: {heading}"


def test_render_includes_provider_name():
    summary = load_manifest(EXAMPLE)
    md = render_markdown(summary)
    assert "Acme AI Ltd" in md


def test_validate_flags_missing_top_domains():
    summary = load_manifest(EXAMPLE)
    summary.data_sources.crawled_data.top_domains_file = None
    summary.data_sources.crawled_data.top_domains_summary = None
    findings = validate(summary)
    assert any(f.section == "2.3" and f.level == "error" for f in findings)


def test_validate_clean_example_has_no_errors():
    summary = load_manifest(EXAMPLE)
    findings = validate(summary)
    errors = [f for f in findings if f.level == "error"]
    assert errors == []
