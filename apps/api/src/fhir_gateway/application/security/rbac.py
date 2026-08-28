from enum import StrEnum
from types import MappingProxyType
from typing import Final, Mapping

from fhir_gateway.application.security.current_principal import CurrentPrincipal
from fhir_gateway.application.security.errors import PermissionDeniedError


class Role(StrEnum):
    CLINICIAN = "clinician"
    AUDITOR = "auditor"
    ADMIN = "admin"


class Permission(StrEnum):
    PATIENT_READ = "patient:read"
    OBSERVATION_READ = "observation:read"
    CONDITION_READ = "condition:read"
    ENCOUNTER_READ = "encounter:read"
    BUNDLE_EXPORT = "bundle:export"
    AUDIT_READ = "audit:read"


_ROLE_PERMISSIONS: Final[Mapping[Role, frozenset[Permission]]] = (
    MappingProxyType(
        {
            Role.CLINICIAN: frozenset(
                {
                    Permission.PATIENT_READ,
                    Permission.OBSERVATION_READ,
                    Permission.CONDITION_READ,
                    Permission.ENCOUNTER_READ,
                    Permission.BUNDLE_EXPORT,
                }
            ),
            Role.AUDITOR: frozenset(
                {
                    Permission.AUDIT_READ,
                }
            ),
            Role.ADMIN: frozenset(
                {
                    Permission.PATIENT_READ,
                    Permission.OBSERVATION_READ,
                    Permission.CONDITION_READ,
                    Permission.ENCOUNTER_READ,
                    Permission.BUNDLE_EXPORT,
                    Permission.AUDIT_READ,
                }
            ),
        }
    )
)


def permissions_for_roles(
    roles: tuple[str, ...],
) -> frozenset[Permission]:
    permissions: set[Permission] = set()

    for raw_role in roles:
        try:
            role = Role(raw_role)
        except ValueError:
            continue

        permissions.update(_ROLE_PERMISSIONS[role])

    return frozenset(permissions)


def has_permission(
    principal: CurrentPrincipal,
    permission: Permission,
) -> bool:
    return permission in permissions_for_roles(principal.roles)


def ensure_permission(
    principal: CurrentPrincipal,
    permission: Permission,
) -> None:
    if not has_permission(principal, permission):
        raise PermissionDeniedError(
            required_permission=permission,
        )
