from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from fhir_gateway.infrastructure.persistence.sqlalchemy.adapters import (
    SqlAlchemyAuditEventReader,
    SqlAlchemyConditionReader,
    SqlAlchemyEncounterReader,
    SqlAlchemyObservationReader,
    SqlAlchemyPatientReader,
)
from fhir_gateway.interfaces.http.dependencies.database import (
    get_database_session,
)


def get_patient_reader(
    session: Annotated[Session, Depends(get_database_session)],
) -> SqlAlchemyPatientReader:
    return SqlAlchemyPatientReader(session)


def get_observation_reader(
    session: Annotated[Session, Depends(get_database_session)],
) -> SqlAlchemyObservationReader:
    return SqlAlchemyObservationReader(session)


def get_condition_reader(
    session: Annotated[Session, Depends(get_database_session)],
) -> SqlAlchemyConditionReader:
    return SqlAlchemyConditionReader(session)


def get_encounter_reader(
    session: Annotated[Session, Depends(get_database_session)],
) -> SqlAlchemyEncounterReader:
    return SqlAlchemyEncounterReader(session)


def get_audit_event_reader(
    session: Annotated[Session, Depends(get_database_session)],
) -> SqlAlchemyAuditEventReader:
    return SqlAlchemyAuditEventReader(session)
