import logging

from fastapi import FastAPI

from fhir_gateway.infrastructure.config.settings import get_settings
from fhir_gateway.infrastructure.logging import configure_logging
from fhir_gateway.interfaces.http.routers.health import router as health_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:

    settings = get_settings()

    configure_logging(settings.log_level)

    logger.info(
        "Creating FastAPI application for environment: %s",
        settings.environment,
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    app.include_router(health_router)

    return app
