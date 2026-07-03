import time
from typing import Any

import jwt
import pytest

from fhir_gateway.infrastructure.security import (
    JwtTokenVerifier,
    TokenVerificationError,
    TokenVerifierConfigurationError,
    VerifiedJwtClaims,
)

SECRET = "test-secret-for-hs256-minimum-32-bytes"
WRONG_SECRET = "wrong-secret-for-hs256-minimum-32-bytes"
ISSUER = "fhir-gateway-local"
AUDIENCE = "fhir-gateway-api"
ALGORITHM = "HS256"


def _build_verifier(
    *,
    secret: str | None = SECRET,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    algorithm: str = ALGORITHM,
) -> JwtTokenVerifier:
    return JwtTokenVerifier(
        secret=secret,
        issuer=issuer,
        audience=audience,
        algorithm=algorithm,
    )


def _encode_token(
    *,
    secret: str = SECRET,
    overrides: dict[str, Any] | None = None,
    excluded_claims: tuple[str, ...] = (),
) -> str:
    now = int(time.time())

    payload: dict[str, Any] = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "clinician-demo-001",
        "exp": now + 3600,
        "iat": now,
        "roles": ["clinician"],
        "name": "Demo Clinician",
        "email": "clinician@example.test",
    }

    if overrides is not None:
        payload.update(overrides)

    for claim_name in excluded_claims:
        payload.pop(claim_name, None)

    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def test_verify_returns_verified_claims_for_valid_token():
    verifier = _build_verifier()
    token = _encode_token()

    claims = verifier.verify(token)

    assert claims == VerifiedJwtClaims(
        subject="clinician-demo-001",
        issuer=ISSUER,
        audience=AUDIENCE,
        issued_at=claims.issued_at,
        expires_at=claims.expires_at,
        roles=("clinician",),
        name="Demo Clinician",
        email="clinician@example.test",
    )


@pytest.mark.parametrize("token", ["", "   "])
def test_verify_rejects_missing_token(token: str):
    verifier = _build_verifier()

    with pytest.raises(TokenVerificationError) as exc_info:
        verifier.verify(token)

    assert exc_info.value.message == "Token is missing."


@pytest.mark.parametrize("secret", [None, "", "   "])
def test_verify_rejects_missing_secret_configuration(secret: str | None):
    verifier = _build_verifier(secret=secret)
    token = _encode_token()

    with pytest.raises(TokenVerifierConfigurationError) as exc_info:
        verifier.verify(token)

    assert exc_info.value.message == "JWT secret is not configured."


def test_verify_rejects_too_short_secret_configuration():
    verifier = _build_verifier(secret="too-short")
    token = _encode_token()

    with pytest.raises(TokenVerifierConfigurationError) as exc_info:
        verifier.verify(token)

    assert exc_info.value.message == "JWT secret must be at least 32 bytes long."


def test_verify_rejects_invalid_signature():
    verifier = _build_verifier()
    token = _encode_token(secret=WRONG_SECRET)

    with pytest.raises(TokenVerificationError) as exc_info:
        verifier.verify(token)

    assert exc_info.value.message == "Token verification failed."


def test_verify_rejects_expired_token():
    verifier = _build_verifier()
    token = _encode_token(overrides={"exp": int(time.time()) - 60})

    with pytest.raises(TokenVerificationError) as exc_info:
        verifier.verify(token)

    assert exc_info.value.message == "Token verification failed."


def test_verify_rejects_wrong_issuer():
    verifier = _build_verifier()
    token = _encode_token(overrides={"iss": "wrong-issuer"})

    with pytest.raises(TokenVerificationError) as exc_info:
        verifier.verify(token)

    assert exc_info.value.message == "Token verification failed."


def test_verify_rejects_wrong_audience():
    verifier = _build_verifier()
    token = _encode_token(overrides={"aud": "wrong-audience"})

    with pytest.raises(TokenVerificationError) as exc_info:
        verifier.verify(token)

    assert exc_info.value.message == "Token verification failed."


def test_verify_rejects_missing_required_claim():
    verifier = _build_verifier()
    token = _encode_token(excluded_claims=("sub",))

    with pytest.raises(TokenVerificationError) as exc_info:
        verifier.verify(token)

    assert exc_info.value.message == "Token verification failed."


@pytest.mark.parametrize(
    ("claim_name", "claim_value"),
    [
        ("sub", ""),
        ("sub", "   "),
        ("iss", ""),
        ("aud", ""),
    ],
)
def test_verify_rejects_invalid_string_claims(
    claim_name: str,
    claim_value: str,
):
    verifier = _build_verifier()
    token = _encode_token(overrides={claim_name: claim_value})

    with pytest.raises(TokenVerificationError):
        verifier.verify(token)


@pytest.mark.parametrize(
    "roles",
    [
        "clinician",
        [],
        [""],
        ["   "],
        ["clinician", ""],
    ],
)
def test_verify_rejects_invalid_roles_claim(roles: Any):
    verifier = _build_verifier()
    token = _encode_token(overrides={"roles": roles})

    with pytest.raises(TokenVerificationError):
        verifier.verify(token)


@pytest.mark.parametrize(
    ("claim_name", "claim_value"),
    [
        ("iat", "not-an-integer"),
        ("iat", True),
        ("exp", "not-an-integer"),
        ("exp", False),
    ],
)
def test_verify_rejects_invalid_integer_claims(
    claim_name: str,
    claim_value: Any,
):
    verifier = _build_verifier()
    token = _encode_token(overrides={claim_name: claim_value})

    with pytest.raises(TokenVerificationError):
        verifier.verify(token)


@pytest.mark.parametrize(
    ("claim_name", "claim_value"),
    [
        ("name", ""),
        ("name", "   "),
        ("name", 123),
        ("email", ""),
        ("email", "   "),
        ("email", 123),
    ],
)
def test_verify_rejects_invalid_optional_string_claims(
    claim_name: str,
    claim_value: Any,
):
    verifier = _build_verifier()
    token = _encode_token(overrides={claim_name: claim_value})

    with pytest.raises(TokenVerificationError):
        verifier.verify(token)


def test_verify_allows_missing_optional_claims():
    verifier = _build_verifier()
    token = _encode_token(excluded_claims=("name", "email"))

    claims = verifier.verify(token)

    assert claims.name is None
    assert claims.email is None
