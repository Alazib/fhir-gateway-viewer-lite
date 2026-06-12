from datetime import datetime, timezone

from fhir_gateway.domain.entities.audit_event import AuditAction, AuditEvent
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.audit_event import (
    audit_event_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.audit_event import (
    AuditEventRecord,
)


def test_audit_event_record_to_domain_returns_audit_event():
    record = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        agent="system:fhir-gateway",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    audit_event = audit_event_record_to_domain(record)

    assert isinstance(audit_event, AuditEvent)


def test_audit_event_record_to_domain_maps_id_to_resource_id():
    record = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        agent="system:fhir-gateway",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    audit_event = audit_event_record_to_domain(record)

    assert audit_event.id == ResourceId("audit-001")


def test_audit_event_record_to_domain_maps_recorded_at_to_recorded():
    recorded_at = datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc)

    record = AuditEventRecord(
        id="audit-001",
        recorded_at=recorded_at,
        agent="system:fhir-gateway",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    audit_event = audit_event_record_to_domain(record)

    assert audit_event.recorded == Instant(recorded_at)


def test_audit_event_record_to_domain_maps_agent():
    record = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        agent="system:fhir-gateway",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    audit_event = audit_event_record_to_domain(record)

    assert audit_event.agent == "system:fhir-gateway"


def test_audit_event_record_to_domain_maps_action_to_audit_action():
    record = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        agent="system:fhir-gateway",
        action="export",
        entity_resource_type="Patient",
        entity_id="pat-001",
    )

    audit_event = audit_event_record_to_domain(record)

    assert audit_event.action is AuditAction.EXPORT


def test_audit_event_record_to_domain_maps_entity_reference():
    record = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        agent="system:fhir-gateway",
        action="read",
        entity_resource_type="Observation",
        entity_id="obs-001",
    )

    audit_event = audit_event_record_to_domain(record)

    assert audit_event.entity == Reference(
        resource_type="Observation",
        id=ResourceId("obs-001"),
    )


def test_audit_event_record_to_domain_uses_recorded_at_not_created_at():
    recorded_at = datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc)
    created_at = datetime(2026, 6, 4, 11, 0, tzinfo=timezone.utc)

    record = AuditEventRecord(
        id="audit-001",
        recorded_at=recorded_at,
        agent="system:fhir-gateway",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
        created_at=created_at,
    )

    audit_event = audit_event_record_to_domain(record)

    assert audit_event.recorded == Instant(recorded_at)
    assert audit_event.recorded != Instant(created_at)


def test_audit_event_record_to_domain_ignores_technical_metadata():
    created_at = datetime(2026, 6, 4, 11, 0, tzinfo=timezone.utc)

    record = AuditEventRecord(
        id="audit-001",
        recorded_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        agent="system:fhir-gateway",
        action="read",
        entity_resource_type="Patient",
        entity_id="pat-001",
        created_at=created_at,
    )

    audit_event = audit_event_record_to_domain(record)

    assert not hasattr(audit_event, "created_at")
    assert not hasattr(audit_event, "updated_at")
    assert not hasattr(audit_event, "deleted_at")
