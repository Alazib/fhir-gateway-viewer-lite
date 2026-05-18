import pytest

from fhir_gateway.infrastructure.config.settings import get_settings
from fhir_gateway.interfaces.http.app import create_app


ENVIRONMENT_VARIABLES = (
    "FHIR_GATEWAY_APP_NAME",
    "FHIR_GATEWAY_APP_VERSION",
    "FHIR_GATEWAY_ENVIRONMENT",
    "FHIR_GATEWAY_LOG_LEVEL",
)


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch: pytest.MonkeyPatch):
    for variable_name in ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable_name, raising=False)

    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


def test_create_app_uses_default_settings():
    app = create_app()

    assert app.title == "FHIR Mini-Gateway API"
    assert app.version == "0.1.0"


def test_create_app_uses_environment_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FHIR_GATEWAY_APP_NAME", "Test API")
    monkeypatch.setenv("FHIR_GATEWAY_APP_VERSION", "9.9.9")
    monkeypatch.setenv("FHIR_GATEWAY_ENVIRONMENT", "test")
    monkeypatch.setenv("FHIR_GATEWAY_LOG_LEVEL", "DEBUG")

    get_settings.cache_clear()

    app = create_app()

    assert app.title == "Test API"
    assert app.version == "9.9.9"
