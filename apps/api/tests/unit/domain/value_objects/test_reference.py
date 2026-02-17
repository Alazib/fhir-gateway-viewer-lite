import pytest

from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


################################### VALID CASES:


def test_accepts_valid_reference():
    ref = Reference(resource_type="Patient", id=ResourceId("pat-001"))

    assert ref.resource_type == "Patient"
    assert ref.id.value == "pat-001"


def test_trims_resource_type():
    ref = Reference(resource_type="  Patient  ", id=ResourceId("pat-001"))
    assert ref.resource_type == "Patient"


################################### NOT VALID CASES:


def test_rejects_non_string_resource_type():
    with pytest.raises(DomainValidationError) as exc:
        Reference(resource_type=123, id=ResourceId("pat-001"))  # type: ignore

    assert exc.value.field == "Reference.resource_type"
    assert exc.value.message == "must be a string"


def test_rejects_empty_resource_type():
    with pytest.raises(DomainValidationError) as exc:
        Reference(resource_type="   ", id=ResourceId("pat-001"))

    assert exc.value.field == "Reference.resource_type"
    assert exc.value.message == "cannot be empty"


def test_rejects_non_resource_id():
    with pytest.raises(DomainValidationError) as exc:
        Reference(resource_type="Patient", id="pat-001")  # type: ignore

    assert exc.value.field == "Reference.id"
    assert exc.value.message == "must be a ResourceId"
