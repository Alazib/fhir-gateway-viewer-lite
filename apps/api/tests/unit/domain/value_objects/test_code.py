import pytest
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.code import Code


####################################VALID CASES:


# Code without display returns "code.display = None".
def test_without_display():
    code = Code(system="http://loinc.org", code="4548-4")
    assert code.display is None


# Code with " " (empty string) display returns "code.display = None"
def test_empty_string_display():
    code = Code(system="http://loinc.org", code="4548-4", display="    ")
    assert code.display is None


# Code with a string display is valid:
def test_string_display():
    code = Code(
        system="http://loinc.org",
        code="4548-4",
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
    )
    assert code.display == "Hemoglobin A1c/Hemoglobin.total in Blood"


# Code trims system, code and display:
def test_trims_whitespace():
    code = Code(
        system="   http://loinc.org   ",
        code="   4548-4   ",
        display="   Hemoglobin A1c/Hemoglobin.total in Blood   ",
    )
    assert code.system == "http://loinc.org"
    assert code.code == "4548-4"
    assert code.display == "Hemoglobin A1c/Hemoglobin.total in Blood"


####################################NOT VALID CASES:


# Code with not string Code.system throws DomainValidationError.
def test_rejects_not_string_system():
    with pytest.raises(DomainValidationError) as exc:
        Code(system=123, code="x")  # type: ignore

    assert exc.value.field == "Code.system"
    assert exc.value.message == "must be a string"


# Code with " " (whitespace only) Code.system throws DomainValidationError.
def test_rejects_whitespace_only_system():
    with pytest.raises(DomainValidationError) as exc:
        Code(system=" ", code="x")

    assert exc.value.field == "Code.system"
    assert exc.value.message == "cannot be empty"


# Code with "" (empty) Code.system throws DomainValidationError.
def test_rejects_empty_string_system():
    with pytest.raises(DomainValidationError) as exc:
        Code(system="", code="x")

    assert exc.value.field == "Code.system"
    assert exc.value.message == "cannot be empty"


# Code with not string Code.code throws DomainValidationError.
def test_rejects_not_string_code():
    with pytest.raises(DomainValidationError) as exc:
        Code(system="x", code=123)  # type: ignore

    assert exc.value.field == "Code.code"
    assert exc.value.message == "must be a string"


# Code with " " (whitespace only) Code.code throws DomainValidationError.
def test_rejects_whitespace_only_code():
    with pytest.raises(DomainValidationError) as exc:
        Code(system="x", code=" ")

    assert exc.value.field == "Code.code"
    assert exc.value.message == "cannot be empty"


# Code with "" (empty) Code.code throws DomainValidationError.
def test_rejects_empty_string_code():
    with pytest.raises(DomainValidationError) as exc:
        Code(system="x", code="")

    assert exc.value.field == "Code.code"
    assert exc.value.message == "cannot be empty"


# Code with not string Code.display throws DomainValidationError.
def test_rejects_not_string_display():
    with pytest.raises(DomainValidationError) as exc:
        Code(system="x", code="x", display=1234)  # type: ignore

    assert exc.value.field == "Code.display"
    assert exc.value.message == "must be a string"
