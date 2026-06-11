# FHIR Mini-Gateway API Documentation

## Status

Current API status: **Phase 3 / Backend foundation**

The API currently exposes one technical endpoint:

- `GET /health`

The backend includes:

- clean FastAPI application structure
- centralized runtime configuration
- logging baseline
- SQLAlchemy/Alembic persistence foundation
- Patient persistence schema
- Patient identifier persistence schema
- Observation code catalog persistence schema
- Condition code catalog persistence schema
- Observation persistence schema
- Condition persistence schema
- Encounter persistence schema
- logical deletion metadata for top-level clinical resources
- AuditEvent persistence schema

Clinical HTTP endpoints are not implemented yet.

No clinical HTTP endpoint is currently backed by database persistence.

No audit HTTP endpoint is currently backed by database persistence.

Planned future endpoint groups include:

- patient search
- patient summary
- observation listing by code
- patient bundle export
- audit event listing

For persistence details, see:

    docs/persistence/README.md

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

## Persistence status

The backend includes a SQLAlchemy/Alembic persistence foundation.

Current persistence status:

- Patient ORM schema exists.
- Patient identifier ORM schema exists.
- Observation code catalog ORM schema exists.
- Condition code catalog ORM schema exists.
- Observation ORM schema exists.
- Condition ORM schema exists.
- Encounter ORM schema exists.
- Top-level clinical resources include logical deletion metadata through `deleted_at`.
- AuditEvent ORM schema exists.
- ORM/domain mappers are pending.
- SQLAlchemy adapters are pending.
- Request-scoped SQLAlchemy session management is pending.
- No clinical HTTP endpoint uses persistence yet.
- No audit HTTP endpoint uses persistence yet.

Current top-level clinical resource tables with logical deletion metadata:

- `patients.deleted_at`
- `observations.deleted_at`
- `conditions.deleted_at`
- `encounters.deleted_at`

Current audit table:

- `audit_events`

The API does not expose `deleted_at` through HTTP responses at this stage.

The API does not expose `audit_events` through HTTP at this stage.

Current Alembic migration chain:

    <base>
        ↓
    f97f9d019499_create_patient_tables
        ↓
    ab48a83daad7_add_clinical_resource_tables
        ↓
    d4e8f2a1c9b7_add_logical_deletion_columns_to_clinical_resources
        ↓
    a6f3c9d2e1b8_add_audit_event_table

Persistence details are documented separately in:

    docs/persistence/README.md

Logical deletion strategy is documented in:

    docs/adr/0016-clinical-resource-logical-deletion-strategy.md

AuditEvent persistence strategy is documented in:

    docs/adr/0015-audit-event-persistence-strategy.md

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
- audit data

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

Run architecture boundary tests:

    pipenv run pytest tests/unit/architecture

Run persistence tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy

Run ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models

Run Patient ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_patient_orm_models.py

Run clinical resource ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_clinical_resource_orm_models.py

Run AuditEvent ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_audit_event_orm_models.py

Useful Alembic inspection commands:

    pipenv run alembic history --verbose
    pipenv run alembic heads --verbose
    pipenv run alembic upgrade head --sql
    pipenv run alembic upgrade base:head --sql
    pipenv run alembic downgrade a6f3c9d2e1b8:d4e8f2a1c9b7 --sql

Do not run database migrations against PostgreSQL until a local PostgreSQL workflow has been created and configured.

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
- persistence-backed audit data
- application use-case wiring through HTTP
- API error response envelope
- clinical Pydantic request/response schemas
- audit Pydantic response schemas
- concrete SQLAlchemy adapters
- ORM/domain mappers
- request-scoped SQLAlchemy session dependency
- seed data

These capabilities are intentionally deferred.

---

## Planned endpoints

The following endpoints are planned but not implemented yet.

### Patient search

    GET /patients?search={text}

Related use-case:

    SearchPatientsUseCase

Future persistence behavior:

- should query `patients`
- should hide logically deleted patients by default using `patients.deleted_at IS NULL`

---

### Patient summary

    GET /patients/{patient_id}/summary

Related use-case:

    GetPatientSummaryUseCase

Future persistence behavior:

- should query Patient data
- should include related Observations, Conditions, and Encounters
- should hide logically deleted resources by default

---

### Observations by code

    GET /patients/{patient_id}/observations?system={system}&code={code}

Related use-case:

    ListObservationsByCodeUseCase

Clinical code identity should be based on:

- `system`
- `code`

The display text should not be used as the code identity.

Future persistence behavior:

- should query `observations`
- should join or resolve `observation_codes`
- should hide logically deleted observations by default

---

### Patient bundle export

    GET /patients/{patient_id}/bundle

Related use-case:

    ExportPatientBundleUseCase

The application layer returns a `PatientBundle` application model.

Final HTTP JSON serialization will be handled in the API/interface layer later.

Future persistence behavior:

- should export the patient bundle from persistence-backed data
- should define explicitly whether logically deleted resources are excluded by default

---

### Audit events

    GET /audit-events?limit={limit}

Related use-case:

    ListAuditEventsUseCase

Initial expected behavior:

- default limit: `50`
- maximum limit: `100`
- ordered from newest to oldest

Current persistence status:

- `audit_events` table exists
- HTTP endpoint is not implemented yet
- SQLAlchemy audit adapter is not implemented yet
- ORM/domain mapper is not implemented yet

Advanced audit filtering and pagination are deferred.

---

## Logical deletion API behavior

Logical deletion has been introduced at the persistence schema level only.

Affected tables:

- `patients`
- `observations`
- `conditions`
- `encounters`

Current API behavior:

- no endpoint exposes `deleted_at`
- no endpoint performs logical deletion
- no endpoint restores logically deleted resources
- no endpoint includes deleted resources by explicit option

Future ordinary clinical endpoints should hide logically deleted resources by default.

Future admin/audit endpoints may decide whether deleted resources can be queried explicitly.

The exact HTTP response behavior for logically deleted resources, such as `404 Not Found`, will be decided when persistence-backed endpoints are implemented.

---

## Audit API behavior

AuditEvent persistence exists at the database schema level.

Current table:

    audit_events

Current API behavior:

- no `/audit-events` endpoint exists yet
- no persistence-backed audit listing exists yet
- no audit write pipeline exists yet
- no current-agent provider exists yet
- no authentication or authorization exists yet

Future audit listing should use:

    ListAuditEventsUseCase

and return audit events ordered from newest to oldest.

Future audit creation must not allow arbitrary user-controlled request bodies to decide the `agent` value.

The `agent` should come from trusted runtime context, such as:

- authenticated principal
- system identity
- background job identity
- local/demo identity

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
11. Hide logically deleted clinical resources from ordinary public reads by default.
12. Do not expose technical persistence metadata unless explicitly designed.
13. Do not let arbitrary request input define audit `agent`.

---

## Error handling

A standard API error response envelope has not been defined yet.

Future HTTP endpoints will need to map application errors such as:

- `ApplicationValidationError`
- `ApplicationNotFoundError`

to HTTP responses such as:

- `400 Bad Request`
- `404 Not Found`

Logical deletion may affect future not-found semantics.

For ordinary clinical endpoints, a logically deleted resource may be treated as not found unless an explicit admin/audit endpoint says otherwise.

This will be decided before exposing clinical use-cases through HTTP.

---

## Security status

Authentication and authorization are not implemented yet.

The current `/health` endpoint is public.

Future clinical and audit endpoints should not be treated as public by default.

Authentication, RBAC, and audit trail enforcement belong to later phases.

Audit event creation should eventually use trusted runtime context for `agent`.

The current local default `database_url` is for development only.

Production database credentials must be provided through environment variables or a future secrets management strategy.

---

## Related documentation

Persistence documentation:

    docs/persistence/README.md

Related ADRs:

- ADR 0011: HTTP API structure and runtime composition
- ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
- ADR 0013: Centralized runtime configuration
- ADR 0014: Database timestamp and audit metadata strategy
- ADR 0015: AuditEvent persistence strategy
- ADR 0016: Clinical resource logical deletion strategy
