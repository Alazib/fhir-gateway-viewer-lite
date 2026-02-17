import pytest

from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.quantity import Quantity


################################### VALID CASES:


def test_accepts_empty_quantity():
    q = Quantity()
    assert q.value is None
    assert q.unit is None


def test_accepts_value_with_unit_int():
    q = Quantity(value=5, unit="mg/dL")
    assert q.value == 5
    assert q.unit == "mg/dL"


def test_accepts_value_with_unit_float():
    q = Quantity(value=6.2, unit="%")
    assert q.value == 6.2
    assert q.unit == "%"


def test_trims_unit_and_converts_empty_to_none():
    q = Quantity(value=1, unit="   kg   ")
    assert q.unit == "kg"

    q2 = Quantity(unit="   ")
    assert q2.unit is None


def test_allows_unit_without_value():
    q = Quantity(unit="mg/dL")
    assert q.value is None
    assert q.unit == "mg/dL"


################################### NOT VALID CASES:


def test_rejects_non_numeric_value():
    with pytest.raises(DomainValidationError) as exc:
        Quantity(value="6.2", unit="%")  # type: ignore

    assert exc.value.field == "Quantity.value"
    assert exc.value.message == "must be a float or int"


def test_requires_unit_when_value_is_present():
    with pytest.raises(DomainValidationError) as exc:
        Quantity(value=6.2)

    assert exc.value.field == "Quantity.unit"
    assert "cannot be empty" in exc.value.message


def test_requires_unit_even_when_value_is_zero():
    with pytest.raises(DomainValidationError) as exc:
        Quantity(value=0)

    assert exc.value.field == "Quantity.unit"
    assert "cannot be empty" in exc.value.message
