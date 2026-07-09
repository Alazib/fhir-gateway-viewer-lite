import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from fhir_gateway.application.errors import (
    ApplicationNotFoundError,
    ApplicationValidationError,
)
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.infrastructure.security import (
    TokenVerifierConfigurationError,
)
from fhir_gateway.interfaces.http.errors import AuthenticationError
from fhir_gateway.interfaces.http.schemas.errors import ApiError, ApiErrorResponse

logger = logging.getLogger(__name__)


def _build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    field: str | None = None,
    resource: str | None = None,
    identifier: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    error_response = ApiErrorResponse(
        error=ApiError(
            code=code,
            message=message,
            field=field,
            resource=resource,
            identifier=identifier,
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
        headers=headers,
    )


async def handle_application_validation_error(
    _request: Request,
    exc: ApplicationValidationError,
) -> JSONResponse:
    return _build_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="validation_error",
        message=exc.message,
        field=exc.field,
    )


async def handle_domain_validation_error(
    _request: Request,
    exc: DomainValidationError,
) -> JSONResponse:
    return _build_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="validation_error",
        message=exc.message,
        field=exc.field,
    )


async def handle_application_not_found_error(
    _request: Request,
    exc: ApplicationNotFoundError,
) -> JSONResponse:
    return _build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="not_found",
        message=exc.message,
        resource=exc.resource,
        identifier=exc.identifier,
    )


async def handle_authentication_error(
    _request: Request,
    _exc: AuthenticationError,
) -> JSONResponse:
    return _build_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="unauthorized",
        message="Authentication credentials are missing or invalid.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def handle_token_verifier_configuration_error(
    request: Request,
    exc: TokenVerifierConfigurationError,
) -> JSONResponse:

    logger.error(
        "JWT token verifier configuration error while handling request "
        "%s %s: %s",
        request.method,
        request.url.path,
        exc.message,
    )

    return _build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_server_error",
        message="Internal server error.",
    )


async def handle_unexpected_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unexpected error while handling request %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )

    return _build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_server_error",
        message="Internal server error.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        ApplicationValidationError,
        handle_application_validation_error,
    )
    app.add_exception_handler(
        DomainValidationError,
        handle_domain_validation_error,
    )
    app.add_exception_handler(
        ApplicationNotFoundError,
        handle_application_not_found_error,
    )
    app.add_exception_handler(
        AuthenticationError,
        handle_authentication_error,
    )
    app.add_exception_handler(
        TokenVerifierConfigurationError,
        handle_token_verifier_configuration_error,
    )
    app.add_exception_handler(
        Exception,
        handle_unexpected_error,
    )
