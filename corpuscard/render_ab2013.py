"""
Renders a California AB 2013 ("Generative Artificial Intelligence: Training
Data Transparency", Cal. Bus. & Prof. Code §22757.11 et seq., effective
2026-01-01) disclosure from the same manifest used for the EU Article 53(1)(d)
Summary.

AB 2013 enumerates 12 required disclosure items (Section 3111(a)). Six overlap
directly with fields the base manifest already captures for the EU template;
the other six live in the optional `ab2013` block (see schema.py). This
renderer numbers every section by its statutory item so it's auditable
against the bill text directly.

Raises ValueError if `summary.ab2013` is not set — AB 2013 disclosure can't be
produced without those fields, and silently omitting six of twelve required
items would be worse than refusing to render.
"""

from __future__ import annotations

from .render import _clean, _opt, _yn, modality_list_str
from .schema import TrainingSummary

_PLACEHOLDER = "_Not provided._"


def _collection_periods(summary: TrainingSummary) -> list[str]:
    periods: list[str] = []
    for d in summary.data_sources.publicly_available_datasets.large_datasets:
        if d.collection_start_date or d.collection_end_date:
            periods.append(f"{d.identifier_or_name}: {d.collection_start_date or 'unknown'} to {d.collection_end_date or 'unknown'}")
    cr = summary.data_sources.crawled_data
    if cr.crawlers_used and (cr.collection_period_start or cr.collection_period_end):
        periods.append(f"Crawled data: {cr.collection_period_start or 'unknown'} to {cr.collection_period_end or 'unknown'}")
    return periods


def render_ab2013(summary: TrainingSummary) -> str:
    if summary.ab2013 is None:
        raise ValueError(
            "This manifest has no 'ab2013' block. AB 2013 disclosure needs six fields "
            "(intended purpose, IP status, personal information, aggregate consumer "
            "information, data cleaning, first-used-in-development date) that aren't "
            "part of the base EU Article 53 manifest — add an 'ab2013:' section (see "
            "schema.py: CaliforniaAB2013Disclosures) before rendering."
        )

    s = summary
    gi = s.general_information
    ds = s.data_sources
    ab = s.ab2013

    lines: list[str] = []
    a = lines.append

    a("# California AB 2013 Training Data Transparency Disclosure")
    a("")
    a("Required by Cal. Bus. & Prof. Code Section 3111 (AB 2013), effective 2026-01-01.")
    a("")
    a(f"**Developer:** {_clean(gi.provider_identification.provider_name_and_contact)}")
    a(f"**System(s):** {', '.join(gi.model_identification.versioned_model_names)}")
    a(f"**Published:** {s.last_update}")
    a("")

    a("## 1. Sources or owners of the datasets")
    a("")
    pad = ds.publicly_available_datasets
    if pad.used and pad.large_datasets:
        for d in pad.large_datasets:
            a(f"- {_clean(d.identifier_or_name)}" + (f" ({d.link})" if d.link else ""))
    lic = ds.private_third_party_datasets.licensed
    if lic.has_licensing_agreements:
        a(f"- Commercially licensed third-party content ({modality_list_str(lic.modalities_covered)})")
    o3p = ds.private_third_party_datasets.other_third_party
    if o3p.obtained:
        for name in o3p.publicly_known_datasets:
            a(f"- {_clean(name)}")
        if o3p.general_description:
            a(f"- Other third-party data: {_clean(o3p.general_description)}")
    if ds.crawled_data.crawlers_used:
        a(f"- Web-crawled data ({_clean(ds.crawled_data.content_and_sources_description) if ds.crawled_data.content_and_sources_description else 'see Section 10 for collection period'})")
    a("")

    a("## 2. How the datasets further the intended purpose of the system")
    a("")
    a(_clean(ab.intended_purpose_description))
    a("")

    a("## 3. Number of data points included in the datasets")
    a("")
    a("| Modality | Size |")
    a("|---|---|")
    for m in gi.modalities:
        size_label = m.size_range if m.size_range else f"{m.custom_size_value} {m.custom_size_unit}"
        a(f"| {m.modality.value} | {size_label} |")
    a("")

    a("## 4. Types of data points within the datasets")
    a("")
    for m in gi.modalities:
        a(f"- **{m.modality.value}:** {_clean(m.types_of_content)}")
    a("")

    a("## 5. Intellectual property status")
    a("")
    ip = ab.ip_status
    a(f"- Includes copyrighted content: {_yn(ip.includes_copyrighted_content)}")
    a(f"- Includes trademarked content: {_yn(ip.includes_trademarked_content)}")
    a(f"- Includes patented content: {_yn(ip.includes_patented_content)}")
    a(f"- Includes public domain content: {_yn(ip.includes_public_domain_content)}")
    if ip.additional_comments:
        a(f"- Additional comments: {_clean(ip.additional_comments)}")
    a("")

    a("## 6. Whether datasets were purchased or licensed")
    a("")
    a(f"{_yn(lic.has_licensing_agreements)}" + (f" ({modality_list_str(lic.modalities_covered)})" if lic.has_licensing_agreements else ""))
    a("")

    a("## 7. Whether datasets include personal information")
    a("")
    a(_yn(ab.includes_personal_information))
    a("")

    a("## 8. Whether datasets include aggregate consumer information (as defined by the CCPA)")
    a("")
    a(_yn(ab.includes_aggregate_consumer_information))
    a("")

    a("## 9. Cleaning, processing, or other modification of the datasets")
    a("")
    a(_opt(ab.data_cleaning_description, _PLACEHOLDER))
    a("")

    a("## 10. Time period during which the data was collected")
    a("")
    periods = _collection_periods(summary)
    if periods:
        for p in periods:
            a(f"- {p}")
    else:
        a(_PLACEHOLDER)
    a("")

    a("## 11. Date(s) the datasets were first used during development")
    a("")
    a(_opt(ab.first_used_in_development_date, _PLACEHOLDER))
    a("")

    a("## 12. Use of synthetic data generation")
    a("")
    sd = ds.synthetic_data
    if sd.used:
        continuous_note = (
            " Training continues on new/dynamic data after the latest collection date, "
            "which may include ongoing synthetic data generation."
            if gi.continuously_trained_on_new_data
            else " Not reported as continuous."
        )
        a(f"Yes.{continuous_note}")
    else:
        a("No.")
    a("")

    return "\n".join(lines)
