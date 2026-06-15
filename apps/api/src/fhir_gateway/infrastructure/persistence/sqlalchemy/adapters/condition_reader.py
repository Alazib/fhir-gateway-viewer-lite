from sqlalchemy import select
from sqlalchemy.orm import Session

from fhir_gateway.domain.entities.condition import Condition
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.condition import (
    condition_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.condition import (
    ConditionCodeRecord,
    ConditionRecord,
)


class SqlAlchemyConditionReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_patient(
        self,
        patient_id: ResourceId,
    ) -> tuple[Condition, ...]:
        stmt = (
            select(ConditionRecord, ConditionCodeRecord)
            .join(
                ConditionCodeRecord,
                ConditionRecord.code_id == ConditionCodeRecord.id,
            )
            .where(ConditionRecord.patient_id == patient_id.value)
            .where(ConditionRecord.deleted_at.is_(None))
            .order_by(
                ConditionRecord.recorded_at,
                ConditionRecord.id,
            )
        )

        rows = self._session.execute(stmt).all()

        return tuple(
            condition_record_to_domain(
                condition_record,
                code_record,
            )
            for condition_record, code_record in rows
        )
