import pytest
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.identifier import Identifier
from fhir_gateway.domain.value_objects.resource_id import ResourceId


################################### VALID CASES:


def test_accepts_patient_with_id_only():
    p = Patient(id=ResourceId("pat-001"))
    assert p.id.value == "pat-001"
    assert p.identifier is None
    assert p.name is None


def test_accepts_patient_with_name():
    name = HumanName(given=["Ana"], family="García")
    p = Patient(id=ResourceId("pat-001"), name=name)
    assert p.name == name


def test_accepts_patient_with_identifier():
    identifier = Identifier(system="urn:mrn:hospital-x", value="MRN-000123")
    p = Patient(id=ResourceId("pat-001"), identifier=identifier)
    assert p.identifier == identifier


################################### NOT VALID CASES:


def test_rejects_non_resource_id():
    with pytest.raises(DomainValidationError) as exc:
        Patient(id="pat-001")  # type: ignore

    assert exc.value.field == "Patient.id"
    assert exc.value.message == "must be a ResourceId"


def test_rejects_non_identifier():
    with pytest.raises(DomainValidationError) as exc:
        Patient(id=ResourceId("pat-001"), identifier="MRN-000123")  # type: ignore

    assert exc.value.field == "Patient.identifier"
    assert exc.value.message == "must be an Identifier"


def test_rejects_non_human_name():
    with pytest.raises(DomainValidationError) as exc:
        Patient(id=ResourceId("pat-001"), name="Ana García")  # type: ignore

    assert exc.value.field == "Patient.name"
    assert exc.value.message == "must be a HumanName"
