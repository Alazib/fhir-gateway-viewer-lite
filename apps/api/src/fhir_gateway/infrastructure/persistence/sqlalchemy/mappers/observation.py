from fhir_gateway.domain.entities.observation import (
    Observation,
    ObservationStatus,
)
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.quantity import Quantity
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.observation import (
    ObservationCodeRecord,
    ObservationRecord,
)


def observation_record_to_domain(
    record: ObservationRecord,
    code_record: ObservationCodeRecord,
) -> Observation:
    if record.code_id != code_record.id:
        raise ValueError(
            "ObservationRecord.code_id must match ObservationCodeRecord.id"
        )

    return Observation(
        id=ResourceId(record.id),
        status=ObservationStatus(record.status),
        code=_observation_code_to_domain(code_record),
        subject=Reference(
            resource_type="Patient",
            id=ResourceId(record.patient_id),
        ),
        effective=Instant(record.effective_at),
        value=Quantity(
            value=record.value_quantity,
            unit=record.value_unit,
        ),
    )


def _observation_code_to_domain(
    code_record: ObservationCodeRecord,
) -> Code:
    return Code(
        system=code_record.system,
        code=code_record.code,
        display=code_record.display,
    )
