from datetime import datetime, timezone, timedelta
import pytest
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.instant import Instant


################################### VALID CASES:


# Accepts a timezone-aware datetime already in UTC (keeps the same instant).
def test_accepts_utc_datetime():
    dt = datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
    instant = Instant(value=dt)

    assert instant.value.tzinfo == timezone.utc
    assert instant.value == dt


# Accepts a timezone-aware datetime in another offset and normalizes it to UTC.
def test_normalizes_to_utc_from_offset_timezone():
    dt = datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))
    instant = Instant(value=dt)

    assert instant.value.tzinfo == timezone.utc
    assert instant.value.hour == 9  # 10:00+01:00 -> 09:00Z


################################### NOT VALID CASES:


# Rejects non-datetime values.
def test_rejects_non_datetime():
    with pytest.raises(DomainValidationError) as exc:
        Instant(value="2026-02-14T10:00:00Z")  # type: ignore

    assert exc.value.field == "Instant.value"
    assert exc.value.message == "must be a datetime"


# Rejects naive datetimes (no tzinfo).
def test_rejects_naive_datetime():
    dt = datetime(2026, 2, 14, 10, 0, 0)
    with pytest.raises(DomainValidationError) as exc:
        Instant(value=dt)

    assert exc.value.field == "Instant.value"
    assert exc.value.message == "must be timezone-aware"
