"""
Renders a TrainingSummary as a single self-contained HTML page - the format
the template actually asks for publication in ("on the provider's official
website"), as an alternative to the Markdown output in render.py.

All user-supplied free text is HTML-escaped; this module does not trust
manifest content to be safe to embed verbatim.
"""

from __future__ import annotations

from html import escape

from .render import _clean, _yn, modality_list_str
from .schema import Modality, TrainingSummary

_STYLE = """
body { font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif; max-width: 860px;
       margin: 2rem auto; padding: 0 1.25rem; line-height: 1.55; color: #1a1a1a; }
h1 { font-size: 1.5rem; }
h2 { border-bottom: 1px solid #ddd; padding-bottom: .25rem; margin-top: 2.25rem; }
h3 { margin-top: 1.5rem; }
h4 { margin-top: 1.25rem; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { border: 1px solid #ccc; padding: .5rem .6rem; text-align: left; vertical-align: top; }
th { background: #f4f4f4; }
dt { font-weight: 600; margin-top: .75rem; }
dd { margin: .15rem 0 0; }
.meta { color: #555; font-size: .9rem; }
.placeholder { color: #888; font-style: italic; }
"""


class _Raw(str):
    """Marks a string as already-safe HTML so _dt_dd doesn't escape it again."""


_PLACEHOLDER = _Raw('<span class="placeholder">Not provided.</span>')


def _esc(value) -> str:
    if value is None or value == "" or value == []:
        return _PLACEHOLDER
    if isinstance(value, str):
        return escape(_clean(value)).replace("\n", "<br>")
    return escape(str(value))


def _esc_list(values) -> _Raw:
    if not values:
        return _PLACEHOLDER
    items = "".join(f"<li>{escape(_clean(v)) if isinstance(v, str) else escape(str(v))}</li>" for v in values)
    return _Raw(f"<ul>{items}</ul>")


def _esc_modalities(values) -> _Raw:
    if not values:
        return _PLACEHOLDER
    return _Raw(escape(modality_list_str(values)))


def _dt_dd(term: str, value) -> str:
    rendered = value if isinstance(value, _Raw) else _esc(value)
    return f"<dt>{escape(term)}</dt><dd>{rendered}</dd>"


def render_html(summary: TrainingSummary) -> str:
    s = summary
    gi = s.general_information
    ds = s.data_sources
    dpa = s.data_processing_aspects

    parts: list[str] = []
    a = parts.append

    a("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">")
    a("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
    a(f"<title>Training Content Summary - {escape(', '.join(gi.model_identification.versioned_model_names))}</title>")
    a(f"<style>{_STYLE}</style></head><body>")

    a("<h1>Template for the Public Summary of Training Content for General-Purpose AI models</h1>")
    a("<p class=\"meta\">Required by Article 53(1)(d) of Regulation (EU) 2024/1689 (AI Act)</p>")
    a(f"<p class=\"meta\"><strong>Version:</strong> {escape(s.version)} &nbsp;|&nbsp; <strong>Last update:</strong> {escape(s.last_update)}</p>")

    a("<h2>1. General information</h2>")
    a("<h3>1.1. Provider identification</h3><dl>")
    a(_dt_dd("Provider name and contact details", gi.provider_identification.provider_name_and_contact))
    a(_dt_dd("Authorised representative", gi.provider_identification.authorised_representative_name_and_contact))
    a("</dl>")

    a("<h3>1.2. Model identification</h3><dl>")
    a(_dt_dd("Versioned model name(s)", ", ".join(gi.model_identification.versioned_model_names)))
    a(_dt_dd("Model dependencies", gi.model_identification.model_dependencies))
    a(_dt_dd("Date of placement on the Union market", gi.model_identification.date_of_placement_on_union_market))
    a("</dl>")

    a("<h3>1.3. Modalities, overall training data size and other characteristics</h3>")
    a("<table><thead><tr><th>Modality</th><th>Training data size</th><th>Types of content</th></tr></thead><tbody>")
    for m in gi.modalities:
        modality_label = m.other_modality_name if m.modality == Modality.OTHER else m.modality.value.capitalize()
        size_label = m.size_range if m.size_range else f"{m.custom_size_value} {m.custom_size_unit}"
        a(f"<tr><td>{escape(modality_label)}</td><td>{escape(size_label)}</td><td>{_esc(m.types_of_content)}</td></tr>")
    a("</tbody></table>")
    a("<dl>")
    a(_dt_dd(
        "Latest date of data acquisition/collection",
        _Raw(f"{escape(gi.latest_data_collection_date)} (continuously trained on new/dynamic data after this date: {_yn(gi.continuously_trained_on_new_data)})"),
    ))
    a(_dt_dd("Linguistic characteristics", gi.linguistic_characteristics))
    a(_dt_dd("Other characteristics", gi.other_characteristics))
    a(_dt_dd("Additional comments", gi.additional_comments))
    a("</dl>")

    a("<h2>2. List of data sources</h2>")

    a("<h3>2.1. Publicly available datasets</h3><dl>")
    pad = ds.publicly_available_datasets
    a(_dt_dd("Used publicly available datasets?", _yn(pad.used)))
    if pad.used:
        a(_dt_dd("Modality(ies) covered", _esc_modalities(pad.modalities_covered)))
        rows = []
        for d in pad.large_datasets:
            ref = d.link or d.description or "No link or description provided."
            dates = f" (collected {d.collection_start_date or 'unknown'} to {d.collection_end_date or 'unknown'})" if (d.collection_start_date or d.collection_end_date) else ""
            rows.append(f"{d.identifier_or_name}: {ref}{dates}")
        a(_dt_dd("List of large publicly available datasets", _esc_list(rows)))
        a(_dt_dd("Other publicly available datasets (general description)", pad.other_datasets_general_description))
        a(_dt_dd("Additional comments", pad.additional_comments))
    a("</dl>")

    a("<h3>2.2. Private non-publicly available datasets obtained from third parties</h3>")
    a("<h4>2.2.1. Datasets commercially licensed by rightsholders or their representatives</h4><dl>")
    lic = ds.private_third_party_datasets.licensed
    a(_dt_dd("Licensing agreements concluded?", _yn(lic.has_licensing_agreements)))
    if lic.has_licensing_agreements:
        a(_dt_dd("Modality(ies) covered", _esc_modalities(lic.modalities_covered)))
    a("</dl>")
    a("<h4>2.2.2. Private datasets obtained from other third parties</h4><dl>")
    o3p = ds.private_third_party_datasets.other_third_party
    a(_dt_dd("Private datasets obtained from other third parties?", _yn(o3p.obtained)))
    if o3p.obtained:
        a(_dt_dd("Modality(ies) covered", _esc_modalities(o3p.modalities_covered)))
        a(_dt_dd("Publicly known datasets", _esc_list(o3p.publicly_known_datasets)))
        a(_dt_dd("General description", o3p.general_description))
        a(_dt_dd("Additional comments", o3p.additional_comments))
    a("</dl>")

    a("<h3>2.3. Data crawled and scraped from online sources</h3><dl>")
    cr = ds.crawled_data
    a(_dt_dd("Crawlers used?", _yn(cr.crawlers_used)))
    if cr.crawlers_used:
        a(_dt_dd("Crawler name(s)/identifier(s)", _esc_list(cr.crawler_names)))
        a(_dt_dd("Purposes of the crawler(s)", cr.crawler_purposes))
        a(_dt_dd("Crawler behaviour", cr.crawler_behaviour_description))
        period = f"{cr.collection_period_start or 'unknown'} to {cr.collection_period_end or 'unknown'}" if (cr.collection_period_start or cr.collection_period_end) else None
        a(_dt_dd("Period of data collection", period))
        a(_dt_dd("Content and sources crawled", cr.content_and_sources_description))
        a(_dt_dd("Type of modality covered", _esc_modalities(cr.modalities_covered)))
        domains = _Raw(f'<a href="{escape(cr.top_domains_file)}">{escape(cr.top_domains_file)}</a>') if cr.top_domains_file else cr.top_domains_summary
        a(_dt_dd("Summary of the most relevant domain names crawled", domains))
        a(_dt_dd("Additional comments", cr.additional_comments))
    a("</dl>")

    a("<h3>2.4. User data</h3><dl>")
    ud = ds.user_data
    a(_dt_dd("Model-interaction data used?", _yn(ud.model_interaction_data_used)))
    a(_dt_dd("Other product-interaction data used?", _yn(ud.other_product_interaction_data_used)))
    if ud.model_interaction_data_used or ud.other_product_interaction_data_used:
        a(_dt_dd("Services/products description", ud.services_or_products_description))
        a(_dt_dd("Type of modality covered", _esc_modalities(ud.modalities_covered)))
        a(_dt_dd("Additional comments", ud.additional_comments))
    a("</dl>")

    a("<h3>2.5. Synthetic data</h3><dl>")
    sd = ds.synthetic_data
    a(_dt_dd("Synthetic AI-generated data used?", _yn(sd.used)))
    if sd.used:
        a(_dt_dd("Modality of the synthetic data", _esc_modalities(sd.modalities_covered)))
        a(_dt_dd("Generating model(s)", _esc_list(sd.generating_models)))
        a(_dt_dd("Other generating models description", sd.other_generating_models_description))
        a(_dt_dd("Additional comments", sd.additional_comments))
    a("</dl>")

    a("<h3>2.6. Other sources of data</h3><dl>")
    osd = ds.other_sources
    a(_dt_dd("Other data sources used?", _yn(osd.used)))
    if osd.used:
        a(_dt_dd("Description", osd.description))
        a(_dt_dd("Additional comments", osd.additional_comments))
    a("</dl>")

    a("<h2>3. Data processing aspects</h2>")
    a("<h3>3.1. Respect of reservation of rights from text and data mining exception or limitation</h3><dl>")
    tdm = dpa.tdm_reservation_respect
    a(_dt_dd("Code of Practice signatory?", _yn(tdm.is_code_of_practice_signatory)))
    a(_dt_dd("Measures implemented", tdm.measures_description))
    a(_dt_dd("Additional comments", tdm.additional_comments))
    a("</dl>")
    a("<h3>3.2. Removal of illegal content</h3><dl>")
    a(_dt_dd("Measures taken", dpa.illegal_content_removal.measures_description))
    a("</dl>")
    a("<h3>3.3. Other information (optional)</h3><dl>")
    a(_dt_dd("Other relevant information", dpa.other_information))
    a("</dl>")

    a("</body></html>")
    return "".join(parts)
