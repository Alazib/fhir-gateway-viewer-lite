from collections.abc import Callable

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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


@pytest.mark.parametrize(
    ("dependency", "expected_type"),
    [
        (get_patient_reader, SqlAlchemyPatientReader),
        (get_observation_reader, SqlAlchemyObservationReader),
        (get_condition_reader, SqlAlchemyConditionReader),
        (get_encounter_reader, SqlAlchemyEncounterReader),
        (get_audit_event_reader, SqlAlchemyAuditEventReader),
    ],
)
def test_adapter_dependency_returns_expected_reader(
    session: Session,
    dependency: Callable[[Session], object],
    expected_type: type[object],
):
    reader = dependency(session)

    assert isinstance(reader, expected_type)
    assert reader._session is session
