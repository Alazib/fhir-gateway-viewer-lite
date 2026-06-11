from sqlalchemy import CheckConstraint, DateTime

from fhir_gateway.domain.entities.audit_event import AuditAction
from fhir_gateway.domain.value_objects.reference import ALLOWED_REFERENCE_RESOURCE_TYPES
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import (
    LogicalDeletionMixin,
    TimestampMixin,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.audit_event import (
    AUDIT_ACTION_VALUES,
    AUDIT_ENTITY_RESOURCE_TYPE_VALUES,
    AuditEventRecord,
)


def _check_constraint_names(table) -> set[str]:
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def _check_constraint_sql_by_name(table) -> dict[str, str]:
    return {
        constraint.name: str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def _index_columns_by_name(table) -> dict[str, tuple[str, ...]]:
    return {
        index.name: tuple(column.name for column in index.columns)
        for index in table.indexes
    }


def test_audit_events_table_is_registered_in_metadata():
    assert "audit_events" in Base.metadata.tables


def test_audit_event_record_uses_expected_table_name():
    assert AuditEventRecord.__tablename__ == "audit_events"
    assert AuditEventRecord.__table__ is Base.metadata.tables["audit_events"]


def test_audit_event_record_does_not_use_timestamp_mixin():
    assert not issubclass(AuditEventRecord, TimestampMixin)


def test_audit_event_record_does_not_use_logical_deletion_mixin():
    assert not issubclass(AuditEventRecord, LogicalDeletionMixin)


def test_audit_events_table_has_expected_columns():
    table = AuditEventRecord.__table__

    assert set(table.columns.keys()) == {
        "id",
        "recorded_at",
        "agent",
        "action",
        "entity_resource_type",
        "entity_id",
        "created_at",
    }


def test_audit_events_table_does_not_have_updated_at_or_deleted_at():
    table = AuditEventRecord.__table__

    assert "updated_at" not in table.columns
    assert "deleted_at" not in table.columns


def test_audit_events_table_has_expected_primary_key_and_required_columns():
    table = AuditEventRecord.__table__

    assert table.c.id.primary_key
    assert not table.c.recorded_at.nullable
    assert not table.c.agent.nullable
    assert not table.c.action.nullable
    assert not table.c.entity_resource_type.nullable
    assert not table.c.entity_id.nullable
    assert not table.c.created_at.nullable


def test_audit_events_datetime_columns_are_timezone_aware():
    table = AuditEventRecord.__table__

    assert isinstance(table.c.recorded_at.type, DateTime)
    assert isinstance(table.c.created_at.type, DateTime)
    assert table.c.recorded_at.type.timezone
    assert table.c.created_at.type.timezone


def test_audit_events_created_at_has_server_default_but_no_onupdate():
    table = AuditEventRecord.__table__

    assert table.c.created_at.server_default is not None
    assert table.c.created_at.onupdate is None


def test_audit_action_values_match_domain_enum():
    assert AUDIT_ACTION_VALUES == tuple(action.value for action in AuditAction)


def test_audit_entity_resource_type_values_match_domain_reference_allowed_values():
    assert AUDIT_ENTITY_RESOURCE_TYPE_VALUES == tuple(
        sorted(ALLOWED_REFERENCE_RESOURCE_TYPES)
    )


def test_audit_events_table_has_expected_check_constraints():
    table = AuditEventRecord.__table__

    constraint_names = _check_constraint_names(table)

    assert "ck_audit_events_action_allowed" in constraint_names
    assert "ck_audit_events_entity_resource_type_allowed" in constraint_names
    assert "ck_audit_events_agent_not_empty" in constraint_names


def test_audit_events_action_check_constraint_uses_current_action_values():
    table = AuditEventRecord.__table__
    constraints = _check_constraint_sql_by_name(table)

    action_check_sql = constraints["ck_audit_events_action_allowed"]

    for action in AUDIT_ACTION_VALUES:
        assert action in action_check_sql


def test_audit_events_entity_resource_type_check_constraint_uses_allowed_values():
    table = AuditEventRecord.__table__
    constraints = _check_constraint_sql_by_name(table)

    entity_resource_type_check_sql = constraints[
        "ck_audit_events_entity_resource_type_allowed"
    ]

    for resource_type in AUDIT_ENTITY_RESOURCE_TYPE_VALUES:
        assert resource_type in entity_resource_type_check_sql


def test_audit_events_agent_not_empty_check_constraint_trims_blank_values():
    table = AuditEventRecord.__table__
    constraints = _check_constraint_sql_by_name(table)

    agent_check_sql = constraints["ck_audit_events_agent_not_empty"]

    assert "btrim(agent)" in agent_check_sql
    assert "''" in agent_check_sql


def test_audit_events_table_has_recorded_at_index():
    table = AuditEventRecord.__table__

    indexes = _index_columns_by_name(table)

    assert indexes["ix_audit_events_recorded_at"] == ("recorded_at",)


def test_audit_events_table_does_not_have_entity_lookup_index():
    table = AuditEventRecord.__table__

    indexes = _index_columns_by_name(table)

    assert "ix_audit_events_entity" not in indexes


def test_audit_events_table_has_no_foreign_keys():
    table = AuditEventRecord.__table__

    assert len(table.foreign_keys) == 0


def test_audit_events_entity_id_has_no_foreign_keys():
    table = AuditEventRecord.__table__

    assert len(table.c.entity_id.foreign_keys) == 0
