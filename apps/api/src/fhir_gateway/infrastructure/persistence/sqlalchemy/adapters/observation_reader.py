from sqlalchemy import select
from sqlalchemy.orm import Session

from fhir_gateway.domain.entities.observation import Observation
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.observation import (
    observation_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.observation import (
    ObservationCodeRecord,
    ObservationRecord,
)


class SqlAlchemyObservationReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_patient(
        self,
        patient_id: ResourceId,
    ) -> tuple[Observation, ...]:
        stmt = (
            select(ObservationRecord, ObservationCodeRecord)
            .join(
                ObservationCodeRecord,
                ObservationRecord.code_id == ObservationCodeRecord.id,
            )
            .where(ObservationRecord.patient_id == patient_id.value)
            .where(ObservationRecord.deleted_at.is_(None))
            .order_by(
                ObservationRecord.effective_at,
                ObservationRecord.id,
            )
        )

        rows = self._session.execute(stmt).all()

        return tuple(
            observation_record_to_domain(
                observation_record,
                code_record,
            )
            for observation_record, code_record in rows
        )

    def list_by_patient_and_code(
        self,
        patient_id: ResourceId,
        code: Code,
    ) -> tuple[Observation, ...]:
        stmt = (
            select(ObservationRecord, ObservationCodeRecord)
            .join(
                ObservationCodeRecord,
                ObservationRecord.code_id == ObservationCodeRecord.id,
            )
            .where(ObservationRecord.patient_id == patient_id.value)
            .where(ObservationRecord.deleted_at.is_(None))
            .where(ObservationCodeRecord.system == code.system)
            .where(ObservationCodeRecord.code == code.code)
            .order_by(
                ObservationRecord.effective_at,
                ObservationRecord.id,
            )
        )

        rows = self._session.execute(stmt).all()

        return tuple(
            observation_record_to_domain(
                observation_record,
                code_record,
            )
            for observation_record, code_record in rows
        )
