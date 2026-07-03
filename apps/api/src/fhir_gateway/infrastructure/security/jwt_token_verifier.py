from typing import Any

import jwt
from jwt import PyJWTError

from fhir_gateway.infrastructure.security.errors import (
    TokenVerificationError,
    TokenVerifierConfigurationError,
)
from fhir_gateway.infrastructure.security.jwt_claims import VerifiedJwtClaims

REQUIRED_CLAIMS = (
    "iss",
    "aud",
    "sub",
    "exp",
    "iat",
    "roles",
)

MINIMUM_HMAC_SECRET_LENGTH_BYTES = 32


class JwtTokenVerifier:
    def __init__(
        self,
        *,
        secret: str | None,
        issuer: str,
        audience: str,
        algorithm: str,
    ) -> None:
        self._secret = secret
        self._issuer = issuer
        self._audience = audience
        self._algorithm = algorithm

    def verify(self, token: str) -> VerifiedJwtClaims:
        if not isinstance(token, str) or not token.strip():
            raise TokenVerificationError("Token is missing.")

        if self._secret is None or not self._secret.strip():
            raise TokenVerifierConfigurationError("JWT secret is not configured.")

        if len(self._secret.encode("utf-8")) < MINIMUM_HMAC_SECRET_LENGTH_BYTES:
            raise TokenVerifierConfigurationError(
                "JWT secret must be at least 32 bytes long.",
            )

        try:
            decoded_claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
                options={"require": list(REQUIRED_CLAIMS)},
            )
        except PyJWTError as exc:
            raise TokenVerificationError("Token verification failed.") from exc

        return _build_verified_jwt_claims(decoded_claims)


def _build_verified_jwt_claims(
    claims: dict[str, Any],
) -> VerifiedJwtClaims:
    subject = _get_required_non_empty_string_claim(claims, "sub")
    issuer = _get_required_non_empty_string_claim(claims, "iss")
    audience = _get_required_non_empty_string_claim(claims, "aud")
    issued_at = _get_required_integer_claim(claims, "iat")
    expires_at = _get_required_integer_claim(claims, "exp")
    roles = _get_roles_claim(claims)
    name = _get_optional_non_empty_string_claim(claims, "name")
    email = _get_optional_non_empty_string_claim(claims, "email")

    return VerifiedJwtClaims(
        subject=subject,
        issuer=issuer,
        audience=audience,
        issued_at=issued_at,
        expires_at=expires_at,
        roles=roles,
        name=name,
        email=email,
    )


def _get_required_non_empty_string_claim(
    claims: dict[str, Any],
    claim_name: str,
) -> str:
    value = claims.get(claim_name)

    if not isinstance(value, str) or not value.strip():
        raise TokenVerificationError(
            f"Token claim '{claim_name}' must be a non-empty string.",
        )

    return value


def _get_required_integer_claim(
    claims: dict[str, Any],
    claim_name: str,
) -> int:
    value = claims.get(claim_name)

    if isinstance(value, bool) or not isinstance(value, int):
        raise TokenVerificationError(
            f"Token claim '{claim_name}' must be an integer.",
        )

    return value


def _get_optional_non_empty_string_claim(
    claims: dict[str, Any],
    claim_name: str,
) -> str | None:
    value = claims.get(claim_name)

    if value is None:
        return None

    if not isinstance(value, str) or not value.strip():
        raise TokenVerificationError(
            f"Token claim '{claim_name}' must be a non-empty string when provided.",
        )

    return value


def _get_roles_claim(claims: dict[str, Any]) -> tuple[str, ...]:
    roles = claims.get("roles")

    if not isinstance(roles, (list, tuple)):
        raise TokenVerificationError(
            "Token claim 'roles' must be a list or tuple of non-empty strings.",
        )

    if len(roles) == 0:
        raise TokenVerificationError(
            "Token claim 'roles' must contain at least one role.",
        )

    for role in roles:
        if not isinstance(role, str) or not role.strip():
            raise TokenVerificationError(
                "Token claim 'roles' must contain only non-empty strings.",
            )

    return tuple(roles)
