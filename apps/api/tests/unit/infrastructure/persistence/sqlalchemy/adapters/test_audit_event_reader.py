from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from fhir_gateway.domain.entities.audit_event import AuditAction, AuditEvent
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.adapters.audit_event_reader import (
    SqlAlchemyAuditEventReader,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.audit_event import (
    AuditEventRecord,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_btrim(dbapi_connection, connection_record):
        dbapi_connection.create_function(
            "btrim",
            1,
            lambda value: value.strip() if value is not None else None,
        )

    Base.metadata.create_all(
        engine,
        tables=[
            AuditEventRecord.__table__,
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
            AuditEventRecord.__table__,
        ],
    )


def _restore_sqlite_datetime_timezone(
    *records: AuditEventRecord,
) -> None:
    """Restore UTC tzinfo after SQLite/SQLAlchemy datetime roundtrip.

    These adapter unit tests use SQLite for speed. SQLite does not preserve
    timezone-aware datetimes in the same way PostgreSQL does for
    DateTime(timezone=True). The production model is PostgreSQL-oriented, so
    this helper keeps the test focused on adapter behavior instead of SQLite's
    datetime limitation.
    """
    for record in records:
        if record.recorded_at.tzinfo is None:
            record.recorded_at = record.recorded_at.replace(
                tzinfo=timezone.utc
            )

        if record.created_at is not None and record.created_at.tzinfo is None:
            record.created_at = record.created_at.replace(
                tzinfo=timezone.utc
            )


def test_list_recent_returns_audit_events(session: Session):
    audit_event = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    session.add(audit_event)
    session.flush()
    _restore_sqlite_datetime_timezone(audit_event)

    reader = SqlAlchemyAuditEventReader(session)

    audit_events = reader.list_recent(limit=50)

    assert len(audit_events) == 1
    assert isinstance(audit_events[0], AuditEvent)
    assert audit_events[0].id == ResourceId("audit-001")
    assert audit_events[0].agent == "system"
    assert audit_events[0].action == AuditAction.READ
    assert audit_events[0].entity.resource_type == "Patient"
    assert audit_events[0].entity.id == ResourceId("pat-001")


def test_list_recent_returns_empty_tuple_when_no_audit_events_exist(
    session: Session,
):
    reader = SqlAlchemyAuditEventReader(session)

    audit_events = reader.list_recent(limit=50)

    assert audit_events == ()


def test_list_recent_orders_events_by_recorded_at_desc(session: Session):
    older_event = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )
    newer_event = AuditEventRecord(
        id="audit-002",
        recorded_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="search",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    session.add_all([older_event, newer_event])
    session.flush()
    _restore_sqlite_datetime_timezone(older_event, newer_event)

    reader = SqlAlchemyAuditEventReader(session)

    audit_events = reader.list_recent(limit=50)

    assert tuple(event.id for event in audit_events) == (
        ResourceId("audit-002"),
        ResourceId("audit-001"),
    )


def test_list_recent_applies_limit(session: Session):
    first_event = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )
    second_event = AuditEventRecord(
        id="audit-002",
        recorded_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="search",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )
    third_event = AuditEventRecord(
        id="audit-003",
        recorded_at=datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="export",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    session.add_all([first_event, second_event, third_event])
    session.flush()
    _restore_sqlite_datetime_timezone(
        first_event,
        second_event,
        third_event,
    )

    reader = SqlAlchemyAuditEventReader(session)

    audit_events = reader.list_recent(limit=2)

    assert tuple(event.id for event in audit_events) == (
        ResourceId("audit-003"),
        ResourceId("audit-002"),
    )


def test_list_recent_maps_supported_actions(session: Session):
    read_event = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )
    search_event = AuditEventRecord(
        id="audit-002",
        recorded_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="search",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )
    export_event = AuditEventRecord(
        id="audit-003",
        recorded_at=datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="export",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    session.add_all([read_event, search_event, export_event])
    session.flush()
    _restore_sqlite_datetime_timezone(
        read_event,
        search_event,
        export_event,
    )

    reader = SqlAlchemyAuditEventReader(session)

    audit_events = reader.list_recent(limit=50)

    assert tuple(event.action for event in audit_events) == (
        AuditAction.EXPORT,
        AuditAction.SEARCH,
        AuditAction.READ,
    )


def test_list_recent_maps_supported_entity_resource_types(session: Session):
    patient_event = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )
    observation_event = AuditEventRecord(
        id="audit-002",
        recorded_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="read",
        entity_resource_type="Observation",
        entity_id="obs-001",
    )
    condition_event = AuditEventRecord(
        id="audit-003",
        recorded_at=datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="read",
        entity_resource_type="Condition",
        entity_id="cond-001",
    )
    encounter_event = AuditEventRecord(
        id="audit-004",
        recorded_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        agent="system",
        action="read",
        entity_resource_type="Encounter",
        entity_id="enc-001",
    )

    session.add_all(
        [
            patient_event,
            observation_event,
            condition_event,
            encounter_event,
        ]
    )
    session.flush()
    _restore_sqlite_datetime_timezone(
        patient_event,
        observation_event,
        condition_event,
        encounter_event,
    )

    reader = SqlAlchemyAuditEventReader(session)

    audit_events = reader.list_recent(limit=50)

    assert tuple(event.entity.resource_type for event in audit_events) == (
        "Encounter",
        "Condition",
        "Observation",
        "Patient",
    )
