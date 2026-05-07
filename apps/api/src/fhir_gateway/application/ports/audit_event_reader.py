from typing import Protocol

from fhir_gateway.domain.entities.audit_event import AuditEvent


class AuditEventReader(Protocol):
    def list_recent(self, limit: int) -> tuple[AuditEvent, ...]: ...
