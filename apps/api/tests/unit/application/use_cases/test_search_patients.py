import pytest

from fhir_gateway.application.errors import ApplicationValidationError
from fhir_gateway.application.use_cases.search_patients import SearchPatientsUseCase
from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.identifier import Identifier
from fhir_gateway.domain.value_objects.resource_id import ResourceId


#### FAKE ADAPTER (INFRASTRUCTURE LAYER):
class InMemoryPatientSearchReader:
    def __init__(self, patients: tuple[Patient, ...]) -> None:
        self.patients = patients
        self.received_search_text: str | None = None

    def search_by_text(self, search_text: str) -> tuple[Patient, ...]:
        self.received_search_text = search_text
        return self.patients


################################### VALID CASES:


def test_search_patients_returns_patients_from_reader():
    patient = Patient(
        id=ResourceId("pat-001"),
        identifiers=(Identifier(system="urn:mrn:hospital-x", value="MRN-000123"),),
        name=HumanName(given=("Ana",), family="García"),
    )
    reader = InMemoryPatientSearchReader(patients=(patient,))
    use_case = SearchPatientsUseCase(patient_search_reader=reader)

    result = use_case.execute("garcia")

    assert result == (patient,)
    assert reader.received_search_text == "garcia"


def test_search_patients_trims_search_text_before_calling_reader():
    patient = Patient(
        id=ResourceId("pat-001"),
        name=HumanName(given=("Ana",), family="García"),
    )
    reader = InMemoryPatientSearchReader(patients=(patient,))
    use_case = SearchPatientsUseCase(patient_search_reader=reader)

    result = use_case.execute("   garcia   ")

    assert result == (patient,)
    assert reader.received_search_text == "garcia"


def test_search_patients_returns_empty_tuple_when_reader_finds_nothing():
    reader = InMemoryPatientSearchReader(patients=())
    use_case = SearchPatientsUseCase(patient_search_reader=reader)

    result = use_case.execute("unknown")

    assert result == ()
    assert reader.received_search_text == "unknown"


################################### NOT VALID CASES:


def test_search_patients_rejects_non_string_search_text():
    reader = InMemoryPatientSearchReader(patients=())
    use_case = SearchPatientsUseCase(patient_search_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute(123)  # type: ignore[arg-type]

    assert exc.value.field == "SearchPatients.search_text"
    assert exc.value.message == "must be a string"


def test_search_patients_rejects_empty_search_text():
    reader = InMemoryPatientSearchReader(patients=())
    use_case = SearchPatientsUseCase(patient_search_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute("")

    assert exc.value.field == "SearchPatients.search_text"
    assert exc.value.message == "cannot be empty"


def test_search_patients_rejects_whitespace_only_search_text():
    reader = InMemoryPatientSearchReader(patients=())
    use_case = SearchPatientsUseCase(patient_search_reader=reader)

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute("     ")

    assert exc.value.field == "SearchPatients.search_text"
    assert exc.value.message == "cannot be empty"
