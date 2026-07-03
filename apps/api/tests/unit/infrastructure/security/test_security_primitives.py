from dataclasses import FrozenInstanceError

import pytest

from fhir_gateway.infrastructure.security import (
    TokenVerificationError,
    TokenVerifierConfigurationError,
    VerifiedJwtClaims,
)


def test_verified_jwt_claims_stores_verified_token_claims():
    claims = VerifiedJwtClaims(
        subject="clinician-demo-001",
        issuer="fhir-gateway-local",
        audience="fhir-gateway-api",
        issued_at=1_700_000_000,
        expires_at=1_700_003_600,
        roles=("clinician",),
        name="Demo Clinician",
        email="clinician@example.test",
    )

    assert claims.subject == "clinician-demo-001"
    assert claims.issuer == "fhir-gateway-local"
    assert claims.audience == "fhir-gateway-api"
    assert claims.issued_at == 1_700_000_000
    assert claims.expires_at == 1_700_003_600
    assert claims.roles == ("clinician",)
    assert claims.name == "Demo Clinician"
    assert claims.email == "clinician@example.test"


def test_verified_jwt_claims_is_immutable():
    claims = VerifiedJwtClaims(
        subject="clinician-demo-001",
        issuer="fhir-gateway-local",
        audience="fhir-gateway-api",
        issued_at=1_700_000_000,
        expires_at=1_700_003_600,
        roles=("clinician",),
    )

    with pytest.raises(FrozenInstanceError):
        setattr(claims, "subject", "changed-subject")


def test_token_verification_error_exposes_message():
    error = TokenVerificationError("Token has expired.")

    assert error.message == "Token has expired."
    assert str(error) == "Token has expired."


def test_token_verifier_configuration_error_exposes_message():
    error = TokenVerifierConfigurationError("JWT secret is not configured.")

    assert error.message == "JWT secret is not configured."
    assert str(error) == "JWT secret is not configured."
