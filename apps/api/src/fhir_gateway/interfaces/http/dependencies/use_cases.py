from typing import Annotated

from fastapi import Depends

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
from fhir_gateway.interfaces.http.dependencies.adapters import (
    get_audit_event_reader,
    get_condition_reader,
    get_encounter_reader,
    get_observation_reader,
    get_patient_reader,
)


def get_search_patients_use_case(
    patient_reader: Annotated[
        SqlAlchemyPatientReader,
        Depends(get_patient_reader),
    ],
) -> SearchPatientsUseCase:
    return SearchPatientsUseCase(patient_reader)


def get_patient_summary_use_case(
    patient_reader: Annotated[
        SqlAlchemyPatientReader,
        Depends(get_patient_reader),
    ],
    condition_reader: Annotated[
        SqlAlchemyConditionReader,
        Depends(get_condition_reader),
    ],
    encounter_reader: Annotated[
        SqlAlchemyEncounterReader,
        Depends(get_encounter_reader),
    ],
    observation_reader: Annotated[
        SqlAlchemyObservationReader,
        Depends(get_observation_reader),
    ],
) -> GetPatientSummaryUseCase:
    return GetPatientSummaryUseCase(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )


def get_list_observations_by_code_use_case(
    patient_reader: Annotated[
        SqlAlchemyPatientReader,
        Depends(get_patient_reader),
    ],
    observation_reader: Annotated[
        SqlAlchemyObservationReader,
        Depends(get_observation_reader),
    ],
) -> ListObservationsByCodeUseCase:
    return ListObservationsByCodeUseCase(
        patient_reader=patient_reader,
        observation_by_code_reader=observation_reader,
    )


def get_export_patient_bundle_use_case(
    patient_reader: Annotated[
        SqlAlchemyPatientReader,
        Depends(get_patient_reader),
    ],
    condition_reader: Annotated[
        SqlAlchemyConditionReader,
        Depends(get_condition_reader),
    ],
    encounter_reader: Annotated[
        SqlAlchemyEncounterReader,
        Depends(get_encounter_reader),
    ],
    observation_reader: Annotated[
        SqlAlchemyObservationReader,
        Depends(get_observation_reader),
    ],
) -> ExportPatientBundleUseCase:
    return ExportPatientBundleUseCase(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )


def get_list_audit_events_use_case(
    audit_event_reader: Annotated[
        SqlAlchemyAuditEventReader,
        Depends(get_audit_event_reader),
    ],
) -> ListAuditEventsUseCase:
    return ListAuditEventsUseCase(audit_event_reader)
