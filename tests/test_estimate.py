from corpuscard.estimate import estimate_image_count, estimate_text_tokens, suggest_manifest_snippet


def test_estimate_text_tokens_counts_words_and_files(tmp_path):
    (tmp_path / "a.txt").write_text("one two three four five", encoding="utf-8")
    (tmp_path / "b.md").write_text("six seven eight", encoding="utf-8")
    (tmp_path / "ignored.bin").write_bytes(b"\x00\x01")

    result = estimate_text_tokens([str(tmp_path)])

    assert result.file_count == 2
    assert result.word_count == 8
    assert result.size_range == "Less than 1 billion tokens"
    assert result.method in ("heuristic", "tiktoken")


def test_estimate_image_count(tmp_path):
    for name in ("a.jpg", "b.png", "c.txt"):
        (tmp_path / name).write_bytes(b"\x00")

    result = estimate_image_count([str(tmp_path)])
    assert result.file_count == 2
    assert result.size_range == "Less than 1 million images"


def test_suggest_manifest_snippet_includes_both_modalities():
    text = estimate_text_tokens([])
    image = estimate_image_count([])
    snippet = suggest_manifest_snippet(text, image)
    assert "modality: text" in snippet
    assert "modality: image" in snippet


def test_suggest_manifest_snippet_omits_modality_when_none_given():
    text = estimate_text_tokens([])
    snippet = suggest_manifest_snippet(text, None)
    assert "modality: text" in snippet
    assert "modality: image" not in snippet
