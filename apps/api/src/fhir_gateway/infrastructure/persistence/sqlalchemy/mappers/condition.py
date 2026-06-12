from fhir_gateway.domain.entities.condition import Condition
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.condition import (
    ConditionCodeRecord,
    ConditionRecord,
)


def condition_record_to_domain(
    record: ConditionRecord,
    code_record: ConditionCodeRecord,
) -> Condition:
    if record.code_id != code_record.id:
        raise ValueError(
            "ConditionRecord.code_id must match ConditionCodeRecord.id"
        )

    return Condition(
        id=ResourceId(record.id),
        code=_condition_code_to_domain(code_record),
        subject=Reference(
            resource_type="Patient",
            id=ResourceId(record.patient_id),
        ),
        recorded_date=(
            Instant(record.recorded_at)
            if record.recorded_at is not None
            else None
        ),
    )


def _condition_code_to_domain(
    code_record: ConditionCodeRecord,
) -> Code:
    return Code(
        system=code_record.system,
        code=code_record.code,
        display=code_record.display,
    )
