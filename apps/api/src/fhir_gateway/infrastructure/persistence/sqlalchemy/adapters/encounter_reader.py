from sqlalchemy import select
from sqlalchemy.orm import Session

from fhir_gateway.domain.entities.encounter import Encounter
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.encounter import (
    encounter_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.encounter import (
    EncounterRecord,
)


class SqlAlchemyEncounterReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_patient(
        self,
        patient_id: ResourceId,
    ) -> tuple[Encounter, ...]:
        stmt = (
            select(EncounterRecord)
            .where(EncounterRecord.patient_id == patient_id.value)
            .where(EncounterRecord.deleted_at.is_(None))
            .order_by(
                EncounterRecord.period_start_at,
                EncounterRecord.id,
            )
        )

        records = self._session.execute(stmt).scalars().all()

        return tuple(
            encounter_record_to_domain(record)
            for record in records
        )
