from datetime import datetime, timezone
import pytest
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.period import Period


################################### VALID CASES:


def test_accepts_empty_period():
    p = Period()
    assert p.start is None
    assert p.end is None


def test_accepts_start_only():
    start = Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc))
    p = Period(start=start)

    assert p.start == start
    assert p.end is None


def test_accepts_end_only():
    end = Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc))
    p = Period(end=end)

    assert p.start is None
    assert p.end == end


def test_accepts_start_before_end():
    start = Instant(value=datetime(2026, 2, 14, 9, 0, 0, tzinfo=timezone.utc))
    end = Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc))
    p = Period(start=start, end=end)

    assert p.start == start
    assert p.end == end


def test_accepts_start_equal_end():
    dt = datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
    start = Instant(value=dt)
    end = Instant(value=dt)
    p = Period(start=start, end=end)

    assert p.start == start
    assert p.end == end


################################### NOT VALID CASES:


def test_rejects_non_instant_start():
    with pytest.raises(DomainValidationError) as exc:
        Period(start="2026-02-14T10:00:00Z")  # type: ignore

    assert exc.value.field == "Period.start"
    assert exc.value.message == "must be a Instant"


def test_rejects_non_instant_end():
    with pytest.raises(DomainValidationError) as exc:
        Period(end="2026-02-14T10:00:00Z")  # type: ignore

    assert exc.value.field == "Period.end"
    assert exc.value.message == "must be a Instant"


def test_rejects_start_after_end():
    start = Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc))
    end = Instant(value=datetime(2026, 2, 14, 9, 0, 0, tzinfo=timezone.utc))

    with pytest.raises(DomainValidationError) as exc:
        Period(start=start, end=end)

    assert exc.value.field == "Period"
    assert exc.value.message == "start must be <= end"
