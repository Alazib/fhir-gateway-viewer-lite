import pytest

from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.identifier import Identifier
from fhir_gateway.domain.value_objects.resource_id import ResourceId


################################### VALID CASES:


def test_accepts_patient_with_id_only():
    p = Patient(id=ResourceId("pat-001"))
    assert p.id.value == "pat-001"
    assert p.identifiers == ()
    assert p.name is None


def test_accepts_patient_with_name():
    name = HumanName(given=["Ana"], family="García")  # type: ignore
    p = Patient(id=ResourceId("pat-001"), name=name)
    assert p.name == name


def test_accepts_patient_with_identifiers_as_list_and_stores_tuple():
    ids = [
        Identifier(system="urn:mrn:hospital-x", value="MRN-000123"),
        Identifier(system="urn:insurance:acme", value="POLICY-998877"),
    ]
    p = Patient(id=ResourceId("pat-001"), identifiers=ids)  # type: ignore # list input
    assert isinstance(p.identifiers, tuple)
    assert p.identifiers == tuple(ids)


def test_accepts_patient_with_identifiers_as_tuple():
    ids = (
        Identifier(system="urn:mrn:hospital-x", value="MRN-000123"),
        Identifier(system="urn:insurance:acme", value="POLICY-998877"),
    )
    p = Patient(id=ResourceId("pat-001"), identifiers=ids)
    assert p.identifiers == ids


################################### NOT VALID CASES:


def test_rejects_non_resource_id():
    with pytest.raises(DomainValidationError) as exc:
        Patient(id="pat-001")  # type: ignore

    assert exc.value.field == "Patient.id"
    assert exc.value.message == "must be a ResourceId"


def test_rejects_non_human_name():
    with pytest.raises(DomainValidationError) as exc:
        Patient(id=ResourceId("pat-001"), name="Ana García")  # type: ignore

    assert exc.value.field == "Patient.name"
    assert exc.value.message == "must be a HumanName"


def test_rejects_identifiers_not_list_or_tuple():
    with pytest.raises(DomainValidationError) as exc:
        Patient(id=ResourceId("pat-001"), identifiers=1234)  # type: ignore

    assert exc.value.field == "Patient.identifiers"
    assert exc.value.message == "must be a list or a tuple of Identifier"


def test_rejects_identifiers_as_string():
    with pytest.raises(DomainValidationError) as exc:
        Patient(id=ResourceId("pat-001"), identifiers="MRN-000123")  # type: ignore

    assert exc.value.field == "Patient.identifiers"
    assert exc.value.message == "must be a list or a tuple of Identifier"


def test_rejects_identifiers_with_non_identifier_items():
    bad_ids = [Identifier(system="urn:mrn:hospital-x", value="MRN-000123"), "X"]  # type: ignore[list-item]
    with pytest.raises(DomainValidationError) as exc:
        Patient(id=ResourceId("pat-001"), identifiers=bad_ids)  # type: ignore[arg-type]

    assert exc.value.field == "Patient.identifiers"
    assert exc.value.message == "must be a list/tuple of Identifier"


def test_rejects_duplicate_identifiers_by_system_and_value():
    dup = [
        Identifier(system="urn:mrn:hospital-x", value="MRN-000123"),
        Identifier(system="urn:mrn:hospital-x", value="MRN-000123"),
    ]
    with pytest.raises(DomainValidationError) as exc:
        Patient(id=ResourceId("pat-001"), identifiers=dup)  # type: ignore[arg-type]

    assert exc.value.field == "Patient.identifiers"
    assert exc.value.message == "duplicate Identifier (system, value)"
