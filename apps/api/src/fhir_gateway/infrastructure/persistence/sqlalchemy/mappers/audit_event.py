from fhir_gateway.domain.entities.audit_event import AuditAction, AuditEvent
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.audit_event import (
    AuditEventRecord,
)


def audit_event_record_to_domain(record: AuditEventRecord) -> AuditEvent:
    return AuditEvent(
        id=ResourceId(record.id),
        recorded=Instant(record.recorded_at),
        agent=record.agent,
        action=AuditAction(record.action),
        entity=Reference(
            resource_type=record.entity_resource_type,
            id=ResourceId(record.entity_id),
        ),
    )
