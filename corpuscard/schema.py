"""
Data model for the EU AI Office's "Template for the Public Summary of Training
Content for General-Purpose AI models" required by Article 53(1)(d) of
Regulation (EU) 2024/1689 (the AI Act).

Field names, sections, and allowed value ranges are taken directly from the
official template, Annex to C(2025) 5235 final (Brussels, 24.7.2025):
https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models

Section numbers in this file's docstrings and class names (1, 1.1, 1.2, 1.3,
2, 2.1 ... 3.3) match the official template one-to-one, so a provider filling
this in can cross-reference the PDF directly.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"


# Fixed size bins from Section 1.3 of the template. A provider may instead
# give a custom size/unit ("Alternatively, specify the approximate size in a
# different measurement unit") — see ModalityEntry.custom_size_value/unit.
TEXT_SIZE_RANGES = ["Less than 1 billion tokens", "1 billion to 10 trillion tokens", "More than 10 trillion tokens"]
IMAGE_SIZE_RANGES = ["Less than 1 million images", "1 million to 1 billion images", "More than 1 billion images"]
AUDIO_VIDEO_SIZE_RANGES = ["Less than 10,000 hours", "10,000 to 1 million hours", "More than 1 million hours"]

_FIXED_RANGES_BY_MODALITY = {
    Modality.TEXT: TEXT_SIZE_RANGES,
    Modality.IMAGE: IMAGE_SIZE_RANGES,
    Modality.AUDIO: AUDIO_VIDEO_SIZE_RANGES,
    Modality.VIDEO: AUDIO_VIDEO_SIZE_RANGES,
}


class ModalityEntry(BaseModel):
    """One row of the Section 1.3 modality/size/content-type table."""

    modality: Modality
    other_modality_name: Optional[str] = Field(
        default=None, description="Required when modality == OTHER."
    )
    size_range: Optional[str] = Field(
        default=None,
        description="One of the fixed bins for this modality (see *_SIZE_RANGES). "
        "Leave unset and use custom_size_value/unit instead if you want to report "
        "an exact or differently-binned figure.",
    )
    custom_size_value: Optional[str] = None
    custom_size_unit: Optional[str] = None
    types_of_content: str = Field(
        description="General description of the type of content included, e.g. "
        "'fiction and non-fiction text, scientific text, source code'."
    )

    @model_validator(mode="after")
    def _check_size_and_other_name(self) -> "ModalityEntry":
        if self.modality == Modality.OTHER and not self.other_modality_name:
            raise ValueError("other_modality_name is required when modality is OTHER")

        has_fixed = self.size_range is not None
        has_custom = self.custom_size_value is not None and self.custom_size_unit is not None
        if not has_fixed and not has_custom:
            raise ValueError(
                f"{self.modality.value}: provide either size_range or "
                "custom_size_value + custom_size_unit"
            )
        if has_fixed and self.modality in _FIXED_RANGES_BY_MODALITY:
            allowed = _FIXED_RANGES_BY_MODALITY[self.modality]
            if self.size_range not in allowed:
                raise ValueError(
                    f"{self.modality.value}: size_range must be one of {allowed} "
                    "(or omit it and use custom_size_value/unit instead)"
                )
        return self


class ProviderIdentification(BaseModel):
    """Section 1.1"""

    provider_name_and_contact: str
    authorised_representative_name_and_contact: Optional[str] = Field(
        default=None,
        description="Only applicable if the provider is established outside the Union (Article 54 AI Act).",
    )


class ModelIdentification(BaseModel):
    """Section 1.2"""

    versioned_model_names: List[str] = Field(
        description="Unique identifier(s) for the model(s)/model version(s) covered by this Summary, "
        "e.g. 'Llama 3.1-405B'."
    )
    model_dependencies: Optional[str] = Field(
        default=None,
        description="If this model results from modifying/fine-tuning another GPAI model already on "
        "the Union market, name that model/version and link to its Summary.",
    )
    date_of_placement_on_union_market: str = Field(
        description="Date(s) the model (version(s)) was placed on the Union market."
    )


class GeneralInformation(BaseModel):
    """Section 1: identification + modalities/size/characteristics."""

    provider_identification: ProviderIdentification
    model_identification: ModelIdentification
    modalities: List[ModalityEntry] = Field(min_length=1)
    latest_data_collection_date: str = Field(
        description="Latest date data was collected/obtained for model training, format MM/YYYY."
    )
    continuously_trained_on_new_data: bool = Field(
        description="Whether the model is continuously trained on new/dynamic data after "
        "latest_data_collection_date."
    )
    linguistic_characteristics: Optional[str] = None
    other_characteristics: Optional[str] = Field(
        default=None,
        description="E.g. national/regional/demographic specificities of the training data.",
    )
    additional_comments: Optional[str] = None


class PubliclyAvailableDataset(BaseModel):
    """One entry in the 'large' publicly available datasets list, Section 2.1."""

    identifier_or_name: str
    link: Optional[str] = None
    description: Optional[str] = Field(
        default=None, description="Required if no link is available."
    )
    collection_start_date: Optional[str] = None
    collection_end_date: Optional[str] = None


class PubliclyAvailableDatasets(BaseModel):
    """Section 2.1"""

    used: bool
    modalities_covered: List[Modality] = Field(default_factory=list)
    large_datasets: List[PubliclyAvailableDataset] = Field(default_factory=list)
    other_datasets_general_description: Optional[str] = None
    additional_comments: Optional[str] = None


class LicensedDatasets(BaseModel):
    """Section 2.2.1 — datasets commercially licensed by rightsholders or their representatives."""

    has_licensing_agreements: bool
    modalities_covered: List[Modality] = Field(default_factory=list)


class OtherThirdPartyDatasets(BaseModel):
    """Section 2.2.2 — private datasets obtained from other third parties (not licensed as in 2.2.1)."""

    obtained: bool
    modalities_covered: List[Modality] = Field(default_factory=list)
    publicly_known_datasets: List[str] = Field(
        default_factory=list,
        description="Identifiers/names (+ links where available) of publicly known private "
        "third-party datasets.",
    )
    general_description: Optional[str] = None
    additional_comments: Optional[str] = None


class PrivateThirdPartyDatasets(BaseModel):
    """Section 2.2"""

    licensed: LicensedDatasets
    other_third_party: OtherThirdPartyDatasets


class CrawledData(BaseModel):
    """Section 2.3 — data crawled and scraped from online sources."""

    crawlers_used: bool
    crawler_names: List[str] = Field(default_factory=list)
    crawler_purposes: Optional[str] = None
    crawler_behaviour_description: Optional[str] = Field(
        default=None,
        description="E.g. respect of captchas, paywalls, robots.txt.",
    )
    collection_period_start: Optional[str] = Field(default=None, description="MM/YYYY")
    collection_period_end: Optional[str] = Field(default=None, description="MM/YYYY")
    content_and_sources_description: Optional[str] = None
    modalities_covered: List[Modality] = Field(default_factory=list)
    top_domains_summary: Optional[str] = Field(
        default=None,
        description="Summary of the most relevant domain names crawled: top 10% of all domains by "
        "content volume (top 5% or top 1000, whichever lower, for SMEs). May reference a "
        "downloadable file instead of inlining the list.",
    )
    top_domains_file: Optional[str] = Field(
        default=None, description="Path/URL to a downloadable file listing top domains, if used instead of inlining."
    )
    additional_comments: Optional[str] = None


class UserData(BaseModel):
    """Section 2.4"""

    model_interaction_data_used: bool = Field(
        description="Was data from user interactions with the AI model (e.g. prompts) used to train it?"
    )
    other_product_interaction_data_used: bool = Field(
        description="Was data collected from user interactions with the provider's other "
        "services/products used to train the model?"
    )
    services_or_products_description: Optional[str] = None
    modalities_covered: List[Modality] = Field(default_factory=list)
    additional_comments: Optional[str] = None


class SyntheticData(BaseModel):
    """Section 2.5"""

    used: bool
    modalities_covered: List[Modality] = Field(default_factory=list)
    generating_models: List[str] = Field(
        default_factory=list,
        description="Name(s) of the general-purpose AI model(s) used to generate the synthetic "
        "data, if on the market, with links to their Summaries.",
    )
    other_generating_models_description: Optional[str] = Field(
        default=None,
        description="Other AI models (incl. the provider's own unreleased models) used to generate "
        "synthetic data, including a general description of their training data if known.",
    )
    additional_comments: Optional[str] = None


class OtherDataSources(BaseModel):
    """Section 2.6"""

    used: bool
    description: Optional[str] = Field(
        default=None, description="Narrative description of these other data sources and the data."
    )
    additional_comments: Optional[str] = None


class DataSources(BaseModel):
    """Section 2"""

    publicly_available_datasets: PubliclyAvailableDatasets
    private_third_party_datasets: PrivateThirdPartyDatasets
    crawled_data: CrawledData
    user_data: UserData
    synthetic_data: SyntheticData
    other_sources: OtherDataSources


class TdmReservationRespect(BaseModel):
    """Section 3.1 — respect of rights reservation from the text-and-data-mining exception."""

    is_code_of_practice_signatory: bool
    measures_description: Optional[str] = Field(
        default=None,
        description="Measures implemented before/during data collection to respect TDM opt-outs, "
        "e.g. opt-out protocols honoured.",
    )
    additional_comments: Optional[str] = None


class IllegalContentRemoval(BaseModel):
    """Section 3.2"""

    measures_description: Optional[str] = Field(
        default=None,
        description="General description of measures to avoid/remove illegal content "
        "(blacklists, keywords, model-based classifiers).",
    )


class DataProcessingAspects(BaseModel):
    """Section 3"""

    tdm_reservation_respect: TdmReservationRespect
    illegal_content_removal: IllegalContentRemoval
    other_information: Optional[str] = None


class TrainingSummary(BaseModel):
    """Top-level document: the full Article 53(1)(d) Summary."""

    version: str = Field(description="Version of the Summary, with link(s) to previous versions where applicable.")
    last_update: str = Field(description="Date of last update, format DD/MM/YY.")
    general_information: GeneralInformation
    data_sources: DataSources
    data_processing_aspects: DataProcessingAspects
