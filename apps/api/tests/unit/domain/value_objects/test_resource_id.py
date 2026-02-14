import pytest
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.resource_id import ResourceId


####################################VALID CASES:


# ResourceId("pat-001") is valid.
def test_resource_id_accepts_non_empty_string():
    rid = ResourceId("pat-001")
    assert rid.value == "pat-001"


# ResourceId(" pat-001 ") trims white spaces.
def test_resource_id_trims_whitespace():
    rid = ResourceId(" pat-001 ")
    assert rid.value == "pat-001"


####################################NOT VALID CASES:


# ResourceId("") throws DomainValidationError.
def test_resource_id_rejects_empty_string():
    with pytest.raises(DomainValidationError) as exc:
        ResourceId("")

    assert exc.value.field == "ResourceId.value"
    assert "empty" in exc.value.message


# ResourceId(" ") throws DomainValidationError.
def test_resource_id_rejects_whitespace_only():
    with pytest.raises(DomainValidationError) as exc:
        ResourceId("   ")

    assert exc.value.field == "ResourceId.value"
    assert "empty" in exc.value.message


# ResourceId(123) throws DomainValidationError.
def test_resource_id_rejects_non_string_and_exposes_context():
    with pytest.raises(DomainValidationError) as exc:
        ResourceId(123)  # type: ignore

    assert exc.value.field == "ResourceId.value"
    assert "string" in exc.value.message
