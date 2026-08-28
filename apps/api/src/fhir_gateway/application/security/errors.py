from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from fhir_gateway.application.security.rbac import Permission


class PermissionDeniedError(Exception):
    def __init__(self, required_permission: Permission) -> None:
        self.required_permission = required_permission
        super().__init__(
            f"Permission denied: {required_permission.value}"
        )
