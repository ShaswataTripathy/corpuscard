from pathlib import Path

import pytest

from corpuscard.loader import load_manifest
from corpuscard.render_ab2013 import render_ab2013

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_manifest.yaml"


def test_ab2013_raises_clear_error_when_block_missing():
    summary = load_manifest(EXAMPLE)
    summary.ab2013 = None
    with pytest.raises(ValueError, match="no 'ab2013' block"):
        render_ab2013(summary)


def test_ab2013_covers_all_twelve_numbered_items():
    summary = load_manifest(EXAMPLE)
    disclosure = render_ab2013(summary)
    for i in range(1, 13):
        assert f"## {i}. " in disclosure, f"missing item {i}"


def test_ab2013_reflects_ip_status_and_personal_information_flags():
    summary = load_manifest(EXAMPLE)
    disclosure = render_ab2013(summary)
    assert "Includes copyrighted content: Yes" in disclosure
    assert "Includes trademarked content: No" in disclosure
    assert "## 7. Whether datasets include personal information\n\nNo" in disclosure


def test_ab2013_reuses_base_manifest_data_for_overlapping_items():
    summary = load_manifest(EXAMPLE)
    disclosure = render_ab2013(summary)
    # item 1 (sources) and item 3 (data point counts) come from the base
    # manifest, not the ab2013 block - confirm they're actually populated.
    assert "Common Crawl" in disclosure
    assert "1 billion to 10 trillion tokens" in disclosure
