from dataclasses import dataclass

from fhir_gateway.application.errors import ApplicationValidationError


@dataclass(frozen=True, slots=True)
class CurrentPrincipal:
    subject: str
    roles: tuple[str, ...]
    display_name: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ApplicationValidationError(
                "CurrentPrincipal.subject",
                "must be a non-empty string",
            )

        if not isinstance(self.roles, tuple):
            raise ApplicationValidationError(
                "CurrentPrincipal.roles",
                "must be a tuple of non-empty strings",
            )

        if not self.roles:
            raise ApplicationValidationError(
                "CurrentPrincipal.roles",
                "must contain at least one role",
            )

        if not all(
            isinstance(role, str) and role.strip()
            for role in self.roles
        ):
            raise ApplicationValidationError(
                "CurrentPrincipal.roles",
                "must contain only non-empty strings",
            )

        if (
            self.display_name is not None
            and (
                not isinstance(self.display_name, str)
                or not self.display_name.strip()
            )
        ):
            raise ApplicationValidationError(
                "CurrentPrincipal.display_name",
                "must be a non-empty string when provided",
            )
