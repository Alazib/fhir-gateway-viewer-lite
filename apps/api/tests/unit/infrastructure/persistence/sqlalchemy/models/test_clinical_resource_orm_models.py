from sqlalchemy import CheckConstraint, DateTime

from fhir_gateway.domain.entities.observation import ObservationStatus
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import TimestampMixin
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.condition import (
    ConditionRecord,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.encounter import (
    EncounterRecord,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.observation import (
    OBSERVATION_STATUS_VALUES,
    ObservationRecord,
)


def _foreign_key_targets(column) -> set[str]:
    return {str(foreign_key.column) for foreign_key in column.foreign_keys}


def _foreign_key_ondelete(column) -> set[str | None]:
    return {foreign_key.ondelete for foreign_key in column.foreign_keys}


def _check_constraint_names(table) -> set[str]:
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def _index_columns_by_name(table) -> dict[str, tuple[str, ...]]:
    return {
        index.name: tuple(column.name for column in index.columns)
        for index in table.indexes
    }


def test_clinical_resource_tables_are_registered_in_metadata():
    assert "observations" in Base.metadata.tables
    assert "conditions" in Base.metadata.tables
    assert "encounters" in Base.metadata.tables


def test_clinical_resource_records_use_timestamp_mixin():
    assert issubclass(ObservationRecord, TimestampMixin)
    assert issubclass(ConditionRecord, TimestampMixin)
    assert issubclass(EncounterRecord, TimestampMixin)


def test_observation_status_values_match_domain_enum():
    assert OBSERVATION_STATUS_VALUES == tuple(
        status.value for status in ObservationStatus
    )


def test_observations_table_has_expected_columns():
    table = ObservationRecord.__table__

    assert set(table.columns.keys()) == {
        "id",
        "patient_id",
        "status",
        "code_id",
        "effective_at",
        "value_quantity",
        "value_unit",
        "created_at",
        "updated_at",
    }


def test_conditions_table_has_expected_columns():
    table = ConditionRecord.__table__

    assert set(table.columns.keys()) == {
        "id",
        "patient_id",
        "code_id",
        "recorded_at",
        "created_at",
        "updated_at",
    }


def test_encounters_table_has_expected_columns():
    table = EncounterRecord.__table__

    assert set(table.columns.keys()) == {
        "id",
        "patient_id",
        "period_start_at",
        "period_end_at",
        "created_at",
        "updated_at",
    }


def test_observations_table_has_expected_required_and_nullable_columns():
    table = ObservationRecord.__table__

    assert table.c.id.primary_key
    assert not table.c.patient_id.nullable
    assert not table.c.status.nullable
    assert not table.c.code_id.nullable
    assert not table.c.effective_at.nullable
    assert table.c.value_quantity.nullable
    assert table.c.value_unit.nullable
    assert not table.c.created_at.nullable
    assert not table.c.updated_at.nullable


def test_conditions_table_has_expected_required_and_nullable_columns():
    table = ConditionRecord.__table__

    assert table.c.id.primary_key
    assert not table.c.patient_id.nullable
    assert not table.c.code_id.nullable
    assert table.c.recorded_at.nullable
    assert not table.c.created_at.nullable
    assert not table.c.updated_at.nullable


def test_encounters_table_has_expected_required_and_nullable_columns():
    table = EncounterRecord.__table__

    assert table.c.id.primary_key
    assert not table.c.patient_id.nullable
    assert not table.c.period_start_at.nullable
    assert table.c.period_end_at.nullable
    assert not table.c.created_at.nullable
    assert not table.c.updated_at.nullable


def test_clinical_resource_datetime_columns_are_timezone_aware():
    observation_table = ObservationRecord.__table__
    condition_table = ConditionRecord.__table__
    encounter_table = EncounterRecord.__table__

    assert isinstance(observation_table.c.effective_at.type, DateTime)
    assert observation_table.c.effective_at.type.timezone

    assert isinstance(condition_table.c.recorded_at.type, DateTime)
    assert condition_table.c.recorded_at.type.timezone

    assert isinstance(encounter_table.c.period_start_at.type, DateTime)
    assert encounter_table.c.period_start_at.type.timezone

    assert isinstance(encounter_table.c.period_end_at.type, DateTime)
    assert encounter_table.c.period_end_at.type.timezone


def test_observations_table_references_patients_and_observation_codes():
    table = ObservationRecord.__table__

    assert _foreign_key_targets(table.c.patient_id) == {"patients.id"}
    assert _foreign_key_ondelete(table.c.patient_id) == {"CASCADE"}

    assert _foreign_key_targets(table.c.code_id) == {"observation_codes.id"}
    assert _foreign_key_ondelete(table.c.code_id) == {None}


def test_conditions_table_references_patients_and_condition_codes():
    table = ConditionRecord.__table__

    assert _foreign_key_targets(table.c.patient_id) == {"patients.id"}
    assert _foreign_key_ondelete(table.c.patient_id) == {"CASCADE"}

    assert _foreign_key_targets(table.c.code_id) == {"condition_codes.id"}
    assert _foreign_key_ondelete(table.c.code_id) == {None}


def test_encounters_table_references_patients():
    table = EncounterRecord.__table__

    assert _foreign_key_targets(table.c.patient_id) == {"patients.id"}
    assert _foreign_key_ondelete(table.c.patient_id) == {"CASCADE"}


def test_observations_table_has_expected_check_constraints():
    table = ObservationRecord.__table__

    assert "ck_observations_status_allowed" in _check_constraint_names(table)
    assert (
        "ck_observations_value_quantity_requires_unit"
        in _check_constraint_names(table)
    )


def test_encounters_table_has_expected_check_constraints():
    table = EncounterRecord.__table__

    assert "ck_encounters_period_start_before_end" in _check_constraint_names(table)


def test_observations_table_has_expected_indexes():
    table = ObservationRecord.__table__

    indexes = _index_columns_by_name(table)

    assert indexes["ix_observations_patient_id"] == ("patient_id",)
    assert indexes["ix_observations_patient_code"] == ("patient_id", "code_id")
    assert indexes["ix_observations_patient_effective_at"] == (
        "patient_id",
        "effective_at",
    )


def test_conditions_table_has_expected_indexes():
    table = ConditionRecord.__table__

    indexes = _index_columns_by_name(table)

    assert indexes["ix_conditions_patient_id"] == ("patient_id",)
    assert indexes["ix_conditions_patient_code"] == ("patient_id", "code_id")


def test_encounters_table_has_expected_indexes():
    table = EncounterRecord.__table__

    indexes = _index_columns_by_name(table)

    assert indexes["ix_encounters_patient_id"] == ("patient_id",)
    assert indexes["ix_encounters_patient_period_start_at"] == (
        "patient_id",
        "period_start_at",
    )


def test_clinical_resource_timestamp_columns_keep_expected_defaults():
    for table in (
        ObservationRecord.__table__,
        ConditionRecord.__table__,
        EncounterRecord.__table__,
    ):
        assert table.c.created_at.server_default is not None
        assert table.c.updated_at.server_default is not None
        assert table.c.updated_at.onupdate is not None
