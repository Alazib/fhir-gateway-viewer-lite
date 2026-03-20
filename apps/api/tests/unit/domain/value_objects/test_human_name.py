import pytest

from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.human_name import HumanName


################################### VALID CASES:


def test_only_text_attribute_is_valid():
    hn = HumanName(text="Dr. John A. Smith")

    assert hn.text == "Dr. John A. Smith"
    assert hn.family is None
    assert hn.given == ()


def test_human_name_trims_text():
    hn = HumanName(text="  Dr. John A. Smith  ")
    assert hn.text == "Dr. John A. Smith"


def test_whitespace_text_falls_back_to_structured_when_given_and_family_present():
    hn = HumanName(text="   ", given=["Ana"], family="García")  # type: ignore

    assert hn.text is None
    assert hn.given == ("Ana",)
    assert hn.family == "García"


def test_only_given_and_family_is_valid_and_given_is_stored_as_tuple():
    hn = HumanName(given=["Ana", "María"], family="García López")  # type: ignore

    assert hn.text is None
    assert hn.given == ("Ana", "María")
    assert hn.family == "García López"


def test_trims_and_drops_empty_given_items_and_trims_family():
    hn = HumanName(given=["  Ana ", " ", "  María "], family="   García López  ")  # type: ignore

    assert hn.given == ("Ana", "María")
    assert hn.family == "García López"


################################### NOT VALID CASES:


def test_rejects_empty_parameters_when_text_missing():
    with pytest.raises(DomainValidationError) as exc:
        HumanName()

    assert exc.value.field == "HumanName.given"
    assert exc.value.message == "cannot be empty when text is missing"


def test_rejects_empty_given_when_text_missing():
    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=[], family="García")  # type: ignore

    assert exc.value.field == "HumanName.given"
    assert exc.value.message == "cannot be empty when text is missing"


def test_rejects_missing_family_when_text_missing():
    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=["Ana"])  # type: ignore

    assert exc.value.field == "HumanName.family"
    assert exc.value.message == "cannot be empty when text is missing"

    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=["Ana"], family="   ")  # type: ignore

    assert exc.value.field == "HumanName.family"
    assert exc.value.message == "cannot be empty when text is missing"


def test_rejects_given_is_a_string():
    with pytest.raises(DomainValidationError) as exc:
        HumanName(given="Ana")  # type: ignore

    assert exc.value.field == "HumanName.given"
    assert exc.value.message == "must be a list or a tuple"


def test_rejects_given_is_not_list_or_tuple():
    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=1234)  # type: ignore

    assert exc.value.field == "HumanName.given"
    assert exc.value.message == "must be a list or a tuple"


def test_rejects_given_contains_non_strings():
    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=["Ana", 1234], family="García")  # type: ignore[list-item]

    assert exc.value.field == "HumanName.given"
    assert exc.value.message == "must be a list/tuple of strings"


def test_rejects_family_not_string():
    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=["Ana"], family=123)  # type: ignore

    assert exc.value.field == "HumanName.family"
    assert exc.value.message == "must be a string"


def test_rejects_text_not_string():
    with pytest.raises(DomainValidationError) as exc:
        HumanName(text=1234)  # type: ignore

    assert exc.value.field == "HumanName.text"
    assert exc.value.message == "must be a string"
