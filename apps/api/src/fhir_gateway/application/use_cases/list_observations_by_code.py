from fhir_gateway.application.errors import (
    ApplicationNotFoundError,
    ApplicationValidationError,
)
from fhir_gateway.application.ports.observation_by_code_reader import (
    ObservationByCodeReader,
)
from fhir_gateway.application.ports.patient_reader import PatientReader
from fhir_gateway.domain.entities.observation import Observation
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class ListObservationsByCodeUseCase:
    def __init__(
        self,
        patient_reader: PatientReader,
        observation_by_code_reader: ObservationByCodeReader,
    ) -> None:
        self._patient_reader = patient_reader
        self._observation_by_code_reader = observation_by_code_reader

    def execute(
        self,
        patient_id: ResourceId,
        code: Code,
    ) -> tuple[Observation, ...]:

        if not isinstance(patient_id, ResourceId):
            raise ApplicationValidationError(
                "ListObservationsByCode.patient_id",
                "must be a ResourceId",
            )

        if not isinstance(code, Code):
            raise ApplicationValidationError(
                "ListObservationsByCode.code",
                "must be a Code",
            )

        patient = self._patient_reader.get_by_id(patient_id)

        if patient is None:
            raise ApplicationNotFoundError("Patient", patient_id.value)

        return self._observation_by_code_reader.list_by_patient_and_code(
            patient_id,
            code,
        )
