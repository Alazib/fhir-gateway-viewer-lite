from sqlalchemy import MetaData

from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base


def test_base_exposes_sqlalchemy_metadata():
    assert isinstance(Base.metadata, MetaData)
