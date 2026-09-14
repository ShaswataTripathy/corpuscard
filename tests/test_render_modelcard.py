from pathlib import Path

from corpuscard.loader import load_manifest
from corpuscard.render_modelcard import render_model_card

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_manifest.yaml"


def test_model_card_contains_expected_sections():
    summary = load_manifest(EXAMPLE)
    card = render_model_card(summary)
    assert "# Model Card for Acme-Base-70B-v1.2" in card
    assert "## Model Details" in card
    assert "## Training Data" in card
    assert "Acme AI Ltd" in card
    # Sections corpuscard has no data for should say so, not fabricate content.
    assert "Not covered by corpuscard" in card


def test_model_card_includes_license_and_summary_link():
    summary = load_manifest(EXAMPLE)
    card = render_model_card(summary, license="apache-2.0", summary_url="https://acme-ai.example/summary")
    assert "license: apache-2.0" in card
    assert "https://acme-ai.example/summary" in card


def test_model_card_mentions_publicly_available_datasets():
    summary = load_manifest(EXAMPLE)
    card = render_model_card(summary)
    assert "Common Crawl" in card
