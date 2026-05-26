import pytest

from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.reference import (
    ALLOWED_REFERENCE_RESOURCE_TYPES,
    Reference,
)
from fhir_gateway.domain.value_objects.resource_id import ResourceId


################################### VALID CASES:


def test_allowed_reference_resource_types_contains_supported_domain_resources():
    assert ALLOWED_REFERENCE_RESOURCE_TYPES == frozenset(
        {
            "Patient",
            "Observation",
            "Condition",
            "Encounter",
        }
    )


@pytest.mark.parametrize(
    "resource_type, resource_id",
    (
        ("Patient", "pat-001"),
        ("Observation", "obs-001"),
        ("Condition", "con-001"),
        ("Encounter", "enc-001"),
    ),
)
def test_accepts_supported_resource_types(resource_type: str, resource_id: str):
    ref = Reference(resource_type=resource_type, id=ResourceId(resource_id))

    assert ref.resource_type == resource_type
    assert ref.id.value == resource_id


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
        Reference(resource_type="", id=ResourceId("pat-001"))

    assert exc.value.field == "Reference.resource_type"
    assert exc.value.message == "cannot be empty"


def test_rejects_blank_resource_type():
    with pytest.raises(DomainValidationError) as exc:
        Reference(resource_type="   ", id=ResourceId("pat-001"))

    assert exc.value.field == "Reference.resource_type"
    assert exc.value.message == "cannot be empty"


def test_rejects_lowercase_resource_type():
    with pytest.raises(DomainValidationError) as exc:
        Reference(resource_type="patient", id=ResourceId("pat-001"))

    assert exc.value.field == "Reference.resource_type"
    assert exc.value.message == "must be one of: Condition, Encounter, Observation, Patient"


def test_rejects_uppercase_resource_type():
    with pytest.raises(DomainValidationError) as exc:
        Reference(resource_type="PATIENT", id=ResourceId("pat-001"))

    assert exc.value.field == "Reference.resource_type"
    assert exc.value.message == "must be one of: Condition, Encounter, Observation, Patient"


def test_rejects_unsupported_resource_type():
    with pytest.raises(DomainValidationError) as exc:
        Reference(resource_type="Organization", id=ResourceId("org-001"))

    assert exc.value.field == "Reference.resource_type"
    assert exc.value.message == "must be one of: Condition, Encounter, Observation, Patient"


def test_rejects_non_resource_id():
    with pytest.raises(DomainValidationError) as exc:
        Reference(resource_type="Patient", id="pat-001")  # type: ignore

    assert exc.value.field == "Reference.id"
    assert exc.value.message == "must be a ResourceId"
