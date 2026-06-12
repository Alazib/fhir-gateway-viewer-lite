from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.identifier import Identifier
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.patient import (
    PatientRecord,
)


def patient_record_to_domain(record: PatientRecord) -> Patient:
    return Patient(
        id=ResourceId(record.id),
        identifiers=_patient_identifiers_to_domain(record),
        name=_patient_name_to_domain(record),
    )


def _patient_identifiers_to_domain(
    record: PatientRecord,
) -> tuple[Identifier, ...]:
    return tuple(
        Identifier(
            system=identifier_record.system,
            value=identifier_record.value,
        )
        for identifier_record in record.identifiers
    )


def _patient_name_to_domain(record: PatientRecord) -> HumanName | None:
    name_text = record.name_text
    name_family = record.name_family
    name_given = tuple(record.name_given or ())

    if name_text is None and name_family is None and not name_given:
        return None

    return HumanName(
        given=name_given,
        family=name_family,
        text=name_text,
    )
