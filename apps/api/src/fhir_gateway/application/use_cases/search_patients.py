from fhir_gateway.application.errors import ApplicationValidationError
from fhir_gateway.application.ports.patient_search_reader import PatientSearchReader
from fhir_gateway.domain.entities.patient import Patient


class SearchPatientsUseCase:
    def __init__(self, patient_search_reader: PatientSearchReader) -> None:
        self._patient_search_reader = patient_search_reader

    def execute(self, search_text: str) -> tuple[Patient, ...]:
        if not isinstance(search_text, str):
            raise ApplicationValidationError(
                "SearchPatients.search_text",
                "must be a string",
            )

        cleaned_search_text = search_text.strip()

        if cleaned_search_text == "":
            raise ApplicationValidationError(
                "SearchPatients.search_text",
                "cannot be empty",
            )

        return self._patient_search_reader.search_by_text(cleaned_search_text)
