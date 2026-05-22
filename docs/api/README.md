# FHIR Mini-Gateway API Documentation

## Status

Current API status: **Phase 3 / Backend foundation**

The API currently exposes one technical endpoint:

- `GET /health`

The backend now includes an initial persistence foundation based on:

- SQLAlchemy ORM
- Alembic
- Psycopg 3
- centralized runtime database configuration

Clinical endpoints are not implemented yet.

Planned future endpoint groups include:

- patient search
- patient summary
- observation listing by code
- patient bundle export
- audit event listing

---

## Purpose

The FHIR Mini-Gateway API is the HTTP backend interface for the `FHIR Gateway Viewer Lite` project.

The long-term goal is to expose a deliberately scoped FHIR-like API over synthetic clinical data, focused on:

- clean backend architecture
- healthcare interoperability concepts
- structured clinical resources
- traceability
- future EHR-lite viewer integration
- future grounded Applied AI Engineering features

This project must only use synthetic/demo data.

Do not use real patient data.

---

## Current HTTP structure

Current structure:

    apps/api/src/fhir_gateway/interfaces/http/
    ├── __init__.py
    ├── app.py
    ├── main.py
    └── routers/
        ├── __init__.py
        └── health.py

Responsibilities:

- `app.py`: creates and configures the FastAPI application.
- `main.py`: exposes the ASGI `app` object used by Uvicorn.
- `routers/health.py`: defines the `/health` endpoint.

The HTTP layer may depend on FastAPI.

The domain and application layers must not depend on FastAPI.

---

## Runtime configuration

Runtime settings are defined in:

    apps/api/src/fhir_gateway/infrastructure/config/settings.py

Current settings:

| Setting | Environment variable | Default |
|---|---|---|
| `app_name` | `FHIR_GATEWAY_APP_NAME` | `FHIR Mini-Gateway API` |
| `app_version` | `FHIR_GATEWAY_APP_VERSION` | `0.1.0` |
| `environment` | `FHIR_GATEWAY_ENVIRONMENT` | `local` |
| `log_level` | `FHIR_GATEWAY_LOG_LEVEL` | `INFO` |
| `database_url` | `FHIR_GATEWAY_DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway` |

Allowed `environment` values:

    local
    test
    development
    production

Allowed `log_level` values:

    DEBUG
    INFO
    WARNING
    ERROR
    CRITICAL

Example PowerShell overrides:

    $env:FHIR_GATEWAY_LOG_LEVEL = "DEBUG"
    $env:FHIR_GATEWAY_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway"

Settings are loaded through `pydantic-settings`.

Runtime configuration is centralized so that infrastructure concerns such as logging and database connectivity do not define their own scattered environment variable logic.

---

## Logging

Basic logging is configured in:

    apps/api/src/fhir_gateway/infrastructure/logging.py

Current format:

    %(asctime)s %(levelname)s [%(name)s] %(message)s

Example output:

    2026-05-18 10:30:00 INFO [fhir_gateway.interfaces.http.app] Creating FastAPI application for environment: local

Logging is configured during FastAPI app creation using the configured `FHIR_GATEWAY_LOG_LEVEL`.

---

## Persistence foundation

The backend includes an initial persistence foundation.

Current structure:

    apps/api/src/fhir_gateway/infrastructure/persistence/
    ├── __init__.py
    └── sqlalchemy/
        ├── __init__.py
        ├── base.py
        ├── database.py
        └── models/
            └── __init__.py

Responsibilities:

- `base.py`: defines the SQLAlchemy declarative `Base`.
- `database.py`: provides helpers to create SQLAlchemy engines and session factories.
- `models/`: reserved for future SQLAlchemy ORM models.

The persistence layer belongs to infrastructure.

Domain and application layers must not import SQLAlchemy.

---

## SQLAlchemy base

The SQLAlchemy declarative base is defined in:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/base.py

It exposes:

    Base.metadata

This metadata will be used by future ORM models and by Alembic migrations.

At the current stage, no clinical ORM models have been implemented yet.

---

## Database engine and session factory

Database helpers are defined in:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/database.py

Current helpers:

    create_database_engine(database_url)
    create_session_factory(engine)

The intended future flow is:

    Settings.database_url
        -> create_database_engine(...)
        -> create_session_factory(...)
        -> SQLAlchemy infrastructure adapters

The API does not yet open database sessions for HTTP requests.

---

## Alembic migrations

Alembic has been initialized under:

    apps/api/alembic/

Current Alembic files:

    apps/api/
    ├── alembic.ini
    └── alembic/
        ├── env.py
        ├── script.py.mako
        └── versions/

Alembic is configured to use:

- `Settings.database_url`
- `Base.metadata`

The `alembic.ini` file prepends `src` to the Python path so Alembic can import the `fhir_gateway` package.

Do not run database migrations yet unless a local PostgreSQL database has been created and configured.

No migration revisions have been created yet because no ORM models exist yet.

---

## Local development

Run all backend commands from:

    apps/api

Activate the Pipenv environment:

    pipenv shell

Or run commands directly:

    pipenv run <command>

Install dependencies:

    pipenv install

---

## Running the API locally

Because the backend uses a `src/` layout, the package lives under:

    apps/api/src/fhir_gateway

Run the API from `apps/api` with:

    pipenv run uvicorn fhir_gateway.interfaces.http.main:app --reload --app-dir src

The API starts at:

    http://127.0.0.1:8000

Stop the server with:

    CTRL + C

---

## Interactive documentation

FastAPI exposes interactive API documentation automatically.

Swagger UI:

    http://127.0.0.1:8000/docs

ReDoc:

    http://127.0.0.1:8000/redoc

At the current stage, these pages only expose `/health`.

---

## Endpoint: Health check

### `GET /health`

Checks whether the API process is alive and responding.

This is a technical endpoint.

It does not access:

- domain entities
- application use-cases
- database
- authentication
- clinical data

### Request

    GET /health

### Successful response

Status code:

    200 OK

Body:

    {
      "status": "ok"
    }

### Browser example

Open:

    http://127.0.0.1:8000/health

Expected response:

    {
      "status": "ok"
    }

### PowerShell example

    Invoke-RestMethod http://127.0.0.1:8000/health

### curl example

    curl http://127.0.0.1:8000/health

---

## Testing

Run the full test suite from `apps/api`:

    pipenv run pytest

Run HTTP tests:

    pipenv run pytest tests/unit/interfaces/http

Run settings tests:

    pipenv run pytest tests/unit/infrastructure/config/test_settings.py

Run logging tests:

    pipenv run pytest tests/unit/infrastructure/test_logging.py

Run persistence foundation tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy

Run architecture boundary tests:

    pipenv run pytest tests/unit/architecture

---

## Current limitations

The API does not yet expose:

- patient search
- patient summary retrieval
- observation filtering
- bundle export
- audit event listing
- authentication
- authorization
- persistence-backed clinical data
- application use-case wiring through HTTP
- API error response envelope
- clinical Pydantic request/response schemas
- concrete SQLAlchemy adapters
- clinical ORM models
- database migrations for clinical tables
- seed data

These capabilities are intentionally deferred.

---

## Planned endpoints

The following endpoints are planned but not implemented yet.

### Patient search

    GET /patients?search={text}

Related use-case:

    SearchPatientsUseCase

---

### Patient summary

    GET /patients/{patient_id}/summary

Related use-case:

    GetPatientSummaryUseCase

---

### Observations by code

    GET /patients/{patient_id}/observations?system={system}&code={code}

Related use-case:

    ListObservationsByCodeUseCase

Clinical code identity should be based on:

- `system`
- `code`

The display text should not be used as the code identity.

---

### Patient bundle export

    GET /patients/{patient_id}/bundle

Related use-case:

    ExportPatientBundleUseCase

The application layer returns a `PatientBundle` application model.

Final HTTP JSON serialization will be handled in the API/interface layer later.

---

### Audit events

    GET /audit-events?limit={limit}

Related use-case:

    ListAuditEventsUseCase

Initial expected behavior:

- default limit: `50`
- maximum limit: `100`
- ordered from newest to oldest

Advanced audit filtering and pagination are deferred.

---

## API design principles

As the API evolves:

1. Keep routers thin.
2. Do not put business logic in routers.
3. Do not put persistence logic in routers.
4. Keep domain independent from HTTP.
5. Keep application independent from HTTP.
6. Keep domain independent from SQLAlchemy.
7. Keep application independent from SQLAlchemy.
8. Use infrastructure adapters to implement application ports.
9. Preserve structured clinical evidence in API responses.
10. Avoid broad generic repositories until repeated adapter needs justify them.

---

## Persistence design principles

As persistence evolves:

1. Keep ORM models separate from domain entities.
2. Keep SQLAlchemy imports inside infrastructure.
3. Map ORM records to domain entities in infrastructure adapters or mappers.
4. Keep application ports expressed in domain/application types.
5. Use Alembic for schema changes.
6. Do not create tables manually outside migrations once migrations are active.
7. Do not expose ORM records directly from application use-cases.

---

## Error handling

A standard API error response envelope has not been defined yet.

Future HTTP endpoints will need to map application errors such as:

- `ApplicationValidationError`
- `ApplicationNotFoundError`

to HTTP responses such as:

- `400 Bad Request`
- `404 Not Found`

This will be decided before exposing clinical use-cases through HTTP.

---

## Security status

Authentication and authorization are not implemented yet.

The current `/health` endpoint is public.

Future clinical and audit endpoints should not be treated as public by default.

Authentication, RBAC, and audit trail enforcement belong to later phases.

The current local default `database_url` is for development only.

Production database credentials must be provided through environment variables or a future secrets management strategy.
