from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import pytest

from fhir_gateway.application.use_cases.export_patient_bundle import (
    ExportPatientBundleUseCase,
)
from fhir_gateway.application.use_cases.get_patient_summary import (
    GetPatientSummaryUseCase,
)
from fhir_gateway.application.use_cases.list_audit_events import (
    ListAuditEventsUseCase,
)
from fhir_gateway.application.use_cases.list_observations_by_code import (
    ListObservationsByCodeUseCase,
)
from fhir_gateway.application.use_cases.search_patients import (
    SearchPatientsUseCase,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.adapters import (
    SqlAlchemyAuditEventReader,
    SqlAlchemyConditionReader,
    SqlAlchemyEncounterReader,
    SqlAlchemyObservationReader,
    SqlAlchemyPatientReader,
)
from fhir_gateway.interfaces.http.dependencies.use_cases import (
    get_export_patient_bundle_use_case,
    get_list_audit_events_use_case,
    get_list_observations_by_code_use_case,
    get_patient_summary_use_case,
    get_search_patients_use_case,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def patient_reader(session: Session) -> SqlAlchemyPatientReader:
    return SqlAlchemyPatientReader(session)


@pytest.fixture
def observation_reader(session: Session) -> SqlAlchemyObservationReader:
    return SqlAlchemyObservationReader(session)


@pytest.fixture
def condition_reader(session: Session) -> SqlAlchemyConditionReader:
    return SqlAlchemyConditionReader(session)


@pytest.fixture
def encounter_reader(session: Session) -> SqlAlchemyEncounterReader:
    return SqlAlchemyEncounterReader(session)


@pytest.fixture
def audit_event_reader(session: Session) -> SqlAlchemyAuditEventReader:
    return SqlAlchemyAuditEventReader(session)


def test_get_search_patients_use_case_returns_use_case(
    patient_reader: SqlAlchemyPatientReader,
):
    use_case = get_search_patients_use_case(patient_reader)

    assert isinstance(use_case, SearchPatientsUseCase)
    assert use_case._patient_search_reader is patient_reader


def test_get_patient_summary_use_case_returns_use_case(
    patient_reader: SqlAlchemyPatientReader,
    condition_reader: SqlAlchemyConditionReader,
    encounter_reader: SqlAlchemyEncounterReader,
    observation_reader: SqlAlchemyObservationReader,
):
    use_case = get_patient_summary_use_case(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )

    assert isinstance(use_case, GetPatientSummaryUseCase)
    assert use_case._patient_reader is patient_reader
    assert use_case._condition_reader is condition_reader
    assert use_case._encounter_reader is encounter_reader
    assert use_case._observation_reader is observation_reader


def test_get_list_observations_by_code_use_case_returns_use_case(
    patient_reader: SqlAlchemyPatientReader,
    observation_reader: SqlAlchemyObservationReader,
):
    use_case = get_list_observations_by_code_use_case(
        patient_reader=patient_reader,
        observation_reader=observation_reader,
    )

    assert isinstance(use_case, ListObservationsByCodeUseCase)
    assert use_case._patient_reader is patient_reader
    assert use_case._observation_by_code_reader is observation_reader


def test_get_export_patient_bundle_use_case_returns_use_case(
    patient_reader: SqlAlchemyPatientReader,
    condition_reader: SqlAlchemyConditionReader,
    encounter_reader: SqlAlchemyEncounterReader,
    observation_reader: SqlAlchemyObservationReader,
):
    use_case = get_export_patient_bundle_use_case(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )

    assert isinstance(use_case, ExportPatientBundleUseCase)
    assert use_case._patient_reader is patient_reader
    assert use_case._condition_reader is condition_reader
    assert use_case._encounter_reader is encounter_reader
    assert use_case._observation_reader is observation_reader


def test_get_list_audit_events_use_case_returns_use_case(
    audit_event_reader: SqlAlchemyAuditEventReader,
):
    use_case = get_list_audit_events_use_case(audit_event_reader)

    assert isinstance(use_case, ListAuditEventsUseCase)
    assert use_case._audit_event_reader is audit_event_reader
