import pytest
from pydantic import ValidationError

from fhir_gateway.infrastructure.config.settings import Settings, get_settings

ENVIRONMENT_VARIABLES = (
    "FHIR_GATEWAY_APP_NAME",
    "FHIR_GATEWAY_APP_VERSION",
    "FHIR_GATEWAY_ENVIRONMENT",
    "FHIR_GATEWAY_LOG_LEVEL",
)


def _clear_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:

    for variable_name in ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable_name, raising=False)


def test_settings_uses_default_values(monkeypatch: pytest.MonkeyPatch):

    _clear_environment_variables(monkeypatch)

    settings = Settings()

    assert settings.app_name == "FHIR Mini-Gateway API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "local"
    assert settings.log_level == "INFO"


def test_settings_reads_environment_variables(monkeypatch: pytest.MonkeyPatch):
    _clear_environment_variables(monkeypatch)

    monkeypatch.setenv("FHIR_GATEWAY_APP_NAME", "Test API")
    monkeypatch.setenv("FHIR_GATEWAY_APP_VERSION", "9.9.9")
    monkeypatch.setenv("FHIR_GATEWAY_ENVIRONMENT", "test")
    monkeypatch.setenv("FHIR_GATEWAY_LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.app_name == "Test API"
    assert settings.app_version == "9.9.9"
    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"


def test_settings_rejects_invalid_environment(monkeypatch: pytest.MonkeyPatch):
    _clear_environment_variables(monkeypatch)

    monkeypatch.setenv("FHIR_GATEWAY_ENVIRONMENT", "banana")

    with pytest.raises(ValidationError):
        Settings()


def test_settings_rejects_invalid_log_level(monkeypatch: pytest.MonkeyPatch):
    _clear_environment_variables(monkeypatch)

    monkeypatch.setenv("FHIR_GATEWAY_LOG_LEVEL", "TRACE")

    with pytest.raises(ValidationError):
        Settings()


def test_get_settings_returns_cached_settings(monkeypatch: pytest.MonkeyPatch):
    _clear_environment_variables(monkeypatch)
    get_settings.cache_clear()

    first_settings = get_settings()
    second_settings = get_settings()

    assert first_settings is second_settings

    get_settings.cache_clear()


def test_get_settings_cache_can_be_cleared(monkeypatch: pytest.MonkeyPatch):
    _clear_environment_variables(monkeypatch)
    get_settings.cache_clear()

    first_settings = get_settings()

    monkeypatch.setenv("FHIR_GATEWAY_APP_NAME", "Changed API")

    cached_settings = get_settings()

    assert cached_settings.app_name == first_settings.app_name

    get_settings.cache_clear()

    refreshed_settings = get_settings()

    assert refreshed_settings.app_name == "Changed API"

    get_settings.cache_clear()
