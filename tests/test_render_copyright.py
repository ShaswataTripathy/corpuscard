from pathlib import Path

from corpuscard.loader import load_manifest
from corpuscard.render_copyright import render_copyright_policy

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_manifest.yaml"


def test_copyright_policy_uses_tdm_measures():
    summary = load_manifest(EXAMPLE)
    policy = render_copyright_policy(summary)
    assert "# Copyright Policy" in policy
    assert "TDM reservation opt-out protocol" in policy
    assert "signatory to the Code of Practice" in policy


def test_copyright_policy_falls_back_to_placeholder_when_measures_missing():
    summary = load_manifest(EXAMPLE)
    summary.data_processing_aspects.tdm_reservation_respect.measures_description = None
    policy = render_copyright_policy(summary)
    assert "Not covered by corpuscard" in policy
