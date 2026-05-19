# ADR 0013: Centralized runtime configuration

## Status

Accepted

## Context

Phase 3 introduces the executable backend foundation.

The backend now needs runtime configuration for concerns such as:

- API metadata
- environment name
- logging level
- database URL
- future security settings
- future CORS settings
- future external service URLs

Without a centralized configuration strategy, these values could end up scattered across the codebase.

For example, a non-centralized approach could look like this:

    # interfaces/http/app.py
    app = FastAPI(
        title="FHIR Mini-Gateway API",
        version="0.1.0",
    )

    # infrastructure/logging.py
    logging.basicConfig(level="INFO")

    # infrastructure/persistence/sqlalchemy/database.py
    engine = create_engine(
        "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway"
    )

    # future interfaces/http/middleware.py
    allowed_origins = ["http://localhost:3000"]

This approach works at first, but it spreads runtime configuration across unrelated modules.

As the backend grows, changing configuration would require searching through multiple files, increasing the risk of inconsistency, duplicated defaults, accidental credential exposure, and environment-specific bugs.

## Decision

Use a centralized typed settings model in the infrastructure layer.

Runtime configuration will live in:

    fhir_gateway.infrastructure.config.settings

The settings model will be based on `pydantic-settings`.

Initial settings include:

- `app_name`
- `app_version`
- `environment`
- `log_level`
- `database_url`

Environment variables will use the project prefix:

    FHIR_GATEWAY_

Examples:

    FHIR_GATEWAY_APP_NAME
    FHIR_GATEWAY_APP_VERSION
    FHIR_GATEWAY_ENVIRONMENT
    FHIR_GATEWAY_LOG_LEVEL
    FHIR_GATEWAY_DATABASE_URL

The application runtime will access configuration through:

    get_settings()

Example centralized usage:

    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    configure_logging(settings.log_level)

    engine = create_engine(settings.database_url)

## Rationale

Runtime configuration is an infrastructure concern.

It should not live in the domain layer or application layer.

The domain layer must remain focused on clinical concepts and business invariants.

The application layer must remain focused on use-cases, ports, application models, and application errors.

Centralizing settings provides:

- one place to define configuration defaults
- one place to document available runtime settings
- one place to validate allowed values
- consistent environment variable naming
- easier local development
- easier future deployment configuration
- less risk of hardcoded values spreading across the codebase

Using `pydantic-settings` gives typed settings, defaults, environment variable loading, and validation without manually calling `os.getenv` throughout the project.

## Example: without centralized settings

A scattered approach might look like this:

    # interfaces/http/app.py
    app = FastAPI(
        title=os.getenv("APP_NAME", "FHIR Mini-Gateway API"),
        version=os.getenv("APP_VERSION", "0.1.0"),
    )

    # infrastructure/logging.py
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO")
    )

    # infrastructure/persistence/sqlalchemy/database.py
    engine = create_engine(
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway",
        )
    )

Problems:

- configuration names are generic and may collide with other applications
- defaults are duplicated across modules
- validation is manual or missing
- invalid values may fail late
- future developers must search multiple files to understand runtime configuration
- credentials or environment-specific values are more likely to be hardcoded accidentally

## Example: with centralized settings

A centralized approach looks like this:

    # infrastructure/config/settings.py
    class Settings(BaseSettings):
        app_name: str = "FHIR Mini-Gateway API"
        app_version: str = "0.1.0"
        environment: Literal["local", "test", "development", "production"] = "local"
        log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
        database_url: str = (
            "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway"
        )

        model_config = SettingsConfigDict(
            env_prefix="FHIR_GATEWAY_",
            case_sensitive=False,
        )

    # interfaces/http/app.py
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    # infrastructure/persistence/sqlalchemy/database.py
    engine = create_engine(settings.database_url)

Benefits:

- configuration is discoverable
- defaults are centralized
- allowed values are validated
- environment variables have a clear project prefix
- infrastructure modules do not invent their own configuration names
- future deployment settings can be provided externally

## Alternatives considered

### 1. Hardcode values where they are used

Rejected.

This is simple at the beginning, but it does not scale.

Hardcoded values would make the project harder to configure across local, test, development, and production environments.

It also increases the risk of committing environment-specific values or credentials.

### 2. Use `os.getenv` directly in each module

Rejected.

This avoids an extra dependency, but it spreads configuration access across the codebase.

It also requires manual parsing, validation, defaults, naming discipline, and error handling.

For a growing backend, this becomes repetitive and fragile.

### 3. Use centralized settings with manual parsing

Rejected for now.

A custom settings module could be built manually, but it would duplicate functionality already provided by `pydantic-settings`.

### 4. Use `pydantic-settings`

Accepted.

It provides a small, typed, validated, environment-aware configuration mechanism that fits well with the existing FastAPI/Pydantic ecosystem.

## Consequences

### Positive

- Runtime configuration is centralized.
- Environment variables follow a consistent `FHIR_GATEWAY_` prefix.
- Settings are typed and validated.
- Invalid configuration fails early.
- Domain and application layers stay independent from environment variables.
- Future persistence, security, CORS, and deployment settings have a clear place to live.
- The configuration strategy is easy to explain in a technical interview.

### Negative / Trade-offs

- Adds a dependency on `pydantic-settings`.
- Developers must understand the difference between runtime settings and domain/application logic.
- Cached settings require care in tests when environment variables are modified.

The trade-off is accepted because centralized typed settings improve maintainability and reduce configuration drift.

## Testing implications

Because `get_settings()` is cached, tests that modify environment variables must clear the cache.

Example:

    get_settings.cache_clear()

    monkeypatch.setenv("FHIR_GATEWAY_LOG_LEVEL", "DEBUG")

    settings = get_settings()

    assert settings.log_level == "DEBUG"

    get_settings.cache_clear()

This is expected and acceptable.

## Notes

This ADR does not define deployment-specific secrets management.

Future phases may introduce:

- `.env` loading policy
- Docker Compose environment variables
- CI/CD secrets
- production secret management
- stricter database URL validation

Those decisions will be documented separately if needed.
