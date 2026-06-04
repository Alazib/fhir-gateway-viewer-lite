from sqlalchemy import DateTime, UniqueConstraint

from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import TimestampMixin
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.condition import (
    ConditionCodeRecord,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.observation import (
    ObservationCodeRecord,
)


def test_code_catalog_tables_are_registered_in_metadata():
    assert "observation_codes" in Base.metadata.tables
    assert "condition_codes" in Base.metadata.tables


def test_observation_code_record_uses_timestamp_mixin():
    assert issubclass(ObservationCodeRecord, TimestampMixin)


def test_condition_code_record_uses_timestamp_mixin():
    assert issubclass(ConditionCodeRecord, TimestampMixin)


def test_observation_codes_table_has_expected_columns():
    table = ObservationCodeRecord.__table__

    assert set(table.columns.keys()) == {
        "id",
        "system",
        "code",
        "display",
        "created_at",
        "updated_at",
    }


def test_condition_codes_table_has_expected_columns():
    table = ConditionCodeRecord.__table__

    assert set(table.columns.keys()) == {
        "id",
        "system",
        "code",
        "display",
        "created_at",
        "updated_at",
    }


def test_observation_codes_table_does_not_have_deleted_at():
    table = ObservationCodeRecord.__table__

    assert "deleted_at" not in table.columns


def test_condition_codes_table_does_not_have_deleted_at():
    table = ConditionCodeRecord.__table__

    assert "deleted_at" not in table.columns


def test_observation_codes_table_has_expected_primary_key_and_required_columns():
    table = ObservationCodeRecord.__table__

    assert table.c.id.primary_key
    assert not table.c.system.nullable
    assert not table.c.code.nullable
    assert table.c.display.nullable
    assert not table.c.created_at.nullable
    assert not table.c.updated_at.nullable


def test_condition_codes_table_has_expected_primary_key_and_required_columns():
    table = ConditionCodeRecord.__table__

    assert table.c.id.primary_key
    assert not table.c.system.nullable
    assert not table.c.code.nullable
    assert table.c.display.nullable
    assert not table.c.created_at.nullable
    assert not table.c.updated_at.nullable


def test_observation_codes_table_has_timezone_aware_timestamp_columns():
    table = ObservationCodeRecord.__table__

    assert isinstance(table.c.created_at.type, DateTime)
    assert isinstance(table.c.updated_at.type, DateTime)
    assert table.c.created_at.type.timezone
    assert table.c.updated_at.type.timezone


def test_condition_codes_table_has_timezone_aware_timestamp_columns():
    table = ConditionCodeRecord.__table__

    assert isinstance(table.c.created_at.type, DateTime)
    assert isinstance(table.c.updated_at.type, DateTime)
    assert table.c.created_at.type.timezone
    assert table.c.updated_at.type.timezone


def test_observation_codes_timestamp_columns_keep_expected_defaults():
    table = ObservationCodeRecord.__table__

    assert table.c.created_at.server_default is not None
    assert table.c.updated_at.server_default is not None
    assert table.c.updated_at.onupdate is not None


def test_condition_codes_timestamp_columns_keep_expected_defaults():
    table = ConditionCodeRecord.__table__

    assert table.c.created_at.server_default is not None
    assert table.c.updated_at.server_default is not None
    assert table.c.updated_at.onupdate is not None


def test_observation_codes_table_has_unique_system_code_constraint():
    table = ObservationCodeRecord.__table__

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    unique_constraint_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in unique_constraints
    }

    assert ("system", "code") in unique_constraint_columns


def test_condition_codes_table_has_unique_system_code_constraint():
    table = ConditionCodeRecord.__table__

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    unique_constraint_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in unique_constraints
    }

    assert ("system", "code") in unique_constraint_columns
