from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fhir_gateway.domain.entities.encounter import Encounter
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.adapters.encounter_reader import (
    SqlAlchemyEncounterReader,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.encounter import (
    EncounterRecord,
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
            EncounterRecord.__table__,
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
            EncounterRecord.__table__,
            PatientRecord.__table__,
        ],
    )


def _restore_sqlite_datetime_timezone(
    *records: EncounterRecord,
) -> None:
    """Restore UTC tzinfo after SQLite/SQLAlchemy datetime roundtrip.

    These adapter unit tests use SQLite for speed. SQLite does not preserve
    timezone-aware datetimes in the same way PostgreSQL does for
    DateTime(timezone=True). The production model is PostgreSQL-oriented, so
    this helper keeps the test focused on adapter behavior instead of SQLite's
    datetime limitation.
    """
    for record in records:
        if record.period_start_at.tzinfo is None:
            record.period_start_at = record.period_start_at.replace(
                tzinfo=timezone.utc
            )

        if (
            record.period_end_at is not None
            and record.period_end_at.tzinfo is None
        ):
            record.period_end_at = record.period_end_at.replace(
                tzinfo=timezone.utc
            )

        if record.deleted_at is not None and record.deleted_at.tzinfo is None:
            record.deleted_at = record.deleted_at.replace(
                tzinfo=timezone.utc
            )


def test_list_by_patient_returns_encounters(session: Session):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )

    session.add(patient)
    session.flush()

    encounter = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        period_end_at=datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc),
    )

    session.add(encounter)
    session.flush()
    _restore_sqlite_datetime_timezone(encounter)

    reader = SqlAlchemyEncounterReader(session)

    encounters = reader.list_by_patient(ResourceId("pat-001"))

    assert len(encounters) == 1
    assert isinstance(encounters[0], Encounter)
    assert encounters[0].id == ResourceId("enc-001")


def test_list_by_patient_returns_empty_tuple_when_no_encounters_match(
    session: Session,
):
    reader = SqlAlchemyEncounterReader(session)

    encounters = reader.list_by_patient(ResourceId("pat-001"))

    assert encounters == ()


def test_list_by_patient_ignores_encounters_from_other_patients(
    session: Session,
):
    patient_001 = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    patient_002 = PatientRecord(
        id="pat-002",
        name_text="Jane Doe",
    )

    session.add_all([patient_001, patient_002])
    session.flush()

    matching_encounter = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        period_end_at=datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc),
    )
    other_patient_encounter = EncounterRecord(
        id="enc-002",
        patient_id="pat-002",
        period_start_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
        period_end_at=datetime(2026, 6, 2, 11, 0, tzinfo=timezone.utc),
    )

    session.add_all([matching_encounter, other_patient_encounter])
    session.flush()
    _restore_sqlite_datetime_timezone(
        matching_encounter,
        other_patient_encounter,
    )

    reader = SqlAlchemyEncounterReader(session)

    encounters = reader.list_by_patient(ResourceId("pat-001"))

    assert tuple(encounter.id for encounter in encounters) == (
        ResourceId("enc-001"),
    )


def test_list_by_patient_ignores_logically_deleted_encounters(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )

    session.add(patient)
    session.flush()

    encounter = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        period_end_at=datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc),
        deleted_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
    )

    session.add(encounter)
    session.flush()
    _restore_sqlite_datetime_timezone(encounter)

    reader = SqlAlchemyEncounterReader(session)

    encounters = reader.list_by_patient(ResourceId("pat-001"))

    assert encounters == ()


def test_list_by_patient_orders_encounters_by_period_start_at(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )

    session.add(patient)
    session.flush()

    later_encounter = EncounterRecord(
        id="enc-002",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
        period_end_at=datetime(2026, 6, 2, 11, 0, tzinfo=timezone.utc),
    )
    earlier_encounter = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        period_end_at=datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc),
    )

    session.add_all([later_encounter, earlier_encounter])
    session.flush()
    _restore_sqlite_datetime_timezone(
        later_encounter,
        earlier_encounter,
    )

    reader = SqlAlchemyEncounterReader(session)

    encounters = reader.list_by_patient(ResourceId("pat-001"))

    assert tuple(encounter.id for encounter in encounters) == (
        ResourceId("enc-001"),
        ResourceId("enc-002"),
    )


def test_list_by_patient_maps_encounter_without_period_end(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )

    session.add(patient)
    session.flush()

    encounter = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        period_end_at=None,
    )

    session.add(encounter)
    session.flush()
    _restore_sqlite_datetime_timezone(encounter)

    reader = SqlAlchemyEncounterReader(session)

    encounters = reader.list_by_patient(ResourceId("pat-001"))

    assert len(encounters) == 1
    assert encounters[0].period.end is None
