import time
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from fhir_gateway.application.security.current_principal import CurrentPrincipal
from fhir_gateway.infrastructure.security import JwtTokenVerifier
from fhir_gateway.interfaces.http.dependencies.security import (
    get_current_principal,
    get_jwt_token_verifier,
)
from fhir_gateway.interfaces.http.error_handlers import register_exception_handlers


SECRET = "test-secret-for-hs256-minimum-32-bytes"
ISSUER = "fhir-gateway-local"
AUDIENCE = "fhir-gateway-api"
ALGORITHM = "HS256"


def _build_verifier(
    *,
    secret: str | None = SECRET,
) -> JwtTokenVerifier:
    return JwtTokenVerifier(
        secret=secret,
        issuer=ISSUER,
        audience=AUDIENCE,
        algorithm=ALGORITHM,
    )


def _encode_token(
    *,
    secret: str = SECRET,
) -> str:
    now = int(time.time())

    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "clinician-demo-001",
            "iat": now,
            "exp": now + 3600,
            "roles": ["clinician"],
            "name": "Demo Clinician",
        },
        secret,
        algorithm=ALGORITHM,
    )


def _create_test_app(
    verifier: JwtTokenVerifier,
) -> FastAPI:
    app = FastAPI()
    app.state.jwt_token_verifier = verifier

    register_exception_handlers(app)

    @app.get("/protected-test")
    def protected_test(
        principal: Annotated[
            CurrentPrincipal,
            Depends(get_current_principal),
        ],
    ) -> dict[str, object]:
        return {
            "subject": principal.subject,
            "roles": principal.roles,
            "display_name": principal.display_name,
        }

    return app


def test_get_jwt_token_verifier_returns_application_verifier():
    app = FastAPI()
    verifier = _build_verifier()

    app.state.jwt_token_verifier = verifier

    request = Request(
        {
            "type": "http",
            "app": app,
        },
    )

    result = get_jwt_token_verifier(request)

    assert result is verifier


def test_protected_request_returns_current_principal_for_valid_token():
    client = TestClient(
        _create_test_app(_build_verifier()),
    )

    response = client.get(
        "/protected-test",
        headers={
            "Authorization": f"Bearer {_encode_token()}",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "subject": "clinician-demo-001",
        "roles": ["clinician"],
        "display_name": "Demo Clinician",
    }


def test_protected_request_rejects_missing_credentials():
    client = TestClient(
        _create_test_app(_build_verifier()),
    )

    response = client.get("/protected-test")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Authentication credentials are missing or invalid.",
            "field": None,
            "resource": None,
            "identifier": None,
        }
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_protected_request_rejects_wrong_authentication_scheme():
    client = TestClient(
        _create_test_app(_build_verifier()),
    )

    response = client.get(
        "/protected-test",
        headers={
            "Authorization": "Basic abc123",
        },
    )

    assert response.status_code == 401


def test_protected_request_rejects_invalid_token():
    client = TestClient(
        _create_test_app(_build_verifier()),
    )

    response = client.get(
        "/protected-test",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert "Token verification failed" not in response.text


def test_protected_request_rejects_token_with_invalid_signature():
    client = TestClient(
        _create_test_app(_build_verifier()),
    )

    token = _encode_token(
        secret="different-secret-for-hs256-32-bytes",
    )

    response = client.get(
        "/protected-test",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401


def test_verifier_configuration_error_remains_internal_server_error():
    client = TestClient(
        _create_test_app(
            _build_verifier(secret=None),
        ),
    )

    response = client.get(
        "/protected-test",
        headers={
            "Authorization": f"Bearer {_encode_token()}",
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "Internal server error.",
            "field": None,
            "resource": None,
            "identifier": None,
        }
    }
    assert "JWT secret is not configured" not in response.text
