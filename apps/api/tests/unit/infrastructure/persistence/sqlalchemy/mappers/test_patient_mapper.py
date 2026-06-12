from datetime import datetime, timezone
import pytest

from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.identifier import Identifier
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.patient import (
    patient_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.patient import (
    PatientIdentifierRecord,
    PatientRecord,
)

from fhir_gateway.domain.errors import DomainValidationError


def test_patient_record_to_domain_returns_patient():
    record = PatientRecord(
        id="pat-001",
        name_text="John Smith",
        name_family=None,
        name_given=None,
    )

    patient = patient_record_to_domain(record)

    assert isinstance(patient, Patient)


def test_patient_record_to_domain_maps_id_to_resource_id():
    record = PatientRecord(
        id="pat-001",
        name_text="John Smith",
        name_family=None,
        name_given=None,
    )

    patient = patient_record_to_domain(record)

    assert patient.id == ResourceId("pat-001")


def test_patient_record_to_domain_maps_text_name():
    record = PatientRecord(
        id="pat-001",
        name_text="John Smith",
        name_family=None,
        name_given=None,
    )

    patient = patient_record_to_domain(record)

    assert patient.name == HumanName(text="John Smith")


def test_patient_record_to_domain_maps_structured_name():
    record = PatientRecord(
        id="pat-001",
        name_text=None,
        name_family="Smith",
        name_given=["John", "Edward"],
    )

    patient = patient_record_to_domain(record)

    assert patient.name == HumanName(
        given=("John", "Edward"),
        family="Smith",
    )


def test_patient_record_to_domain_maps_missing_name_to_none():
    record = PatientRecord(
        id="pat-001",
        name_text=None,
        name_family=None,
        name_given=None,
    )

    patient = patient_record_to_domain(record)

    assert patient.name is None


def test_patient_record_to_domain_maps_empty_given_name_as_no_name_when_other_name_fields_missing():
    record = PatientRecord(
        id="pat-001",
        name_text=None,
        name_family=None,
        name_given=[],
    )

    patient = patient_record_to_domain(record)

    assert patient.name is None


def test_patient_record_to_domain_maps_identifiers():
    record = PatientRecord(
        id="pat-001",
        name_text="John Smith",
        name_family=None,
        name_given=None,
        identifiers=[
            PatientIdentifierRecord(
                system="https://hospital.example.org/mrn",
                value="MRN-001",
            ),
            PatientIdentifierRecord(
                system="https://national.example.org/id",
                value="NAT-001",
            ),
        ],
    )

    patient = patient_record_to_domain(record)

    assert patient.identifiers == (
        Identifier(
            system="https://hospital.example.org/mrn",
            value="MRN-001",
        ),
        Identifier(
            system="https://national.example.org/id",
            value="NAT-001",
        ),
    )


def test_patient_record_to_domain_maps_no_identifiers_to_empty_tuple():
    record = PatientRecord(
        id="pat-001",
        name_text="John Smith",
        name_family=None,
        name_given=None,
        identifiers=[],
    )

    patient = patient_record_to_domain(record)

    assert patient.identifiers == ()


def test_patient_record_to_domain_ignores_technical_metadata():
    timestamp = datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc)

    record = PatientRecord(
        id="pat-001",
        name_text="John Smith",
        name_family=None,
        name_given=None,
        created_at=timestamp,
        updated_at=timestamp,
        deleted_at=timestamp,
    )

    patient = patient_record_to_domain(record)

    assert not hasattr(patient, "created_at")
    assert not hasattr(patient, "updated_at")
    assert not hasattr(patient, "deleted_at")

def test_patient_record_to_domain_rejects_partial_structured_name_without_family():
    record = PatientRecord(
        id="pat-001",
        name_text=None,
        name_family=None,
        name_given=["John"],
    )

    with pytest.raises(DomainValidationError) as exc_info:
        patient_record_to_domain(record)

    assert exc_info.value.field == "HumanName.family"


def test_patient_record_to_domain_rejects_partial_structured_name_without_given():
    record = PatientRecord(
        id="pat-001",
        name_text=None,
        name_family="Smith",
        name_given=None,
    )

    with pytest.raises(DomainValidationError) as exc_info:
        patient_record_to_domain(record)

    assert exc_info.value.field == "HumanName.given"


def test_patient_record_to_domain_accepts_text_name_even_without_structured_fields():
    record = PatientRecord(
        id="pat-001",
        name_text="John Smith",
        name_family=None,
        name_given=None,
    )

    patient = patient_record_to_domain(record)

    assert patient.name == HumanName(text="John Smith")
