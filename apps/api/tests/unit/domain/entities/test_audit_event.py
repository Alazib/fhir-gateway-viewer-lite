from datetime import datetime, timezone

import pytest

from fhir_gateway.domain.entities.audit_event import AuditAction, AuditEvent
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


################################### VALID CASES:


def test_accepts_valid_audit_event():
    audit_event = AuditEvent(
        id=ResourceId("aud-001"),
        recorded=Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)),
        agent="clinician-001",
        action=AuditAction.READ,
        entity=Reference(resource_type="Patient", id=ResourceId("pat-001")),
    )

    assert audit_event.id.value == "aud-001"
    assert audit_event.recorded.value == datetime(
        2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc
    )
    assert audit_event.agent == "clinician-001"
    assert audit_event.action is AuditAction.READ
    assert audit_event.entity.resource_type == "Patient"
    assert audit_event.entity.id.value == "pat-001"


def test_trims_agent():
    audit_event = AuditEvent(
        id=ResourceId("aud-002"),
        recorded=Instant(value=datetime(2026, 2, 14, 11, 0, 0, tzinfo=timezone.utc)),
        agent="  clinician-001  ",
        action=AuditAction.EXPORT,
        entity=Reference(resource_type="Observation", id=ResourceId("obs-001")),
    )

    assert audit_event.agent == "clinician-001"
    assert audit_event.action is AuditAction.EXPORT


################################### NOT VALID CASES:


def test_rejects_non_resource_id():
    with pytest.raises(DomainValidationError) as exc:
        AuditEvent(
            id="aud-001",  # type: ignore[arg-type]
            recorded=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            agent="clinician-001",
            action=AuditAction.READ,
            entity=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        )

    assert exc.value.field == "AuditEvent.id"
    assert exc.value.message == "must be a ResourceId"


def test_rejects_non_instant_recorded():
    with pytest.raises(DomainValidationError) as exc:
        AuditEvent(
            id=ResourceId("aud-001"),
            recorded=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc),  # type: ignore[arg-type]
            agent="clinician-001",
            action=AuditAction.READ,
            entity=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        )

    assert exc.value.field == "AuditEvent.recorded"
    assert exc.value.message == "must be an Instant"


def test_rejects_non_string_agent():
    with pytest.raises(DomainValidationError) as exc:
        AuditEvent(
            id=ResourceId("aud-001"),
            recorded=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            agent=1234,  # type: ignore[arg-type]
            action=AuditAction.READ,
            entity=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        )

    assert exc.value.field == "AuditEvent.agent"
    assert exc.value.message == "must be a string"


def test_rejects_empty_agent():
    with pytest.raises(DomainValidationError) as exc:
        AuditEvent(
            id=ResourceId("aud-001"),
            recorded=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            agent="   ",
            action=AuditAction.READ,
            entity=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        )

    assert exc.value.field == "AuditEvent.agent"
    assert exc.value.message == "cannot be empty"


def test_rejects_non_audit_action():
    with pytest.raises(DomainValidationError) as exc:
        AuditEvent(
            id=ResourceId("aud-001"),
            recorded=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            agent="clinician-001",
            action="read",  # type: ignore[arg-type]
            entity=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        )

    assert exc.value.field == "AuditEvent.action"
    assert exc.value.message == "must be an AuditAction"


def test_rejects_non_reference_entity():
    with pytest.raises(DomainValidationError) as exc:
        AuditEvent(
            id=ResourceId("aud-001"),
            recorded=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            agent="clinician-001",
            action=AuditAction.READ,
            entity="Patient/pat-001",  # type: ignore[arg-type]
        )

    assert exc.value.field == "AuditEvent.entity"
    assert exc.value.message == "must be a Reference"
