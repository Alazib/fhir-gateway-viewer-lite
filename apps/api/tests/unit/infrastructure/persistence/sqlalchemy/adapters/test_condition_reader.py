from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fhir_gateway.domain.entities.condition import Condition
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.adapters.condition_reader import (
    SqlAlchemyConditionReader,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.condition import (
    ConditionCodeRecord,
    ConditionRecord,
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
            ConditionCodeRecord.__table__,
            ConditionRecord.__table__,
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
            ConditionRecord.__table__,
            ConditionCodeRecord.__table__,
            PatientRecord.__table__,
        ],
    )


def _restore_sqlite_datetime_timezone(
    *records: ConditionRecord,
) -> None:
    """Restore UTC tzinfo after SQLite/SQLAlchemy datetime roundtrip.

    These adapter unit tests use SQLite for speed. SQLite does not preserve
    timezone-aware datetimes in the same way PostgreSQL does for
    DateTime(timezone=True). The production model is PostgreSQL-oriented, so
    this helper keeps the test focused on adapter behavior instead of SQLite's
    datetime limitation.
    """
    for record in records:
        if record.recorded_at is not None and record.recorded_at.tzinfo is None:
            record.recorded_at = record.recorded_at.replace(
                tzinfo=timezone.utc
            )

        if record.deleted_at is not None and record.deleted_at.tzinfo is None:
            record.deleted_at = record.deleted_at.replace(
                tzinfo=timezone.utc
            )


def test_list_by_patient_returns_conditions(session: Session):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    code = ConditionCodeRecord(
        system="http://snomed.info/sct",
        code="44054006",
        display="Diabetes mellitus type 2",
    )

    session.add_all([patient, code])
    session.flush()

    condition = ConditionRecord(
        id="cond-001",
        patient_id="pat-001",
        code_id=code.id,
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
    )

    session.add(condition)
    session.flush()
    _restore_sqlite_datetime_timezone(condition)

    reader = SqlAlchemyConditionReader(session)

    conditions = reader.list_by_patient(ResourceId("pat-001"))

    assert len(conditions) == 1
    assert isinstance(conditions[0], Condition)
    assert conditions[0].id == ResourceId("cond-001")
    assert conditions[0].code == Code(
        system="http://snomed.info/sct",
        code="44054006",
        display="Diabetes mellitus type 2",
    )


def test_list_by_patient_returns_empty_tuple_when_no_conditions_match(
    session: Session,
):
    reader = SqlAlchemyConditionReader(session)

    conditions = reader.list_by_patient(ResourceId("pat-001"))

    assert conditions == ()


def test_list_by_patient_ignores_conditions_from_other_patients(
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
    code = ConditionCodeRecord(
        system="http://snomed.info/sct",
        code="44054006",
        display="Diabetes mellitus type 2",
    )

    session.add_all([patient_001, patient_002, code])
    session.flush()

    matching_condition = ConditionRecord(
        id="cond-001",
        patient_id="pat-001",
        code_id=code.id,
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
    )
    other_patient_condition = ConditionRecord(
        id="cond-002",
        patient_id="pat-002",
        code_id=code.id,
        recorded_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
    )

    session.add_all([matching_condition, other_patient_condition])
    session.flush()
    _restore_sqlite_datetime_timezone(
        matching_condition,
        other_patient_condition,
    )

    reader = SqlAlchemyConditionReader(session)

    conditions = reader.list_by_patient(ResourceId("pat-001"))

    assert tuple(condition.id for condition in conditions) == (
        ResourceId("cond-001"),
    )


def test_list_by_patient_ignores_logically_deleted_conditions(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    code = ConditionCodeRecord(
        system="http://snomed.info/sct",
        code="44054006",
        display="Diabetes mellitus type 2",
    )

    session.add_all([patient, code])
    session.flush()

    condition = ConditionRecord(
        id="cond-001",
        patient_id="pat-001",
        code_id=code.id,
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        deleted_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
    )

    session.add(condition)
    session.flush()
    _restore_sqlite_datetime_timezone(condition)

    reader = SqlAlchemyConditionReader(session)

    conditions = reader.list_by_patient(ResourceId("pat-001"))

    assert conditions == ()


def test_list_by_patient_orders_conditions_by_recorded_at(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    code = ConditionCodeRecord(
        system="http://snomed.info/sct",
        code="44054006",
        display="Diabetes mellitus type 2",
    )

    session.add_all([patient, code])
    session.flush()

    later_condition = ConditionRecord(
        id="cond-002",
        patient_id="pat-001",
        code_id=code.id,
        recorded_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
    )
    earlier_condition = ConditionRecord(
        id="cond-001",
        patient_id="pat-001",
        code_id=code.id,
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
    )

    session.add_all([later_condition, earlier_condition])
    session.flush()
    _restore_sqlite_datetime_timezone(
        later_condition,
        earlier_condition,
    )

    reader = SqlAlchemyConditionReader(session)

    conditions = reader.list_by_patient(ResourceId("pat-001"))

    assert tuple(condition.id for condition in conditions) == (
        ResourceId("cond-001"),
        ResourceId("cond-002"),
    )


def test_list_by_patient_maps_condition_without_recorded_at(
    session: Session,
):
    patient = PatientRecord(
        id="pat-001",
        name_text="John Smith",
    )
    code = ConditionCodeRecord(
        system="http://snomed.info/sct",
        code="44054006",
        display="Diabetes mellitus type 2",
    )

    session.add_all([patient, code])
    session.flush()

    condition = ConditionRecord(
        id="cond-001",
        patient_id="pat-001",
        code_id=code.id,
        recorded_at=None,
    )

    session.add(condition)
    session.flush()

    reader = SqlAlchemyConditionReader(session)

    conditions = reader.list_by_patient(ResourceId("pat-001"))

    assert len(conditions) == 1
    assert conditions[0].recorded_date is None
