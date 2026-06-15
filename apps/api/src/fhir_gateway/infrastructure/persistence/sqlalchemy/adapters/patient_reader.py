from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.patient import (
    patient_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.patient import (
    PatientIdentifierRecord,
    PatientRecord,
)


class SqlAlchemyPatientReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, patient_id: ResourceId) -> Patient | None:
        stmt = (
            select(PatientRecord)
            .options(selectinload(PatientRecord.identifiers))
            .where(PatientRecord.id == patient_id.value)
            .where(PatientRecord.deleted_at.is_(None))
        )

        record = self._session.execute(stmt).scalar_one_or_none()

        if record is None:
            return None

        return patient_record_to_domain(record)

    def search_by_text(self, search_text: str) -> tuple[Patient, ...]:
        search_pattern = f"%{search_text}%"

        stmt = (
            select(PatientRecord)
            .outerjoin(PatientIdentifierRecord)
            .options(selectinload(PatientRecord.identifiers))
            .where(PatientRecord.deleted_at.is_(None))
            .where(
                or_(
                    PatientRecord.id.ilike(search_pattern),
                    PatientRecord.name_text.ilike(search_pattern),
                    PatientRecord.name_family.ilike(search_pattern),
                    PatientIdentifierRecord.system.ilike(search_pattern),
                    PatientIdentifierRecord.value.ilike(search_pattern),
                )
            )
            .distinct()
            .order_by(PatientRecord.id)
        )

        records = self._session.execute(stmt).scalars().all()

        return tuple(patient_record_to_domain(record) for record in records)
