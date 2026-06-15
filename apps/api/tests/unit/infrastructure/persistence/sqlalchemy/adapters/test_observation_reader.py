from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fhir_gateway.domain.entities.observation import Observation
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.adapters.observation_reader import (
    SqlAlchemyObservationReader,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.observation import (
    ObservationCodeRecord,
    ObservationRecord,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.patient import (
    PatientRecord,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(
        engine,
        tables=[
            PatientRecord.__table__,
            ObservationCodeRecord.__table__,
            ObservationRecord.__table__,
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
            ObservationRecord.__table__,
            ObservationCodeRecord.__table__,
            PatientRecord.__table__,
        ],
    )


def _restore_sqlite_datetime_timezone(
    *records: ObservationRecord,
) -> None:
    """Restore UTC tzinfo after SQLite/SQLAlchemy datetime roundtrip.

    These adapter unit tests use SQLite for speed. SQLite does not preserve
    timezone-aware datetimes in the same way PostgreSQL does for
    DateTime(timezone=True). The production model is PostgreSQL-oriented, so
    this helper keeps the test focused on adapter behavior instead of SQLite's
    datetime limitation.
    """
    for record in records:
        if record.effective_at.tzinfo is None:
            record.effective_at = record.effective_at.replace(
                tzinfo=timezone.utc
            )

        if record.deleted_at is not None and record.deleted_at.tzinfo is None:
            record.deleted_at = record.deleted_at.replace(
                tzinfo=timezone.utc
            )


def test_list_by_patient_returns_observations(session: Session):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    code = ObservationCodeRecord(
        system="http://loinc.org",
        code="4548-4",
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
    )

    session.add_all([patient, code])
    session.flush()

    observation = ObservationRecord(
        id="obs-001",
        patient_id="pat-001",
        status="final",
        code_id=code.id,
        effective_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        value_quantity=7.2,
        value_unit="%",
    )

    session.add(observation)
    session.flush()
    _restore_sqlite_datetime_timezone(observation)

    reader = SqlAlchemyObservationReader(session)

    observations = reader.list_by_patient(ResourceId("pat-001"))

    assert len(observations) == 1
    assert isinstance(observations[0], Observation)
    assert observations[0].id == ResourceId("obs-001")
    assert observations[0].code == Code(
        system="http://loinc.org",
        code="4548-4",
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
    )


def test_list_by_patient_returns_empty_tuple_when_no_observations_match(
    session: Session,
):
    reader = SqlAlchemyObservationReader(session)

    observations = reader.list_by_patient(ResourceId("pat-001"))

    assert observations == ()


def test_list_by_patient_ignores_logically_deleted_observations(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    code = ObservationCodeRecord(
        system="http://loinc.org",
        code="4548-4",
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
    )

    session.add_all([patient, code])
    session.flush()

    observation = ObservationRecord(
        id="obs-001",
        patient_id="pat-001",
        status="final",
        code_id=code.id,
        effective_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        value_quantity=7.2,
        value_unit="%",
        deleted_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
    )

    session.add(observation)
    session.flush()
    _restore_sqlite_datetime_timezone(observation)

    reader = SqlAlchemyObservationReader(session)

    observations = reader.list_by_patient(ResourceId("pat-001"))

    assert observations == ()


def test_list_by_patient_orders_observations_by_effective_at(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    code = ObservationCodeRecord(
        system="http://loinc.org",
        code="4548-4",
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
    )

    session.add_all([patient, code])
    session.flush()

    later_observation = ObservationRecord(
        id="obs-002",
        patient_id="pat-001",
        status="final",
        code_id=code.id,
        effective_at=datetime(
            2026,
            6,
            2,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        value_quantity=7.1,
        value_unit="%",
    )
    earlier_observation = ObservationRecord(
        id="obs-001",
        patient_id="pat-001",
        status="final",
        code_id=code.id,
        effective_at=datetime(
            2026,
            6,
            1,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        value_quantity=7.2,
        value_unit="%",
    )

    session.add_all([later_observation, earlier_observation])
    session.flush()
    _restore_sqlite_datetime_timezone(
        later_observation,
        earlier_observation,
    )

    reader = SqlAlchemyObservationReader(session)

    observations = reader.list_by_patient(ResourceId("pat-001"))

    assert tuple(observation.id for observation in observations) == (
        ResourceId("obs-001"),
        ResourceId("obs-002"),
    )


def test_list_by_patient_and_code_returns_matching_observations(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    hba1c_code = ObservationCodeRecord(
        system="http://loinc.org",
        code="4548-4",
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
    )
    glucose_code = ObservationCodeRecord(
        system="http://loinc.org",
        code="2345-7",
        display="Glucose [Mass/volume] in Serum or Plasma",
    )

    session.add_all([patient, hba1c_code, glucose_code])
    session.flush()

    hba1c_observation = ObservationRecord(
        id="obs-001",
        patient_id="pat-001",
        status="final",
        code_id=hba1c_code.id,
        effective_at=datetime(
            2026,
            6,
            1,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        value_quantity=7.2,
        value_unit="%",
    )
    glucose_observation = ObservationRecord(
        id="obs-002",
        patient_id="pat-001",
        status="final",
        code_id=glucose_code.id,
        effective_at=datetime(
            2026,
            6,
            1,
            11,
            0,
            tzinfo=timezone.utc,
        ),
        value_quantity=110.0,
        value_unit="mg/dL",
    )

    session.add_all([hba1c_observation, glucose_observation])
    session.flush()
    _restore_sqlite_datetime_timezone(
        hba1c_observation,
        glucose_observation,
    )

    reader = SqlAlchemyObservationReader(session)

    observations = reader.list_by_patient_and_code(
        ResourceId("pat-001"),
        Code(
            system="http://loinc.org",
            code="4548-4",
            display="Hemoglobin A1c/Hemoglobin.total in Blood",
        ),
    )

    assert tuple(observation.id for observation in observations) == (
        ResourceId("obs-001"),
    )


def test_list_by_patient_and_code_returns_empty_tuple_when_code_does_not_match(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    code = ObservationCodeRecord(
        system="http://loinc.org",
        code="4548-4",
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
    )

    session.add_all([patient, code])
    session.flush()

    observation = ObservationRecord(
        id="obs-001",
        patient_id="pat-001",
        status="final",
        code_id=code.id,
        effective_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        value_quantity=7.2,
        value_unit="%",
    )

    session.add(observation)
    session.flush()
    _restore_sqlite_datetime_timezone(observation)

    reader = SqlAlchemyObservationReader(session)

    observations = reader.list_by_patient_and_code(
        ResourceId("pat-001"),
        Code(
            system="http://loinc.org",
            code="9999-9",
            display="Other observation",
        ),
    )

    assert observations == ()
