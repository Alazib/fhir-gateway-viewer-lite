from fastapi import FastAPI
from fastapi.testclient import TestClient

from fhir_gateway.application.errors import (
    ApplicationNotFoundError,
    ApplicationValidationError,
)
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.infrastructure.security import (
    TokenVerifierConfigurationError,
)
from fhir_gateway.interfaces.http.error_handlers import register_exception_handlers
from fhir_gateway.interfaces.http.errors import AuthenticationError


def _create_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/application-validation-error")
    def raise_application_validation_error() -> None:
        raise ApplicationValidationError(
            field="limit",
            message="must be greater than or equal to 1",
        )

    @app.get("/domain-validation-error")
    def raise_domain_validation_error() -> None:
        raise DomainValidationError(
            field="Code.code",
            message="cannot be empty",
        )

    @app.get("/application-not-found-error")
    def raise_application_not_found_error() -> None:
        raise ApplicationNotFoundError(
            resource="Patient",
            identifier="pat-001",
        )

    @app.get("/authentication-error")
    def raise_authentication_error() -> None:
        raise AuthenticationError()

    @app.get("/token-verifier-configuration-error")
    def raise_token_verifier_configuration_error() -> None:
        raise TokenVerifierConfigurationError(
            "JWT secret is not configured.",
        )

    @app.get("/unexpected-error")
    def raise_unexpected_error() -> None:
        raise RuntimeError("database exploded")

    return app


def test_application_validation_error_returns_standard_envelope():
    client = TestClient(_create_test_app())

    response = client.get("/application-validation-error")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "must be greater than or equal to 1",
            "field": "limit",
            "resource": None,
            "identifier": None,
        }
    }


def test_domain_validation_error_returns_standard_envelope():
    client = TestClient(_create_test_app())

    response = client.get("/domain-validation-error")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "cannot be empty",
            "field": "Code.code",
            "resource": None,
            "identifier": None,
        }
    }


def test_application_not_found_error_returns_standard_envelope():
    client = TestClient(_create_test_app())

    response = client.get("/application-not-found-error")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Patient not found: pat-001",
            "field": None,
            "resource": "Patient",
            "identifier": "pat-001",
        }
    }


def test_authentication_error_returns_unauthorized_envelope():
    client = TestClient(_create_test_app())

    response = client.get("/authentication-error")

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


def test_authentication_error_includes_bearer_challenge():
    client = TestClient(_create_test_app())

    response = client.get("/authentication-error")

    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_token_verifier_configuration_error_returns_internal_error():
    client = TestClient(_create_test_app())

    response = client.get("/token-verifier-configuration-error")

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


def test_token_verifier_configuration_error_does_not_leak_details():
    client = TestClient(_create_test_app())

    response = client.get("/token-verifier-configuration-error")

    assert "JWT secret is not configured." not in response.text


def test_unexpected_error_returns_standard_envelope_without_leaking_details():
    client = TestClient(
        _create_test_app(),
        raise_server_exceptions=False,
    )

    response = client.get("/unexpected-error")

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
