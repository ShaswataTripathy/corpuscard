"""
Renders a short copyright-policy page from the same manifest, covering
Article 53(1)(c) AI Act - the (separate, smaller) obligation for GPAI
providers to put in place a policy to comply with Union copyright law,
including honouring text-and-data-mining rights reservations.

Section 3.1 of the official Article 53(1)(d) Summary template explicitly
encourages providers to link to this policy from their Summary
("Providers are also encouraged to disclose a summary of their copyright
policy under Article 53(1)(c) AI Act, if made publicly available").

This is necessarily a thin starting point, not a complete policy - it
surfaces only what's already captured in the training-summary manifest
(Section 3's TDM-reservation and illegal-content measures). A real policy
will need legal review and almost certainly more detail than the manifest
alone captures.
"""

from __future__ import annotations

from .render import _clean
from .schema import TrainingSummary

_PLACEHOLDER = "_Not covered by corpuscard - fill in manually with your legal team._"


def render_copyright_policy(summary: TrainingSummary) -> str:
    s = summary
    provider = s.general_information.provider_identification.provider_name_and_contact
    tdm = s.data_processing_aspects.tdm_reservation_respect
    illegal = s.data_processing_aspects.illegal_content_removal

    lines: list[str] = []
    a = lines.append

    a(f"# Copyright Policy")
    a("")
    a(f"**Provider:** {_clean(provider)}")
    a(f"**Last updated:** {s.last_update}")
    a("")
    a(
        "This policy describes how we comply with Union copyright and related-rights law "
        "in the collection and use of training data, as required by Article 53(1)(c) of "
        "Regulation (EU) 2024/1689 (AI Act)."
    )
    a("")

    a("## Respect of rights reservations under the text and data mining exception")
    a("")
    a(
        "Under Article 4(3) of Directive (EU) 2019/790, rightsholders may reserve their "
        "rights to prevent text and data mining of their works. "
        + (
            "We are a signatory to the Code of Practice for general-purpose AI models, "
            "which includes commitments to respect such reservations."
            if tdm.is_code_of_practice_signatory
            else "We are not currently a signatory to the Code of Practice for general-purpose AI models."
        )
    )
    a("")
    if tdm.measures_description:
        a("**Measures implemented:**")
        a("")
        a(_clean(tdm.measures_description))
        a("")
    else:
        a(_PLACEHOLDER)
        a("")

    a("## Removal of illegal content")
    a("")
    if illegal.measures_description:
        a(_clean(illegal.measures_description))
    else:
        a(_PLACEHOLDER)
    a("")

    a("## How to exercise your rights")
    a("")
    a(_PLACEHOLDER)
    a("")

    a("---")
    a("")
    a(
        "This page summarizes measures also referenced in our Article 53(1)(d) public "
        "training-content summary. It does not itself confirm compliance with Union "
        "copyright law; it describes the measures we have put in place."
    )

    return "\n".join(lines)
