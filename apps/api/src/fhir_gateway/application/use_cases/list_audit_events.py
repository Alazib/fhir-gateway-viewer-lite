from fhir_gateway.application.errors import ApplicationValidationError
from fhir_gateway.application.ports.audit_event_reader import AuditEventReader
from fhir_gateway.domain.entities.audit_event import AuditEvent


class ListAuditEventsUseCase:
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 100

    def __init__(self, audit_event_reader: AuditEventReader) -> None:
        self._audit_event_reader = audit_event_reader

    def execute(self, limit: int = DEFAULT_LIMIT) -> tuple[AuditEvent, ...]:

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ApplicationValidationError(
                "ListAuditEvents.limit",
                "must be an integer",
            )

        if limit < 1:
            raise ApplicationValidationError(
                "ListAuditEvents.limit",
                "must be greater than or equal to 1",
            )

        if limit > self.MAX_LIMIT:
            raise ApplicationValidationError(
                "ListAuditEvents.limit",
                f"must be less than or equal to {self.MAX_LIMIT}",
            )

        return self._audit_event_reader.list_recent(limit)
