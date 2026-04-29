from fhir_gateway.application.errors import (
    ApplicationNotFoundError,
    ApplicationValidationError,
)
from fhir_gateway.application.models.patient_summary import PatientSummary
from fhir_gateway.application.ports.condition_reader import ConditionReader
from fhir_gateway.application.ports.encounter_reader import EncounterReader
from fhir_gateway.application.ports.observation_reader import ObservationReader
from fhir_gateway.application.ports.patient_reader import PatientReader
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class GetPatientSummaryUseCase:
    def __init__(
        self,
        patient_reader: PatientReader,
        condition_reader: ConditionReader,
        encounter_reader: EncounterReader,
        observation_reader: ObservationReader,
    ) -> None:
        self._patient_reader = patient_reader
        self._condition_reader = condition_reader
        self._encounter_reader = encounter_reader
        self._observation_reader = observation_reader

    def execute(self, patient_id: ResourceId) -> PatientSummary:
        if not isinstance(patient_id, ResourceId):
            raise ApplicationValidationError(
                "GetPatientSummary.patient_id",
                "must be a ResourceId",
            )

        patient = self._patient_reader.get_by_id(patient_id)

        if patient is None:
            raise ApplicationNotFoundError("Patient", patient_id.value)

        conditions = self._condition_reader.list_by_patient(patient_id)
        encounters = self._encounter_reader.list_by_patient(patient_id)
        observations = self._observation_reader.list_by_patient(patient_id)

        return PatientSummary(
            patient=patient,
            conditions=conditions,
            encounters=encounters,
            observations=observations,
        )
