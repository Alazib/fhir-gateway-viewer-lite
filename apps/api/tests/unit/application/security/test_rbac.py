from types import MappingProxyType

import pytest

from fhir_gateway.application.security.current_principal import CurrentPrincipal
from fhir_gateway.application.security.errors import PermissionDeniedError
from fhir_gateway.application.security.rbac import (
    Permission,
    Role,
    _ROLE_PERMISSIONS,
    ensure_permission,
    has_permission,
    permissions_for_roles,
)


CLINICIAN_PERMISSIONS = frozenset(
    {
        Permission.PATIENT_READ,
        Permission.OBSERVATION_READ,
        Permission.CONDITION_READ,
        Permission.ENCOUNTER_READ,
        Permission.BUNDLE_EXPORT,
    }
)

AUDITOR_PERMISSIONS = frozenset(
    {
        Permission.AUDIT_READ,
    }
)

ADMIN_PERMISSIONS = frozenset(
    {
        Permission.PATIENT_READ,
        Permission.OBSERVATION_READ,
        Permission.CONDITION_READ,
        Permission.ENCOUNTER_READ,
        Permission.BUNDLE_EXPORT,
        Permission.AUDIT_READ,
    }
)


def test_role_catalog_contains_exact_mvp_roles():
    assert {role.value for role in Role} == {
        "clinician",
        "auditor",
        "admin",
    }


def test_permission_catalog_contains_exact_mvp_permissions():
    assert {permission.value for permission in Permission} == {
        "patient:read",
        "observation:read",
        "condition:read",
        "encounter:read",
        "bundle:export",
        "audit:read",
    }


def test_role_permission_mapping_contains_exact_mvp_policy():
    assert _ROLE_PERMISSIONS[Role.CLINICIAN] == CLINICIAN_PERMISSIONS
    assert _ROLE_PERMISSIONS[Role.AUDITOR] == AUDITOR_PERMISSIONS
    assert _ROLE_PERMISSIONS[Role.ADMIN] == ADMIN_PERMISSIONS


def test_role_permission_mapping_is_immutable():
    assert isinstance(_ROLE_PERMISSIONS, MappingProxyType)
    assert all(
        isinstance(permissions, frozenset)
        for permissions in _ROLE_PERMISSIONS.values()
    )


@pytest.mark.parametrize(
    ("roles", "expected_permissions"),
    [
        (("clinician",), CLINICIAN_PERMISSIONS),
        (("auditor",), AUDITOR_PERMISSIONS),
        (("admin",), ADMIN_PERMISSIONS),
    ],
)
def test_permissions_for_roles_resolves_known_role(
    roles: tuple[str, ...],
    expected_permissions: frozenset[Permission],
):
    assert permissions_for_roles(roles) == expected_permissions


def test_permissions_for_roles_unions_multiple_known_roles():
    permissions = permissions_for_roles(("clinician", "auditor"))

    assert permissions == ADMIN_PERMISSIONS


def test_permissions_for_roles_ignores_duplicate_roles():
    permissions = permissions_for_roles(("clinician", "clinician"))

    assert permissions == CLINICIAN_PERMISSIONS


def test_permissions_for_roles_gives_unknown_role_no_permissions():
    permissions = permissions_for_roles(("researcher",))

    assert permissions == frozenset()


def test_permissions_for_roles_keeps_permissions_from_known_roles():
    permissions = permissions_for_roles(("clinician", "researcher"))

    assert permissions == CLINICIAN_PERMISSIONS


@pytest.mark.parametrize(
    "unknown_role",
    [
        "Clinician",
        " clinician ",
    ],
)
def test_permissions_for_roles_does_not_normalize_role_values(
    unknown_role: str,
):
    permissions = permissions_for_roles((unknown_role,))

    assert permissions == frozenset()


def test_permissions_for_roles_handles_multiple_unknown_roles():
    permissions = permissions_for_roles(
        ("researcher", "nurse", "future-role")
    )

    assert permissions == frozenset()


def test_permissions_for_roles_handles_empty_role_collection():
    permissions = permissions_for_roles(())

    assert permissions == frozenset()


def test_permissions_for_roles_returns_immutable_permissions():
    permissions = permissions_for_roles(("clinician",))

    assert isinstance(permissions, frozenset)


def test_has_permission_returns_true_when_principal_has_permission():
    principal = CurrentPrincipal(
        subject="clinician-demo-001",
        roles=("clinician",),
    )

    assert has_permission(
        principal,
        Permission.PATIENT_READ,
    ) is True


def test_has_permission_returns_false_when_principal_lacks_permission():
    principal = CurrentPrincipal(
        subject="clinician-demo-001",
        roles=("clinician",),
    )

    assert has_permission(
        principal,
        Permission.AUDIT_READ,
    ) is False


def test_has_permission_combines_permissions_from_multiple_roles():
    principal = CurrentPrincipal(
        subject="multi-role-demo-001",
        roles=("clinician", "auditor"),
    )

    assert has_permission(
        principal,
        Permission.AUDIT_READ,
    ) is True


def test_has_permission_returns_false_for_unknown_role():
    principal = CurrentPrincipal(
        subject="unknown-role-demo-001",
        roles=("researcher",),
    )

    assert has_permission(
        principal,
        Permission.PATIENT_READ,
    ) is False


def test_ensure_permission_returns_normally_when_permission_is_present():
    principal = CurrentPrincipal(
        subject="clinician-demo-001",
        roles=("clinician",),
    )

    result = ensure_permission(
        principal,
        Permission.PATIENT_READ,
    )

    assert result is None


def test_ensure_permission_raises_when_permission_is_missing():
    principal = CurrentPrincipal(
        subject="auditor-demo-001",
        roles=("auditor",),
    )

    with pytest.raises(PermissionDeniedError) as exc_info:
        ensure_permission(
            principal,
            Permission.PATIENT_READ,
        )

    assert (
        exc_info.value.required_permission
        is Permission.PATIENT_READ
    )
