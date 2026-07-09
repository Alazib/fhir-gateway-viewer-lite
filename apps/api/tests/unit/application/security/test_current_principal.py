from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from fhir_gateway.application.errors import ApplicationValidationError
from fhir_gateway.application.security.current_principal import CurrentPrincipal


def test_current_principal_accepts_valid_values():
    principal = CurrentPrincipal(
        subject="clinician-demo-001",
        roles=("clinician",),
        display_name="Demo Clinician",
    )

    assert principal.subject == "clinician-demo-001"
    assert principal.roles == ("clinician",)
    assert principal.display_name == "Demo Clinician"


def test_current_principal_allows_missing_display_name():
    principal = CurrentPrincipal(
        subject="clinician-demo-001",
        roles=("clinician",),
    )

    assert principal.display_name is None


def test_current_principal_is_immutable():
    principal = CurrentPrincipal(
        subject="clinician-demo-001",
        roles=("clinician",),
    )

    with pytest.raises(FrozenInstanceError):
        setattr(principal, "subject", "another-user")


@pytest.mark.parametrize(
    "subject",
    [
        None,
        123,
        "",
        "   ",
    ],
)
def test_current_principal_rejects_invalid_subject(subject: Any):
    with pytest.raises(ApplicationValidationError) as exc_info:
        CurrentPrincipal(
            subject=subject,
            roles=("clinician",),
        )

    assert exc_info.value.field == "CurrentPrincipal.subject"
    assert exc_info.value.message == "must be a non-empty string"


@pytest.mark.parametrize(
    "roles",
    [
        None,
        "clinician",
        ["clinician"],
    ],
)
def test_current_principal_rejects_roles_that_are_not_a_tuple(
    roles: Any,
):
    with pytest.raises(ApplicationValidationError) as exc_info:
        CurrentPrincipal(
            subject="clinician-demo-001",
            roles=roles,
        )

    assert exc_info.value.field == "CurrentPrincipal.roles"
    assert (
        exc_info.value.message
        == "must be a tuple of non-empty strings"
    )


def test_current_principal_rejects_empty_roles():
    with pytest.raises(ApplicationValidationError) as exc_info:
        CurrentPrincipal(
            subject="clinician-demo-001",
            roles=(),
        )

    assert exc_info.value.field == "CurrentPrincipal.roles"
    assert exc_info.value.message == "must contain at least one role"


@pytest.mark.parametrize(
    "roles",
    [
        ("",),
        ("   ",),
        ("clinician", ""),
        ("clinician", 123),
    ],
)
def test_current_principal_rejects_invalid_role_values(
    roles: tuple[Any, ...],
):
    with pytest.raises(ApplicationValidationError) as exc_info:
        CurrentPrincipal(
            subject="clinician-demo-001",
            roles=roles,
        )

    assert exc_info.value.field == "CurrentPrincipal.roles"
    assert (
        exc_info.value.message
        == "must contain only non-empty strings"
    )


@pytest.mark.parametrize(
    "display_name",
    [
        "",
        "   ",
        123,
    ],
)
def test_current_principal_rejects_invalid_display_name(
    display_name: Any,
):
    with pytest.raises(ApplicationValidationError) as exc_info:
        CurrentPrincipal(
            subject="clinician-demo-001",
            roles=("clinician",),
            display_name=display_name,
        )

    assert exc_info.value.field == "CurrentPrincipal.display_name"
    assert (
        exc_info.value.message
        == "must be a non-empty string when provided"
    )
