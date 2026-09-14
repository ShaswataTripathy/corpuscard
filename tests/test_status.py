from datetime import date
from pathlib import Path

from corpuscard.status import scan_directory

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_manifest.yaml"
_TODAY = date(2026, 9, 14)


def _write_variant(tmp_path: Path, filename: str, last_update: str) -> Path:
    text = EXAMPLE.read_text(encoding="utf-8")
    text = text.replace('last_update: "14/09/2026"', f'last_update: "{last_update}"')
    path = tmp_path / filename
    path.write_text(text, encoding="utf-8")
    return path


def test_scan_directory_flags_overdue_and_fresh(tmp_path):
    _write_variant(tmp_path, "fresh.yaml", "01/09/2026")  # 13 days ago
    _write_variant(tmp_path, "stale.yaml", "01/01/2025")  # well over 6 months ago

    results = scan_directory(tmp_path, today=_TODAY)
    by_name = {r.path.name: r for r in results}

    assert len(results) == 2
    assert by_name["fresh.yaml"].overdue is False
    assert by_name["stale.yaml"].overdue is True
    assert by_name["fresh.yaml"].model_names == ["Acme-Base-70B-v1.2"]


def test_scan_directory_reports_load_errors(tmp_path):
    bad = tmp_path / "broken.yaml"
    bad.write_text("this: is not a valid manifest at all", encoding="utf-8")

    results = scan_directory(tmp_path, today=_TODAY)
    assert len(results) == 1
    assert results[0].load_error is not None


def test_scan_directory_ignores_non_manifest_files(tmp_path):
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")
    results = scan_directory(tmp_path, today=_TODAY)
    assert results == []
