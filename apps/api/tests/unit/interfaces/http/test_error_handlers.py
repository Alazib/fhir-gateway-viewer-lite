from fastapi import FastAPI
from fastapi.testclient import TestClient

from fhir_gateway.application.errors import (
    ApplicationNotFoundError,
    ApplicationValidationError,
)
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.interfaces.http.error_handlers import register_exception_handlers


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
