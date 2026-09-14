"""
Estimate modality sizes from real files on disk, and bin them into the
manifest's fixed size ranges — so filling in Section 1.3 doesn't require
hand-counting a corpus.

Token counting uses `tiktoken` if installed (`pip install corpuscard[estimate]`)
for an accurate count; otherwise it falls back to a word-count heuristic
(~1.3 tokens per English word) and says so in the result, so a caller always
knows which method produced a number.

This only counts files it can see locally — audio/video duration estimation
is out of scope (it would need a media-probing dependency like ffprobe, which
is a heavier ask than this package wants to carry) and is left as a manual
field in the manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .schema import IMAGE_SIZE_RANGES, TEXT_SIZE_RANGES

TEXT_EXTENSIONS = {".txt", ".md", ".rst", ".jsonl", ".json", ".csv", ".tsv"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}


def _collect_files(paths: list[str | Path], extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_file():
            if p.suffix.lower() in extensions:
                files.append(p)
        elif p.is_dir():
            files.extend(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in extensions)
    return files


def _bin(value: int, thresholds: tuple[int, int], ranges: list[str]) -> str:
    low, high = thresholds
    if value < low:
        return ranges[0]
    if value < high:
        return ranges[1]
    return ranges[2]


@dataclass
class TextEstimate:
    file_count: int
    word_count: int
    estimated_tokens: int
    size_range: str
    method: str  # "tiktoken" | "heuristic"


def estimate_text_tokens(paths: list[str | Path], *, encoding_name: str = "cl100k_base") -> TextEstimate:
    files = _collect_files(paths, TEXT_EXTENSIONS)
    total_words = 0
    total_tokens = 0
    method = "heuristic"

    try:
        import tiktoken  # type: ignore[import-not-found]

        enc = tiktoken.get_encoding(encoding_name)
        method = "tiktoken"
        for f in files:
            text = f.read_text(encoding="utf-8", errors="ignore")
            total_words += len(text.split())
            total_tokens += len(enc.encode(text))
    except ImportError:
        for f in files:
            text = f.read_text(encoding="utf-8", errors="ignore")
            words = len(text.split())
            total_words += words
            total_tokens += round(words * 1.3)

    return TextEstimate(
        file_count=len(files),
        word_count=total_words,
        estimated_tokens=total_tokens,
        size_range=_bin(total_tokens, (1_000_000_000, 10_000_000_000_000), TEXT_SIZE_RANGES),
        method=method,
    )


@dataclass
class ImageEstimate:
    file_count: int
    size_range: str


def estimate_image_count(paths: list[str | Path]) -> ImageEstimate:
    files = _collect_files(paths, IMAGE_EXTENSIONS)
    count = len(files)
    return ImageEstimate(
        file_count=count,
        size_range=_bin(count, (1_000_000, 1_000_000_000), IMAGE_SIZE_RANGES),
    )


def suggest_manifest_snippet(text: TextEstimate | None, image: ImageEstimate | None) -> str:
    """A copy-pasteable YAML fragment for the manifest's `modalities` list."""
    lines = ["modalities:"]
    if text is not None:
        lines += [
            "  - modality: text",
            f"    size_range: \"{text.size_range}\"",
            f"    # estimated {text.estimated_tokens:,} tokens across {text.file_count} files"
            f" (method: {text.method})",
            "    types_of_content: \"TODO: describe the content\"",
        ]
    if image is not None:
        lines += [
            "  - modality: image",
            f"    size_range: \"{image.size_range}\"",
            f"    # {image.file_count} image files found",
            "    types_of_content: \"TODO: describe the content\"",
        ]
    return "\n".join(lines)
