import pytest
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.resource_id import ResourceId


# ResourceId("pat-001") es válido.
def test_resource_id_accepts_non_empty_string():
    rid = ResourceId("pat-001")
    assert rid.value == "pat-001"


# ResourceId(" pat-001 ") limpia espacios en blanco.
def test_resource_id_trims_whitespace():
    rid = ResourceId(" pat-001 ")
    assert rid.value == "pat-001"


# ResourceId("") lanza DomainValidationError.
def test_resource_id_rejects_empty_string():
    with pytest.raises(DomainValidationError):
        ResourceId("")


# ResourceId(" ") lanza DomainValidationError.
def test_resource_id_rejects_whitespace_only():
    with pytest.raises(DomainValidationError):
        ResourceId("   ")


# ResourceId(123) lanza DomainValidationError.
def test_resource_id_rejects_non_string_and_exposes_context():
    with pytest.raises(DomainValidationError) as exc:
        ResourceId(123)  # type: ignore

    assert exc.value.field == "ResourceId"
    assert "string" in exc.value.message
