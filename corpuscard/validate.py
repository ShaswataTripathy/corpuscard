"""
Lightweight completeness checks beyond what pydantic's schema already
enforces - the kind of thing a provider would otherwise catch only when a
rightsholder, downstream provider, or the AI Office actually reads the
published Summary.

This is deliberately conservative: it flags gaps a human should look at, it
does not (and cannot) tell you whether your Summary is legally sufficient.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .schema import (
    AUDIO_VIDEO_SIZE_RANGES,
    IMAGE_SIZE_RANGES,
    TEXT_SIZE_RANGES,
    Modality,
    TrainingSummary,
)

_OPEN_ENDED_BIN_BY_MODALITY = {
    Modality.TEXT: TEXT_SIZE_RANGES[-1],
    Modality.IMAGE: IMAGE_SIZE_RANGES[-1],
    Modality.AUDIO: AUDIO_VIDEO_SIZE_RANGES[-1],
    Modality.VIDEO: AUDIO_VIDEO_SIZE_RANGES[-1],
}
_MIN_CONTENT_DESCRIPTION_WORDS = 4


@dataclass
class Finding:
    level: str  # "error" | "warning"
    section: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.section}: {self.message}"


def parse_last_update(value: str) -> date | None:
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def validate(summary: TrainingSummary, *, today: date | None = None) -> list[Finding]:
    findings: list[Finding] = []
    today = today or date.today()

    ds = summary.data_sources
    gi = summary.general_information

    # A 2026 Trinity College Dublin / Mozilla Foundation audit of filed EU
    # Article 53 summaries found that nearly every provider picked the
    # largest, open-ended size bin ("more than 10 trillion tokens", etc.),
    # making the disclosures useless for comparison, and that vague content
    # descriptions were common even where the template boxes were "complete."
    # These two checks nudge toward the kind of specificity that actually
    # distinguished the summaries that passed quality review.
    for m in gi.modalities:
        open_ended_bin = _OPEN_ENDED_BIN_BY_MODALITY.get(m.modality)
        if open_ended_bin and m.size_range == open_ended_bin and not m.custom_size_value:
            findings.append(
                Finding(
                    "warning",
                    "1.3",
                    f"{m.modality.value}: size_range is the largest open-ended bin ('{open_ended_bin}') "
                    "with no custom_size_value given - this is the least informative disclosure choice; "
                    "consider reporting a more specific figure via custom_size_value/custom_size_unit.",
                )
            )
        if len(m.types_of_content.split()) < _MIN_CONTENT_DESCRIPTION_WORDS:
            findings.append(
                Finding(
                    "warning",
                    "1.3",
                    f"{m.modality.value}: types_of_content ('{m.types_of_content}') is very short - "
                    "a more specific description is more useful to rightsholders and less likely to "
                    "read as boilerplate.",
                )
            )

    if ds.publicly_available_datasets.used and not ds.publicly_available_datasets.large_datasets:
        findings.append(
            Finding(
                "warning",
                "2.1",
                "publicly_available_datasets.used is True but large_datasets is empty - "
                "confirm there really are no datasets exceeding the 'large' threshold "
                "(>3% of a modality's total public-dataset size), or list them.",
            )
        )

    if ds.crawled_data.crawlers_used and not (ds.crawled_data.top_domains_summary or ds.crawled_data.top_domains_file):
        findings.append(
            Finding(
                "error",
                "2.3",
                "crawlers_used is True but neither top_domains_summary nor top_domains_file is set - "
                "the template requires a summary of the top 10% of domains crawled by content volume "
                "(top 5% or top 1000, whichever lower, for SMEs).",
            )
        )

    if ds.crawled_data.crawlers_used and not ds.crawled_data.collection_period_start:
        findings.append(
            Finding("warning", "2.3", "crawlers_used is True but collection_period_start is not set.")
        )

    if (ds.user_data.model_interaction_data_used or ds.user_data.other_product_interaction_data_used) and not (
        ds.user_data.services_or_products_description or ds.user_data.modalities_covered
    ):
        findings.append(
            Finding(
                "warning",
                "2.4",
                "User-interaction data is flagged as used but neither services_or_products_description "
                "nor modalities_covered is set - describe what data/modality this covers.",
            )
        )

    if ds.synthetic_data.used and not (
        ds.synthetic_data.generating_models or ds.synthetic_data.other_generating_models_description
    ):
        findings.append(
            Finding(
                "warning",
                "2.5",
                "synthetic_data.used is True but no generating model is named - the template requires "
                "naming the general-purpose AI model(s) used to generate the synthetic data, where known.",
            )
        )

    last_update = parse_last_update(summary.last_update)
    if last_update is None:
        findings.append(
            Finding("warning", "header", f"last_update '{summary.last_update}' is not in DD/MM/YY or DD/MM/YYYY format.")
        )
    else:
        age_days = (today - last_update).days
        if age_days > 183:
            findings.append(
                Finding(
                    "warning",
                    "header",
                    f"last_update is {age_days} days ago. The Summary should be updated at least at "
                    "six-month intervals, or sooner if additional training data requires a materially "
                    "significant update (Explanatory Notice, point 29).",
                )
            )

    market_date_before_2025_08_02 = None
    try:
        parsed = datetime.strptime(
            summary.general_information.model_identification.date_of_placement_on_union_market, "%d/%m/%Y"
        ).date()
        market_date_before_2025_08_02 = parsed < date(2025, 8, 2)
    except ValueError:
        pass

    if market_date_before_2025_08_02:
        findings.append(
            Finding(
                "warning",
                "1.2",
                "Model was placed on the Union market before 2025-08-02: the Summary must be published "
                "no later than 2027-08-02. If any required information cannot be obtained despite best "
                "efforts, state and justify the gap explicitly rather than leaving fields blank.",
            )
        )

    return findings
