import pytest
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.identifier import Identifier

####################################VALID CASES:


# Identifier with string attributes is valid:
def test_identifier_accepts_strings():
    identifier = Identifier(system="urn:mrn:hospital-x", value="MRN-000123")
    assert identifier.system == "urn:mrn:hospital-x"
    assert identifier.value == "MRN-000123"


# Identifier trims system and value:
def test_trims_whitespace():
    identifier = Identifier(system="  urn:mrn:hospital-x  ", value="  MRN-000123  ")
    assert identifier.system == "urn:mrn:hospital-x"
    assert identifier.value == "MRN-000123"


####################################NOT VALID CASES:


# Identifier with not string Identifier.system throws DomainValidationError.
def test_rejects_not_string_system():
    with pytest.raises(DomainValidationError) as exc:
        Identifier(system=123, value="X")  # type: ignore

    assert exc.value.field == "Identifier.system"
    assert "string" in exc.value.message


# Identifier with " " (whitespace only) Identifier.system throws DomainValidationError.
def test_rejects_whitespace_only_system():
    with pytest.raises(DomainValidationError) as exc:
        Identifier(system=" ", value="X")

    assert exc.value.field == "system"
    assert "empty" in exc.value.message


# Identifier with "" (empty) Identifier.system throws DomainValidationError.
def test_rejects_empty_string_system():
    with pytest.raises(DomainValidationError) as exc:
        Identifier(system="", value="X")

    assert exc.value.field == "system"
    assert "empty" in exc.value.message


# Identifier with not string Identifier.value throws DomainValidationError.
def test_rejects_not_string_identifier():
    with pytest.raises(DomainValidationError) as exc:
        Identifier(system="x", value=123)  # type: ignore

    assert exc.value.field == "Identifier.value"
    assert "string" in exc.value.message


# Identifier with " " (whitespace only) Identifier.system throws DomainValidationError.
def test_rejects_whitespace_only_value():
    with pytest.raises(DomainValidationError) as exc:
        Identifier(system="x", value=" ")

    assert exc.value.field == "value"
    assert "empty" in exc.value.message


# Identifier with "" (empty) Identifier.value throws DomainValidationError.
def test_rejects_empty_string_value():
    with pytest.raises(DomainValidationError) as exc:
        Identifier(system="x", value="")

    assert exc.value.field == "value"
    assert "empty" in exc.value.message
