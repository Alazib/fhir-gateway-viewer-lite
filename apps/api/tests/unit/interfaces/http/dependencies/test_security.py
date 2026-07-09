from fastapi import FastAPI, Request

from fhir_gateway.infrastructure.security import JwtTokenVerifier
from fhir_gateway.interfaces.http.dependencies.security import (
    get_jwt_token_verifier,
)


def test_get_jwt_token_verifier_returns_application_verifier():
    app = FastAPI()

    verifier = JwtTokenVerifier(
        secret=None,
        issuer="fhir-gateway-local",
        audience="fhir-gateway-api",
        algorithm="HS256",
    )

    app.state.jwt_token_verifier = verifier

    request = Request(
        {
            "type": "http",
            "app": app,
        },
    )

    result = get_jwt_token_verifier(request)

    assert result is verifier
