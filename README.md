# corpuscard

The card for your training corpus. Generate the EU AI Act **Article 53(1)(d)** public training-data summary — the disclosure every general-purpose AI (GPAI) model provider placing a model on the EU market must publish — from a structured manifest, instead of hand-filling the official form.

```bash
pip install -e .
corpuscard generate examples/example_manifest.yaml -o summary.md
```

That's it — `summary.md` is a narrative-form document matching the [official AI Office template](https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models) section-for-section, ready to publish on your website.

## Why this exists

Article 53(1)(d) of the AI Act requires GPAI providers to publish a "sufficiently detailed summary" of their training content, using a template the AI Office finalized on 2025-07-24. Enforcement started 2026-08-02, with fines up to €15,000,000 or 3% of global annual turnover for non-compliance.

The template asks for **categorical, aggregate disclosure** — what types and rough amounts of data you used, where it came from, how you handled copyright opt-outs — not a document-by-document accounting of your training corpus. That makes it a data-cataloging and documentation problem: something a schema, a manifest file, and a renderer can handle, rather than something that needs to be typed into a web form by hand every time your data mix changes.

This package is exactly that: a typed schema mirroring the template's three sections, a manifest format you fill in once and update as your training data changes, and a set of renderers — the official narrative Summary, a self-contained HTML page, a Hugging Face-style Model Card, a companion copyright-policy page, and a [California AB 2013](#california-ab-2013) disclosure — that all read from the same facts. Plus completeness checks (including two nudges toward the kind of specificity that actually distinguishes a real disclosure from checkbox theater — see below), a diff tool for the six-month update cadence, fleet-wide staleness tracking, and file-based size estimation to help fill the manifest in the first place.

**What this is not:** legal advice, and not a guarantee that your Summary is legally sufficient. It structures the disclosure the template asks for; whether your disclosure is accurate and adequate is still on you and your legal team.

## Usage

### 1. Write a manifest

Copy [`examples/example_manifest.yaml`](examples/example_manifest.yaml) and fill in your own values. Field names and allowed values (e.g. the fixed size-range bins in Section 1.3) follow the official template directly — see [`corpuscard/schema.py`](corpuscard/schema.py) for the full field reference, with each class docstring pointing at the template section it corresponds to.

### 2. Check it before you publish

```bash
corpuscard check manifest.yaml
```

Flags gaps like: crawlers were used but no top-domains summary was given (a required field if `crawlers_used: true`), synthetic data was used but no generating model was named, or the Summary hasn't been updated in over six months (the Explanatory Notice's own update cadence, point 29).

It also flags two things that aren't schema violations but are worth a second look. A 2026 Trinity College Dublin/Mozilla Foundation audit of summaries actually filed under Article 53 found that nearly every provider picked the largest, open-ended size bin ("more than 10 trillion tokens," etc.), making the disclosures useless for comparison, and that content-type descriptions were often vague even where the template boxes were technically complete — Microsoft's Phi-model summary failed the audit's quality review despite being fully filled in. So `check` also warns when a modality picks the top open-ended bin without a `custom_size_value`, and when `types_of_content` reads as boilerplate (under 4 words).

### 3. Generate the Summary

```bash
corpuscard generate manifest.yaml -o summary.md
```

Publish `summary.md` (or paste its content into the AI Office's online form, once available) wherever the template requires — your official website, alongside the model's public distribution channels.

## Other output formats

The same manifest drives several other documents, since a lot of what Article 53 asks for overlaps with things you'd want to publish anyway:

```bash
# A single self-contained HTML page instead of Markdown (Article 53 requires
# publication "on the provider's official website" — HTML is often the more
# direct deliverable). All manifest content is HTML-escaped before embedding.
corpuscard render-html manifest.yaml -o summary.html

# A Hugging Face-style Model Card. The Training Data section is populated
# from the same facts as the Article 53 Summary; sections corpuscard has no
# data for (Uses, Bias/Risks/Limitations, Evaluation, Citation) are left as
# clearly-marked placeholders, not fabricated.
corpuscard render-model-card manifest.yaml --license apache-2.0 --summary-url https://you.example/summary -o MODEL_CARD.md

# A starting point for the separate, smaller Article 53(1)(c) copyright
# policy obligation, built from the same TDM-reservation and
# illegal-content-removal fields already in Section 3 of your manifest.
# The official Summary template explicitly encourages linking to this policy.
corpuscard render-copyright-policy manifest.yaml -o copyright-policy.md
```

## California AB 2013

[AB 2013](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240AB2013) ("Generative Artificial Intelligence: Training Data Transparency," effective 2026-01-01) is a near-twin of Article 53(1)(d): a covered California developer must publicly disclose 12 specific items about their training data. Six of those items are already covered by the base manifest (sources, data-point counts, licensing status, collection time period, synthetic-data use); the other six — intended purpose, IP status, personal-information use, CCPA "aggregate consumer information," data cleaning/processing, and the date first used in development — live in an optional `ab2013:` block (see [`examples/example_manifest.yaml`](examples/example_manifest.yaml) and `CaliforniaAB2013Disclosures` in [`schema.py`](corpuscard/schema.py)).

```bash
corpuscard render-ab2013 manifest.yaml -o ab2013-disclosure.md
```

Leave the `ab2013:` block out of your manifest if AB 2013 doesn't apply to you — `render-ab2013` refuses to render with a clear error rather than silently omitting six of the twelve required items. The output is numbered by statutory item (`## 1.` through `## 12.`) so it's directly auditable against the bill text.

## Keeping a Summary up to date

Article 53 requires republishing at least every six months, or sooner after a "materially significant" training-data change (Explanatory Notice, point 29). Two commands support that workflow:

```bash
# What changed between two manifest versions, before you republish.
corpuscard diff old-manifest.yaml new-manifest.yaml

# Scan a directory of manifests (one per model) and flag which are overdue.
corpuscard status ./manifests/ --fail-on-overdue   # non-zero exit for CI
```

`diff` matches list entries by identity where it can (e.g. datasets by name, modalities by type) rather than by list position, so reordering a list doesn't show up as spurious changes.

## Estimating modality sizes from real files

Filling in Section 1.3's size-range table by hand means counting a corpus yourself. `corpuscard estimate` does that counting for you and prints a ready-to-paste manifest snippet:

```bash
corpuscard estimate --text ./corpus/ --image ./images/
```

Text token counts use [`tiktoken`](https://github.com/openai/tiktoken) if installed (`pip install "corpuscard[estimate]"`) for an accurate count; otherwise it falls back to a word-count heuristic and says so in the output. Audio/video duration isn't estimated — that would need a media-probing dependency this package doesn't want to carry — so those stay manual fields in the manifest.

## Manifest structure

The manifest mirrors the template's three sections:

1. **General information** — provider/model identification, and a table of modality → training-data-size-range → content-type (Section 1.3's fixed bins, e.g. "1 billion to 10 trillion tokens" for text, or a custom value/unit if you'd rather report an exact figure).
2. **List of data sources** — publicly available datasets, licensed third-party datasets, other third-party datasets, crawled/scraped data (including the top-domains disclosure), user-interaction data, synthetic data, and any other source.
3. **Data processing aspects** — how you honour text-and-data-mining opt-outs (Article 4(3), Directive (EU) 2019/790) and how you remove illegal content from training data.

Plus one optional block, `ab2013`, only needed if [California AB 2013](#california-ab-2013) applies to you.

Every field in [`schema.py`](corpuscard/schema.py) is validated with [pydantic](https://docs.pydantic.dev/) — required fields, allowed enum values, and a few structural rules (e.g. "Other" modality requires naming it) are enforced at load time, so a malformed manifest fails fast with a clear error instead of silently producing an incomplete Summary.

## Development

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # .venv/bin/pip on macOS/Linux
pytest
```

## Status

Early — this covers the template as published 2025-07-24. The AI Office has said it may revise the template "in view of practical experience gained" (Explanatory Notice, point 34); if that happens, `schema.py` and `render.py` will need updating to match. PRs welcome, especially from anyone who has actually filed a Summary and found a field this doesn't handle well.

## License

MIT — see [LICENSE](LICENSE).
