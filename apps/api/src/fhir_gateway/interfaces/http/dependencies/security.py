from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fhir_gateway.application.security.current_principal import CurrentPrincipal
from fhir_gateway.infrastructure.security import (
    JwtTokenVerifier,
    TokenVerificationError,
)
from fhir_gateway.interfaces.http.errors import AuthenticationError


bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    bearerFormat="JWT",
    auto_error=False,
)


def get_jwt_token_verifier(
    request: Request,
) -> JwtTokenVerifier:
    return request.app.state.jwt_token_verifier


def get_current_principal(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    verifier: Annotated[
        JwtTokenVerifier,
        Depends(get_jwt_token_verifier),
    ],
) -> CurrentPrincipal:
    if credentials is None:
        raise AuthenticationError()

    try:
        claims = verifier.verify(credentials.credentials)
    except TokenVerificationError as exc:
        raise AuthenticationError() from exc

    return CurrentPrincipal(
        subject=claims.subject,
        roles=claims.roles,
        display_name=claims.name,
    )
