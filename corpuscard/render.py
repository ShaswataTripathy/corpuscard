"""
Renders a TrainingSummary into the narrative Markdown form required by the
Article 53(1)(d) template ("the Summary should be provided in narrative,
simple and effective form" — Explanatory Notice, point 23).

Section headings and order match the official template exactly so a provider
(or a rightsholder checking the published Summary against the template) can
cross-reference the two directly.
"""

from __future__ import annotations

import re

from .schema import Modality, TrainingSummary

_YES_NO = {True: "Yes", False: "No"}
_WHITESPACE_RE = re.compile(r"\s+")


def _yn(value: bool) -> str:
    return _YES_NO[value]


def _clean(text: str) -> str:
    """Collapse YAML block-scalar newlines/indentation into single spaces so
    free-text fields render safely inside Markdown table cells and single lines."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def _opt(value, placeholder: str = "_Not provided._") -> str:
    if value is None or value == "" or value == []:
        return placeholder
    return _clean(value) if isinstance(value, str) else value


def _list(values, placeholder: str = "_Not provided._") -> str:
    if not values:
        return placeholder
    return "\n".join(f"- {_clean(v) if isinstance(v, str) else v}" for v in values)


def _modalities(values) -> str:
    if not values:
        return "_Not provided._"
    return ", ".join(m.value if isinstance(m, Modality) else str(m) for m in values)


def render_markdown(summary: TrainingSummary) -> str:
    s = summary
    gi = s.general_information
    ds = s.data_sources
    dpa = s.data_processing_aspects

    lines: list[str] = []
    a = lines.append

    a("# Template for the Public Summary of Training Content for General-Purpose AI models")
    a("### required by Article 53(1)(d) of Regulation (EU) 2024/1689 (AI Act)")
    a("")
    a(f"**Version of the Summary:** {s.version}")
    a(f"**Last update:** {s.last_update}")
    a("")

    # --- Section 1 ---
    a("## 1. General information")
    a("### 1.1. Provider identification")
    a(f"**Provider name and contact details:** {gi.provider_identification.provider_name_and_contact}")
    a(
        "**Authorised representative name and contact details:** "
        f"{_opt(gi.provider_identification.authorised_representative_name_and_contact, '_Not applicable._')}"
    )
    a("")
    a("### 1.2. Model identification")
    a(f"**Versioned model name(s):** {', '.join(gi.model_identification.versioned_model_names)}")
    a(f"**Model dependencies:** {_opt(gi.model_identification.model_dependencies)}")
    a(f"**Date of placement of the model on the Union market:** {gi.model_identification.date_of_placement_on_union_market}")
    a("")
    a("### 1.3. Modalities, overall training data size and other characteristics")
    a("")
    a("| Modality | Training data size | Types of content |")
    a("|---|---|---|")
    for m in gi.modalities:
        modality_label = m.other_modality_name if m.modality == Modality.OTHER else m.modality.value.capitalize()
        if m.size_range:
            size_label = m.size_range
        else:
            size_label = f"{m.custom_size_value} {m.custom_size_unit}"
        a(f"| {modality_label} | {size_label} | {_clean(m.types_of_content)} |")
    a("")
    a(
        "**Latest date of data acquisition/collection for model training:** "
        f"{gi.latest_data_collection_date} "
        f"(continuously trained on new/dynamic data after this date: {_yn(gi.continuously_trained_on_new_data)})"
    )
    a(f"**Description of the linguistic characteristics of the overall training data:** {_opt(gi.linguistic_characteristics)}")
    a(f"**Other relevant characteristics of the overall training data:** {_opt(gi.other_characteristics)}")
    a(f"**Additional comments:** {_opt(gi.additional_comments)}")
    a("")

    # --- Section 2 ---
    a("## 2. List of data sources")
    a("")
    a("### 2.1. Publicly available datasets")
    pad = ds.publicly_available_datasets
    a(f"**Have you used publicly available datasets to train the model?** {_yn(pad.used)}")
    if pad.used:
        a(f"**Modality(ies) of the content covered:** {_modalities(pad.modalities_covered)}")
        a("**List of large publicly available datasets:**")
        if pad.large_datasets:
            for d in pad.large_datasets:
                ref = d.link if d.link else _opt(d.description, "_No link or description provided._")
                dates = ""
                if d.collection_start_date or d.collection_end_date:
                    dates = f" (collected {d.collection_start_date or 'unknown'} to {d.collection_end_date or 'unknown'})"
                a(f"- {d.identifier_or_name}: {ref}{dates}")
        else:
            a("_Not provided._")
        a(f"**General description of other publicly available datasets not listed above:** {_opt(pad.other_datasets_general_description)}")
        a(f"**Additional comments:** {_opt(pad.additional_comments)}")
    a("")

    a("### 2.2. Private non-publicly available datasets obtained from third parties")
    a("#### 2.2.1. Datasets commercially licensed by rightsholders or their representatives")
    lic = ds.private_third_party_datasets.licensed
    a(f"**Have you concluded transactional commercial licensing agreement(s) with rightsholder(s) or their representatives?** {_yn(lic.has_licensing_agreements)}")
    if lic.has_licensing_agreements:
        a(f"**Modality(ies) of the content covered:** {_modalities(lic.modalities_covered)}")
    a("")
    a("#### 2.2.2. Private datasets obtained from other third parties")
    other3p = ds.private_third_party_datasets.other_third_party
    a(f"**Have you obtained private datasets from other third parties (e.g. data intermediaries) not licensed as in 2.2.1?** {_yn(other3p.obtained)}")
    if other3p.obtained:
        a(f"**Modality(ies) of the content covered:** {_modalities(other3p.modalities_covered)}")
        a("**Publicly known private third-party datasets:**")
        a(_list(other3p.publicly_known_datasets))
        a(f"**General description of non-publicly known private datasets obtained from third parties:** {_opt(other3p.general_description)}")
        a(f"**Additional comments:** {_opt(other3p.additional_comments)}")
    a("")

    a("### 2.3. Data crawled and scraped from online sources")
    cr = ds.crawled_data
    a(f"**Were crawlers used by the provider or on their behalf?** {_yn(cr.crawlers_used)}")
    if cr.crawlers_used:
        a("**Crawler name(s)/identifier(s):**")
        a(_list(cr.crawler_names))
        a(f"**Purposes of the crawler(s):** {_opt(cr.crawler_purposes)}")
        a(f"**General description of crawler behaviour:** {_opt(cr.crawler_behaviour_description)}")
        period = "_Not provided._"
        if cr.collection_period_start or cr.collection_period_end:
            period = f"{cr.collection_period_start or 'unknown'} to {cr.collection_period_end or 'unknown'}"
        a(f"**Period of data collection:** {period}")
        a(f"**Comprehensive description of the type of content and online sources crawled:** {_opt(cr.content_and_sources_description)}")
        a(f"**Type of modality covered:** {_modalities(cr.modalities_covered)}")
        if cr.top_domains_file:
            a(f"**Summary of the most relevant domain names crawled:** see {cr.top_domains_file}")
        else:
            a(f"**Summary of the most relevant domain names crawled:** {_opt(cr.top_domains_summary)}")
        a(f"**Additional comments:** {_opt(cr.additional_comments)}")
    a("")

    a("### 2.4. User data")
    ud = ds.user_data
    a(f"**Was data from user interactions with the AI model (e.g. prompts) used to train the model?** {_yn(ud.model_interaction_data_used)}")
    a(f"**Was data collected from user interactions with the provider's other services/products used to train the model?** {_yn(ud.other_product_interaction_data_used)}")
    if ud.model_interaction_data_used or ud.other_product_interaction_data_used:
        a(f"**General description of the provider's services/products used to collect the user data:** {_opt(ud.services_or_products_description)}")
        a(f"**Type of modality covered:** {_modalities(ud.modalities_covered)}")
        a(f"**Additional comments:** {_opt(ud.additional_comments)}")
    a("")

    a("### 2.5. Synthetic data")
    sd = ds.synthetic_data
    a(f"**Was synthetic AI-generated data created by or on behalf of the provider to train the model?** {_yn(sd.used)}")
    if sd.used:
        a(f"**Modality of the synthetic data:** {_modalities(sd.modalities_covered)}")
        a("**General-purpose AI model(s) used to generate the synthetic data (if on the market):**")
        a(_list(sd.generating_models))
        a(f"**Information about other AI models used to generate synthetic data:** {_opt(sd.other_generating_models_description)}")
        a(f"**Additional comments:** {_opt(sd.additional_comments)}")
    a("")

    a("### 2.6. Other sources of data")
    osd = ds.other_sources
    a(f"**Have data sources other than those described in Sections 2.1 to 2.5 been used to train the model?** {_yn(osd.used)}")
    if osd.used:
        a(f"**Narrative description of these data sources and the data:** {_opt(osd.description)}")
        a(f"**Additional comments:** {_opt(osd.additional_comments)}")
    a("")

    # --- Section 3 ---
    a("## 3. Data processing aspects")
    a("### 3.1. Respect of reservation of rights from text and data mining exception or limitation")
    tdm = dpa.tdm_reservation_respect
    a(
        "**Are you a Signatory to the Code of Practice for general-purpose AI models "
        f"(TDM reservation commitments)?** {_yn(tdm.is_code_of_practice_signatory)}"
    )
    a(f"**Measures implemented to respect reservations of rights from the TDM exception or limitation:** {_opt(tdm.measures_description)}")
    a(f"**Additional comments:** {_opt(tdm.additional_comments)}")
    a("")
    a("### 3.2. Removal of illegal content")
    a(f"**General description of measures taken:** {_opt(dpa.illegal_content_removal.measures_description)}")
    a("")
    a("### 3.3. Other information (optional)")
    a(f"**Other relevant information about data processing aspects:** {_opt(dpa.other_information)}")
    a("")

    return "\n".join(lines)
