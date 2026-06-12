from fhir_gateway.domain.entities.encounter import Encounter
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.period import Period
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.encounter import (
    EncounterRecord,
)


def encounter_record_to_domain(record: EncounterRecord) -> Encounter:
    return Encounter(
        id=ResourceId(record.id),
        subject=Reference(
            resource_type="Patient",
            id=ResourceId(record.patient_id),
        ),
        period=Period(
            start=Instant(record.period_start_at),
            end=(
                Instant(record.period_end_at)
                if record.period_end_at is not None
                else None
            ),
        ),
    )
