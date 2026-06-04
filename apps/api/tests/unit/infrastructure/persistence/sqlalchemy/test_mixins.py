from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import (
    LogicalDeletionMixin,
    TimestampMixin,
)


class MixinTestBase(DeclarativeBase):
    pass


class TimestampedMixinTestRecord(TimestampMixin, MixinTestBase):
    __tablename__ = "timestamped_mixin_test_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)


class LogicalDeletionMixinTestRecord(LogicalDeletionMixin, MixinTestBase):
    __tablename__ = "logical_deletion_mixin_test_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)


def test_timestamp_mixin_adds_created_at_and_updated_at_columns():
    table = TimestampedMixinTestRecord.__table__

    assert "created_at" in table.columns
    assert "updated_at" in table.columns


def test_timestamp_mixin_columns_are_required():
    table = TimestampedMixinTestRecord.__table__

    assert not table.c.created_at.nullable
    assert not table.c.updated_at.nullable


def test_timestamp_mixin_columns_are_timezone_aware_datetimes():
    table = TimestampedMixinTestRecord.__table__

    assert isinstance(table.c.created_at.type, DateTime)
    assert isinstance(table.c.updated_at.type, DateTime)
    assert table.c.created_at.type.timezone
    assert table.c.updated_at.type.timezone


def test_timestamp_mixin_columns_have_server_defaults():
    table = TimestampedMixinTestRecord.__table__

    assert table.c.created_at.server_default is not None
    assert table.c.updated_at.server_default is not None


def test_timestamp_mixin_updated_at_has_onupdate():
    table = TimestampedMixinTestRecord.__table__

    assert table.c.updated_at.onupdate is not None


def test_logical_deletion_mixin_adds_deleted_at_column():
    table = LogicalDeletionMixinTestRecord.__table__

    assert "deleted_at" in table.columns


def test_logical_deletion_mixin_deleted_at_column_is_nullable():
    table = LogicalDeletionMixinTestRecord.__table__

    assert table.c.deleted_at.nullable


def test_logical_deletion_mixin_deleted_at_column_is_timezone_aware_datetime():
    table = LogicalDeletionMixinTestRecord.__table__

    assert isinstance(table.c.deleted_at.type, DateTime)
    assert table.c.deleted_at.type.timezone


def test_logical_deletion_mixin_does_not_add_timestamp_columns():
    table = LogicalDeletionMixinTestRecord.__table__

    assert "created_at" not in table.columns
    assert "updated_at" not in table.columns


def test_logical_deletion_mixin_deleted_at_has_no_server_default_or_onupdate():
    table = LogicalDeletionMixinTestRecord.__table__

    assert table.c.deleted_at.server_default is None
    assert table.c.deleted_at.onupdate is None
