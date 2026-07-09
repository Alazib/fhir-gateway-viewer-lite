from fastapi import Request

from fhir_gateway.infrastructure.security import JwtTokenVerifier


def get_jwt_token_verifier(
    request: Request,
) -> JwtTokenVerifier:
    return request.app.state.jwt_token_verifier
