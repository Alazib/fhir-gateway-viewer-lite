from sqlalchemy import select
from sqlalchemy.orm import Session

from fhir_gateway.domain.entities.audit_event import AuditEvent
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.audit_event import (
    audit_event_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.audit_event import (
    AuditEventRecord,
)


class SqlAlchemyAuditEventReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_recent(self, limit: int) -> tuple[AuditEvent, ...]:
        stmt = (
            select(AuditEventRecord)
            .order_by(
                AuditEventRecord.recorded_at.desc(),
                AuditEventRecord.id,
            )
            .limit(limit)
        )

        records = self._session.execute(stmt).scalars().all()

        return tuple(
            audit_event_record_to_domain(record)
            for record in records
        )
