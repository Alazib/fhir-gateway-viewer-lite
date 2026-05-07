from datetime import datetime, timezone

import pytest

from fhir_gateway.application.errors import ApplicationValidationError
from fhir_gateway.application.use_cases.list_audit_events import (
    ListAuditEventsUseCase,
)
from fhir_gateway.domain.entities.audit_event import AuditAction, AuditEvent
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class InMemoryAuditEventReader:
    def __init__(self, audit_events: tuple[AuditEvent, ...]) -> None:
        self.audit_events = audit_events
        self.received_limit: int | None = None

    def list_recent(self, limit: int) -> tuple[AuditEvent, ...]:
        self.received_limit = limit

        return tuple(
            sorted(
                self.audit_events,
                key=lambda audit_event: audit_event.recorded.value,
                reverse=True,
            )[:limit],
        )


def _build_instant(year: int, month: int, day: int, hour: int, minute: int) -> Instant:
    return Instant(
        value=datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc),
    )


def _build_patient_reference(patient_id: str = "pat-001") -> Reference:
    return Reference(
        resource_type="Patient",
        id=ResourceId(patient_id),
    )


def _build_audit_event(
    audit_event_id: str,
    recorded: Instant,
    agent: str = "doctor.alvarez",
    action: AuditAction = AuditAction.READ,
    patient_id: str = "pat-001",
) -> AuditEvent:
    return AuditEvent(
        id=ResourceId(audit_event_id),
        recorded=recorded,
        agent=agent,
        action=action,
        entity=_build_patient_reference(patient_id),
    )


###################################
# VALID CASES:


def test_list_audit_events_returns_recent_audit_events_newest_first():
    oldest_event = _build_audit_event(
        audit_event_id="aud-001",
        recorded=_build_instant(2026, 5, 2, 9, 10),
        action=AuditAction.SEARCH,
    )
    middle_event = _build_audit_event(
        audit_event_id="aud-002",
        recorded=_build_instant(2026, 5, 2, 9, 12),
        action=AuditAction.READ,
    )
    newest_event = _build_audit_event(
        audit_event_id="aud-003",
        recorded=_build_instant(2026, 5, 2, 9, 15),
        action=AuditAction.EXPORT,
    )

    reader = InMemoryAuditEventReader(
        audit_events=(oldest_event, newest_event, middle_event),
    )
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    result = use_case.execute(limit=2)

    assert result == (newest_event, middle_event)


def test_list_audit_events_returns_empty_tuple_when_there_are_no_events():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    result = use_case.execute()

    assert result == ()


def test_list_audit_events_uses_default_limit_when_none_is_provided():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    use_case.execute()

    assert reader.received_limit == ListAuditEventsUseCase.DEFAULT_LIMIT


def test_list_audit_events_passes_explicit_limit_to_reader():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    use_case.execute(limit=25)

    assert reader.received_limit == 25


def test_list_audit_events_accepts_max_limit():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    use_case.execute(limit=ListAuditEventsUseCase.MAX_LIMIT)

    assert reader.received_limit == ListAuditEventsUseCase.MAX_LIMIT


###################################
# NOT VALID CASES:


def test_list_audit_events_rejects_non_integer_limit():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute(limit="50")  # type: ignore[arg-type]

    assert exc.value.field == "ListAuditEvents.limit"
    assert exc.value.message == "must be an integer"


def test_list_audit_events_rejects_float_limit():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute(limit=50.0)  # type: ignore[arg-type]

    assert exc.value.field == "ListAuditEvents.limit"
    assert exc.value.message == "must be an integer"


def test_list_audit_events_rejects_boolean_limit():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute(limit=True)  # type: ignore[arg-type]

    assert exc.value.field == "ListAuditEvents.limit"
    assert exc.value.message == "must be an integer"


def test_list_audit_events_rejects_limit_lower_than_one():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute(limit=0)

    assert exc.value.field == "ListAuditEvents.limit"
    assert exc.value.message == "must be greater than or equal to 1"


def test_list_audit_events_rejects_negative_limit():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute(limit=-1)

    assert exc.value.field == "ListAuditEvents.limit"
    assert exc.value.message == "must be greater than or equal to 1"


def test_list_audit_events_rejects_limit_greater_than_max_limit():
    reader = InMemoryAuditEventReader(audit_events=())
    use_case = ListAuditEventsUseCase(audit_event_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute(limit=ListAuditEventsUseCase.MAX_LIMIT + 1)

    assert exc.value.field == "ListAuditEvents.limit"
    assert exc.value.message == (
        f"must be less than or equal to {ListAuditEventsUseCase.MAX_LIMIT}"
    )
