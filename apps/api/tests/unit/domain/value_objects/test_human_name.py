import pytest
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.human_name import HumanName


################################### VALID CASES:


# HumanName only with HumanName.text is valid:
def test_only_text_atributte_is_valid():
    humanName = HumanName(text="Dr. John A. Smith")

    assert humanName.text == "Dr. John A. Smith"
    assert humanName.family is None
    assert humanName.given == ()


# HumanName trims HumanName.text:
def test_human_name_trims_text():
    humanName = HumanName(text="  Dr. John A. Smith  ")

    assert humanName.text == "Dr. John A. Smith"


# HumanName with no HumanName.text falls back to structured (HumanName.given + HumanName.family):
def test_text_whitespace_falls_back_to_structured():
    humanName = HumanName(text=" ", given=["Ana"], family="García")

    assert humanName.text is None
    assert humanName.given == ("Ana",)
    assert humanName.family == "García"


# HumanName only with HumanName.given and HumanName.family is valid:
def test_only_with_given_and_family():
    humanName = HumanName(given=["Ana", "María"], family="García López")

    assert humanName.given == ("Ana", "María")
    assert humanName.family == "García López"


# HumanName trims and clean empty HumanName.given and HumanName.family:
def test_human_name_trims_given_and_family():
    humanName = HumanName(given=["  Ana ", " ", "  María "], family="   García López")

    assert humanName.given == ("Ana", "María")
    assert humanName.family == "García López"


################################### NOT VALID CASES:


# HumanName with no HumanName.text and no (HumanName.given and HumanName.family) trhows DomainValidationError:
def test_rejects_empty_parameters():

    with pytest.raises(DomainValidationError) as exc:
        HumanName()

    assert exc.value.field == "given"
    assert exc.value.message == "cannot be empty when text is missing"


# HumanName with no HumanName.text and no HumanName.given trhows DomainValidationError:
def test_rejects_empty_given():

    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=[], family="García")

    assert exc.value.field == "given"
    assert exc.value.message == "cannot be empty when text is missing"


# HumanName with no HumanName.text and no HumanName.family trhows DomainValidationError:
def test_rejects_empty_family():

    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=["Ana"])

    assert exc.value.field == "family"
    assert exc.value.message == "cannot be empty when text is missing"

    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=["Ana"], family=" ")

    assert exc.value.field == "family"
    assert exc.value.message == "cannot be empty when text is missing"


# HumanName when HumanName.given is a string throws DomainValidationError:
def test_rejects_given_is_a_string():

    with pytest.raises(DomainValidationError) as exc:
        HumanName(given="Ana")  # type: ignore

    assert exc.value.field == "given"
    assert exc.value.message == "must be a list/tuple of strings"


# HumanName when HumanName.given is not a list/tuple throws DomainValidationError:
def test_rejects_given_is_not_a_list():

    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=1234)  # type: ignore

    assert exc.value.field == "HumanName.given"
    assert exc.value.message == "must be a list or a tuple"


# HumanName when HumanName.given contains no-strings throws DomainValidationError:
def test_rejects_given_when_contains_no_strings():

    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=["Ana", 1234])  # type: ignore

    assert exc.value.field == "given"
    assert exc.value.message == "must be a list/tuple of strings"


# HumanName when HumanName.family is not a string throws DomainValidationError:
def test_rejects_no_string_family():

    with pytest.raises(DomainValidationError) as exc:
        HumanName(given=["Ana"], family=123)  # type: ignore

    assert exc.value.field == "HumanName.family"
    assert exc.value.message == "must be a string"


# HumanName when HumanName.text is not a string throws DomainValidationError:
def test_rejects_no_string_text():

    with pytest.raises(DomainValidationError) as exc:
        HumanName(text=1234)  # type: ignore

    assert exc.value.field == "HumanName.text"
    assert exc.value.message == "must be a string"
