"""
Renders a TrainingSummary as a Hugging Face-style Model Card
(https://huggingface.co/docs/hub/model-cards, following the structure
popularized by Mitchell et al., 2019, "Model Cards for Model Reporting").

corpuscard's manifest captures training-data provenance in detail but says
nothing about intended use, evaluation results, or known biases — those
sections are included as clearly-marked placeholders for a human to fill in,
not fabricated.
"""

from __future__ import annotations

from .render import _clean
from .schema import Modality, TrainingSummary

_PLACEHOLDER = "_Not covered by corpuscard — fill in manually._"


def _modalities_str(values) -> str:
    if not values:
        return "unspecified"
    return ", ".join(m.value if isinstance(m, Modality) else str(m) for m in values)


def render_model_card(
    summary: TrainingSummary,
    *,
    license: str | None = None,
    summary_url: str | None = None,
) -> str:
    s = summary
    gi = s.general_information
    ds = s.data_sources

    model_names = ", ".join(gi.model_identification.versioned_model_names)
    modalities_present = [m.modality for m in gi.modalities]

    lines: list[str] = []
    a = lines.append

    a("---")
    if license:
        a(f"license: {license}")
    a(f"tags:")
    for m in modalities_present:
        label = m.value if isinstance(m, Modality) else str(m)
        a(f"  - {label}")
    if gi.linguistic_characteristics:
        a(f"# language: {_clean(gi.linguistic_characteristics)}  # free text — set a proper ISO 639-1 code list manually")
    a("---")
    a("")
    a(f"# Model Card for {model_names}")
    a("")

    a("## Model Details")
    a("")
    a(f"- **Developed by:** {_clean(gi.provider_identification.provider_name_and_contact)}")
    a(f"- **Model type:** {_modalities_str(modalities_present)}")
    if gi.model_identification.model_dependencies:
        a(f"- **Built on:** {_clean(gi.model_identification.model_dependencies)}")
    a(f"- **Date placed on the Union market:** {gi.model_identification.date_of_placement_on_union_market}")
    a("")

    a("## Uses")
    a("")
    a(_PLACEHOLDER)
    a("")

    a("## Bias, Risks, and Limitations")
    a("")
    a(_PLACEHOLDER)
    a("")

    a("## Training Data")
    a("")
    a(
        "This section is generated from the same manifest as this model's EU AI Act "
        "Article 53(1)(d) training-content summary"
        + (f" ([full summary]({summary_url}))" if summary_url else "")
        + ". It reflects categorical disclosure, not a document-level accounting of the training corpus."
    )
    a("")

    pad = ds.publicly_available_datasets
    if pad.used:
        a("**Publicly available datasets:**")
        a("")
        if pad.large_datasets:
            for d in pad.large_datasets:
                ref = d.link or d.description or ""
                a(f"- {d.identifier_or_name}" + (f" — {ref}" if ref else ""))
        if pad.other_datasets_general_description:
            a(f"- Other publicly available datasets: {_clean(pad.other_datasets_general_description)}")
        a("")

    lic = ds.private_third_party_datasets.licensed
    if lic.has_licensing_agreements:
        a(f"**Licensed third-party data:** commercially licensed content covering {_modalities_str(lic.modalities_covered)}.")
        a("")

    o3p = ds.private_third_party_datasets.other_third_party
    if o3p.obtained:
        desc = o3p.general_description or "; ".join(o3p.publicly_known_datasets) or "see full training-content summary."
        a(f"**Other third-party data:** {_clean(desc) if isinstance(desc, str) else desc}")
        a("")

    cr = ds.crawled_data
    if cr.crawlers_used:
        a(
            f"**Web-crawled data:** collected {cr.collection_period_start or 'unknown'}–"
            f"{cr.collection_period_end or 'unknown'}"
            + (f". {_clean(cr.content_and_sources_description)}" if cr.content_and_sources_description else ".")
        )
        a("")

    ud = ds.user_data
    if ud.model_interaction_data_used or ud.other_product_interaction_data_used:
        a("**User-interaction data:** included — see full training-content summary for scope.")
        a("")

    sd = ds.synthetic_data
    if sd.used:
        gen = ", ".join(sd.generating_models) if sd.generating_models else "an unspecified model"
        a(f"**Synthetic data:** generated using {gen}.")
        a("")

    a("## Evaluation")
    a("")
    a(_PLACEHOLDER)
    a("")

    a("## Citation")
    a("")
    a(_PLACEHOLDER)
    a("")

    return "\n".join(lines)
