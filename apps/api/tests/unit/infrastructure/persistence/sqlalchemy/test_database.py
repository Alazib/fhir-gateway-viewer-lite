from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from fhir_gateway.infrastructure.persistence.sqlalchemy.database import (
    create_database_engine,
    create_session_factory,
)


def test_create_database_engine_returns_sqlalchemy_engine():
    engine = create_database_engine("sqlite:///:memory:")

    assert isinstance(engine, Engine)


def test_create_session_factory_returns_sessionmaker():
    engine = create_database_engine("sqlite:///:memory:")

    session_factory = create_session_factory(engine)

    assert isinstance(session_factory, sessionmaker)


def test_session_factory_creates_working_session():
    engine = create_database_engine("sqlite:///:memory:")
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        result = session.execute(text("SELECT 1")).scalar_one()

    assert isinstance(session, Session)
    assert result == 1
