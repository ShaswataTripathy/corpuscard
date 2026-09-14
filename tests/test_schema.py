import pytest
from pydantic import ValidationError

from corpuscard.schema import ModalityEntry, Modality


def test_modality_entry_requires_size():
    with pytest.raises(ValidationError):
        ModalityEntry(modality=Modality.TEXT, types_of_content="text")


def test_modality_entry_rejects_out_of_range_bin():
    with pytest.raises(ValidationError):
        ModalityEntry(
            modality=Modality.TEXT,
            size_range="Less than 1 million images",  # wrong bin set for text
            types_of_content="text",
        )


def test_modality_entry_accepts_fixed_bin():
    m = ModalityEntry(
        modality=Modality.TEXT,
        size_range="1 billion to 10 trillion tokens",
        types_of_content="text",
    )
    assert m.size_range == "1 billion to 10 trillion tokens"


def test_modality_entry_accepts_custom_size():
    m = ModalityEntry(
        modality=Modality.IMAGE,
        custom_size_value="40",
        custom_size_unit="million images",
        types_of_content="photos",
    )
    assert m.custom_size_value == "40"


def test_other_modality_requires_name():
    with pytest.raises(ValidationError):
        ModalityEntry(
            modality=Modality.OTHER,
            custom_size_value="10",
            custom_size_unit="GB",
            types_of_content="sensor data",
        )
