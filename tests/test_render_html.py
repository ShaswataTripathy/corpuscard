from pathlib import Path

from corpuscard.loader import load_manifest
from corpuscard.render_html import _dt_dd, _esc_modalities, _Raw, render_html
from corpuscard.schema import Modality

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_manifest.yaml"


def test_render_html_contains_headings():
    summary = load_manifest(EXAMPLE)
    html = render_html(summary)
    assert "<h2>1. General information</h2>" in html
    assert "<h2>2. List of data sources</h2>" in html
    assert "<h2>3. Data processing aspects</h2>" in html
    assert "Acme AI Ltd" in html


def test_render_html_escapes_malicious_provider_field():
    summary = load_manifest(EXAMPLE)
    summary.general_information.provider_identification.provider_name_and_contact = "<script>alert(1)</script>"
    html = render_html(summary)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_esc_modalities_returns_raw_marker():
    # Regression guard: _dt_dd only skips escaping for _Raw values. If
    # _esc_modalities ever stops returning _Raw for the non-empty case,
    # its already-escaped output would be escaped a second time.
    result = _esc_modalities([Modality.TEXT, Modality.IMAGE])
    assert isinstance(result, _Raw)
    assert result == "text, image"


def test_dt_dd_does_not_double_escape_raw_values():
    raw = _Raw("A &amp; B")
    output = _dt_dd("term", raw)
    assert "A &amp; B" in output
    assert "&amp;amp;" not in output
