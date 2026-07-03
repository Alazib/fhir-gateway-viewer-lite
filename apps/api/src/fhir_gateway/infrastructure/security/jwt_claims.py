from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerifiedJwtClaims:
    subject: str
    issuer: str
    audience: str
    issued_at: int
    expires_at: int
    roles: tuple[str, ...]
    name: str | None = None
    email: str | None = None
