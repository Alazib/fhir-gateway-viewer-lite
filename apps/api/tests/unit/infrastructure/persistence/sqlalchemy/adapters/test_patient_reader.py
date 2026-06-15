from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.identifier import Identifier
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.adapters.patient_reader import (
    SqlAlchemyPatientReader,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.patient import (
    PatientIdentifierRecord,
    PatientRecord,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(
        engine,
        tables=[
            PatientRecord.__table__,
            PatientIdentifierRecord.__table__,
        ],
    )

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with SessionLocal() as session:
        yield session

    Base.metadata.drop_all(
        engine,
        tables=[
            PatientIdentifierRecord.__table__,
            PatientRecord.__table__,
        ],
    )


def test_get_by_id_returns_patient(session: Session):
    session.add(
        PatientRecord(
            id="pat-001",
            name_text="John Smith",
            identifiers=[
                PatientIdentifierRecord(
                    system="https://hospital.example.org/mrn",
                    value="MRN-001",
                ),
            ],
        )
    )
    session.commit()

    reader = SqlAlchemyPatientReader(session)

    patient = reader.get_by_id(ResourceId("pat-001"))

    assert isinstance(patient, Patient)
    assert patient.id == ResourceId("pat-001")
    assert patient.identifiers == (
        Identifier(
            system="https://hospital.example.org/mrn",
            value="MRN-001",
        ),
    )


def test_get_by_id_returns_none_when_patient_does_not_exist(session: Session):
    reader = SqlAlchemyPatientReader(session)

    patient = reader.get_by_id(ResourceId("missing-patient"))

    assert patient is None


def test_get_by_id_ignores_logically_deleted_patient(session: Session):
    session.add(
        PatientRecord(
            id="pat-001",
            name_text="John Smith",
            deleted_at=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
        )
    )
    session.commit()

    reader = SqlAlchemyPatientReader(session)

    patient = reader.get_by_id(ResourceId("pat-001"))

    assert patient is None


def test_search_by_text_matches_patient_name(session: Session):
    session.add(
        PatientRecord(
            id="pat-001",
            name_text="John Smith",
        )
    )
    session.commit()

    reader = SqlAlchemyPatientReader(session)

    patients = reader.search_by_text("smith")

    assert tuple(patient.id for patient in patients) == (
        ResourceId("pat-001"),
    )


def test_search_by_text_matches_patient_identifier(session: Session):
    session.add(
        PatientRecord(
            id="pat-001",
            name_text="John Smith",
            identifiers=[
                PatientIdentifierRecord(
                    system="https://hospital.example.org/mrn",
                    value="MRN-001",
                ),
            ],
        )
    )
    session.commit()

    reader = SqlAlchemyPatientReader(session)

    patients = reader.search_by_text("MRN-001")

    assert tuple(patient.id for patient in patients) == (
        ResourceId("pat-001"),
    )


def test_search_by_text_returns_empty_tuple_when_no_patient_matches(
    session: Session,
):
    session.add(
        PatientRecord(
            id="pat-001",
            name_text="John Smith",
        )
    )
    session.commit()

    reader = SqlAlchemyPatientReader(session)

    patients = reader.search_by_text("Garcia")

    assert patients == ()


def test_search_by_text_ignores_logically_deleted_patients(session: Session):
    session.add_all(
        [
            PatientRecord(
                id="pat-001",
                name_text="John Smith",
            ),
            PatientRecord(
                id="pat-002",
                name_text="John Deleted",
                deleted_at=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
            ),
        ]
    )
    session.commit()

    reader = SqlAlchemyPatientReader(session)

    patients = reader.search_by_text("John")

    assert tuple(patient.id for patient in patients) == (
        ResourceId("pat-001"),
    )


def test_search_by_text_does_not_return_duplicate_patients_when_multiple_identifiers_match(
    session: Session,
):
    session.add(
        PatientRecord(
            id="pat-001",
            name_text="John Smith",
            identifiers=[
                PatientIdentifierRecord(
                    system="https://hospital.example.org/mrn",
                    value="MRN-001",
                ),
                PatientIdentifierRecord(
                    system="https://hospital.example.org/legacy-mrn",
                    value="OLD-MRN-001",
                ),
            ],
        )
    )
    session.commit()

    reader = SqlAlchemyPatientReader(session)

    patients = reader.search_by_text("MRN")

    assert tuple(patient.id for patient in patients) == (
        ResourceId("pat-001"),
    )
