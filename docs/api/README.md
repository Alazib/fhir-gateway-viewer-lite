# FHIR Mini-Gateway API Documentation

## Status

Current API status: **Phase 3 / Backend foundation**

The API currently exposes one technical endpoint:

* `GET /health`

The backend includes:

* clean FastAPI application structure
* centralized runtime configuration
* logging baseline
* SQLAlchemy/Alembic persistence foundation
* Patient persistence schema
* Patient identifier persistence schema
* Observation code catalog persistence schema
* Condition code catalog persistence schema
* Observation persistence schema
* Condition persistence schema
* Encounter persistence schema
* logical deletion metadata for top-level clinical resources
* AuditEvent persistence schema
* ORM/domain mappers for the current read-side persistence resources
* SQLAlchemy read adapters for the current application ports
* request-scoped SQLAlchemy session management through HTTP dependencies
* HTTP dependency wiring for the current read-side application use-cases

Clinical HTTP endpoints are not implemented yet.

Audit HTTP endpoints are not implemented yet.

No clinical or audit HTTP endpoint is currently exposed over persistence-backed data.

However, persistence-backed read-side dependency wiring is now implemented for the current Phase 2 application use-cases.

Planned future endpoint groups include:

* patient search
* patient summary
* observation listing by code
* patient bundle export
* audit event listing

For persistence details, see:

```
docs/persistence/README.md
```

---

## Purpose

The FHIR Mini-Gateway API is the HTTP backend interface for the `FHIR Gateway Viewer Lite` project.

The long-term goal is to expose a deliberately scoped FHIR-like API over synthetic clinical data, focused on:

* clean backend architecture
* healthcare interoperability concepts
* structured clinical resources
* traceability
* future EHR-lite viewer integration
* future grounded Applied AI Engineering features

This project must only use synthetic/demo data.

Do not use real patient data.

---

## Current HTTP structure

Current structure:

```
apps/api/src/fhir_gateway/interfaces/http/
├── __init__.py
├── app.py
├── main.py
├── dependencies/
│   ├── __init__.py
│   ├── adapters.py
│   ├── database.py
│   └── use_cases.py
└── routers/
    ├── __init__.py
    └── health.py
```

Responsibilities:

* `app.py`: creates and configures the FastAPI application.
* `main.py`: exposes the ASGI `app` object used by Uvicorn.
* `dependencies/database.py`: provides request-scoped SQLAlchemy session access.
* `dependencies/adapters.py`: wires SQLAlchemy read adapters from the current request session.
* `dependencies/use_cases.py`: wires application use-cases from concrete read adapters.
* `routers/health.py`: defines the `/health` endpoint.

The HTTP layer may depend on FastAPI.

The HTTP dependency layer may compose application use-cases, infrastructure adapters, and SQLAlchemy session management.

The domain and application layers must not depend on FastAPI.

The domain and application layers must not depend on SQLAlchemy.

---

## Runtime configuration

Runtime settings are defined in:

```
apps/api/src/fhir_gateway/infrastructure/config/settings.py
```

Current settings:

| Setting        | Environment variable        | Default                                                              |
| -------------- | --------------------------- | -------------------------------------------------------------------- |
| `app_name`     | `FHIR_GATEWAY_APP_NAME`     | `FHIR Mini-Gateway API`                                              |
| `app_version`  | `FHIR_GATEWAY_APP_VERSION`  | `0.1.0`                                                              |
| `environment`  | `FHIR_GATEWAY_ENVIRONMENT`  | `local`                                                              |
| `log_level`    | `FHIR_GATEWAY_LOG_LEVEL`    | `INFO`                                                               |
| `database_url` | `FHIR_GATEWAY_DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway` |

Allowed `environment` values:

```
local
test
development
production
```

Allowed `log_level` values:

```
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Example PowerShell overrides:

```
$env:FHIR_GATEWAY_LOG_LEVEL = "DEBUG"
$env:FHIR_GATEWAY_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway"
```

Settings are loaded through `pydantic-settings`.

Runtime configuration is centralized so that infrastructure concerns such as logging and database connectivity do not define their own scattered environment variable logic.

---

## Logging

Basic logging is configured in:

```
apps/api/src/fhir_gateway/infrastructure/logging.py
```

Current format:

```
%(asctime)s %(levelname)s [%(name)s] %(message)s
```

Example output:

```
2026-05-18 10:30:00 INFO [fhir_gateway.interfaces.http.app] Creating FastAPI application for environment: local
```

Logging is configured during FastAPI app creation using the configured `FHIR_GATEWAY_LOG_LEVEL`.

---

## Persistence status

The backend includes a SQLAlchemy/Alembic persistence foundation.

Current persistence status:

* Patient ORM schema exists.
* Patient identifier ORM schema exists.
* Observation code catalog ORM schema exists.
* Condition code catalog ORM schema exists.
* Observation ORM schema exists.
* Condition ORM schema exists.
* Encounter ORM schema exists.
* Top-level clinical resources include logical deletion metadata through `deleted_at`.
* AuditEvent ORM schema exists.
* ORM/domain mappers exist for current read-side persistence resources.
* SQLAlchemy read adapters exist for current application ports.
* Request-scoped SQLAlchemy session management exists through HTTP dependencies.
* Application use-case dependency wiring exists for current read-side use-cases.
* No clinical HTTP endpoint uses persistence yet.
* No audit HTTP endpoint uses persistence yet.

Current top-level clinical resource tables with logical deletion metadata:

* `patients.deleted_at`
* `observations.deleted_at`
* `conditions.deleted_at`
* `encounters.deleted_at`

Current audit table:

* `audit_events`

The API does not expose `deleted_at` through HTTP responses at this stage.

The API does not expose `audit_events` through HTTP at this stage.

Current Alembic migration chain:

```
<base>
    ↓
f97f9d019499_create_patient_tables
    ↓
ab48a83daad7_add_clinical_resource_tables
    ↓
d4e8f2a1c9b7_add_logical_deletion_columns_to_clinical_resources
    ↓
a6f3c9d2e1b8_add_audit_event_table
```

Persistence details are documented separately in:

```
docs/persistence/README.md
```

Logical deletion strategy is documented in:

```
docs/adr/0016-clinical-resource-logical-deletion-strategy.md
```

AuditEvent persistence strategy is documented in:

```
docs/adr/0015-audit-event-persistence-strategy.md
```

---

## HTTP dependency wiring

The API now includes HTTP dependency wiring for persistence-backed read use-cases.

This wiring is intentionally located in:

```
apps/api/src/fhir_gateway/interfaces/http/dependencies/
```

Current dependency modules:

```
database.py
adapters.py
use_cases.py
```

Responsibilities:

* `database.py` provides request-scoped SQLAlchemy session access.
* `adapters.py` builds SQLAlchemy read adapters from the current request session.
* `use_cases.py` builds application use-cases from those adapters.

Runtime flow:

```
FastAPI request
    -> get_database_session()
        -> SQLAlchemy Session
            -> SQLAlchemy read adapters
                -> application use-cases
```

The application startup flow prepares the session factory:

```
Settings.database_url
    -> create_database_engine(...)
    -> create_session_factory(...)
    -> app.state.session_factory
```

The request flow then uses that factory:

```
request
    -> request.app
        -> request.app.state.session_factory
            -> Session for the current request
```

The current request-scoped dependency is:

```
get_database_session(request)
```

It creates one SQLAlchemy `Session` for the current HTTP request and closes it when the request finishes.

The current adapter dependencies are:

```
get_patient_reader()
get_observation_reader()
get_condition_reader()
get_encounter_reader()
get_audit_event_reader()
```

The current use-case dependencies are:

```
get_search_patients_use_case()
get_patient_summary_use_case()
get_list_observations_by_code_use_case()
get_export_patient_bundle_use_case()
get_list_audit_events_use_case()
```

Important boundary rule:

Routers must not instantiate SQLAlchemy sessions, SQLAlchemy adapters, or application use-cases manually.

Routers should receive already-wired use-cases through FastAPI dependencies.

Domain and application layers remain independent from FastAPI and SQLAlchemy.

Current status:

* request-scoped SQLAlchemy session dependency: implemented
* SQLAlchemy read adapter dependencies: implemented
* application use-case dependencies: implemented
* clinical routers: not implemented yet
* audit routers: not implemented yet
* API error response envelope: not implemented yet
* clinical Pydantic request/response schemas: not implemented yet
* audit Pydantic response schemas: not implemented yet

Clinical and audit endpoints remain intentionally deferred until endpoint contracts, response schemas, and error mapping are designed.

---

## Local development

Run all backend commands from:

```
apps/api
```

Activate the Pipenv environment:

```
pipenv shell
```

Or run commands directly:

```
pipenv run <command>
```

Install dependencies:

```
pipenv install
```

---

## Running the API locally

Because the backend uses a `src/` layout, the package lives under:

```
apps/api/src/fhir_gateway
```

Run the API from `apps/api` with:

```
pipenv run uvicorn fhir_gateway.interfaces.http.main:app --reload --app-dir src
```

The API starts at:

```
http://127.0.0.1:8000
```

Stop the server with:

```
CTRL + C
```

---

## Interactive documentation

FastAPI exposes interactive API documentation automatically.

Swagger UI:

```
http://127.0.0.1:8000/docs
```

ReDoc:

```
http://127.0.0.1:8000/redoc
```

At the current stage, these pages only expose `/health`.

---

## Endpoint: Health check

### `GET /health`

Checks whether the API process is alive and responding.

This is a technical endpoint.

It does not access:

* domain entities
* application use-cases
* database
* authentication
* clinical data
* audit data

### Request

```
GET /health
```

### Successful response

Status code:

```
200 OK
```

Body:

```
{
  "status": "ok"
}
```

### Browser example

Open:

```
http://127.0.0.1:8000/health
```

Expected response:

```
{
  "status": "ok"
}
```

### PowerShell example

```
Invoke-RestMethod http://127.0.0.1:8000/health
```

### curl example

```
curl http://127.0.0.1:8000/health
```

---

## Testing

Run the full test suite from `apps/api`:

```
pipenv run pytest
```

Run HTTP tests:

```
pipenv run pytest tests/unit/interfaces/http
```

Run HTTP dependency wiring tests:

```
pipenv run pytest tests/unit/interfaces/http/dependencies
```

Run settings tests:

```
pipenv run pytest tests/unit/infrastructure/config/test_settings.py
```

Run logging tests:

```
pipenv run pytest tests/unit/infrastructure/test_logging.py
```

Run architecture boundary tests:

```
pipenv run pytest tests/unit/architecture
```

Run persistence tests:

```
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy
```

Run ORM model tests:

```
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models
```

Run Patient ORM model tests:

```
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_patient_orm_models.py
```

Run clinical resource ORM model tests:

```
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_clinical_resource_orm_models.py
```

Run AuditEvent ORM model tests:

```
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_audit_event_orm_models.py
```

Run ORM/domain mapper tests:

```
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/mappers
```

Run SQLAlchemy adapter tests:

```
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/adapters
```

Useful Alembic inspection commands:

```
pipenv run alembic history --verbose
pipenv run alembic heads --verbose
pipenv run alembic upgrade head --sql
pipenv run alembic upgrade base:head --sql
pipenv run alembic downgrade a6f3c9d2e1b8:d4e8f2a1c9b7 --sql
```

Do not run database migrations against PostgreSQL until a local PostgreSQL workflow has been created and configured.

---

## Current limitations

The API does not yet expose:

* patient search
* patient summary retrieval
* observation filtering
* bundle export
* audit event listing
* authentication
* authorization
* persistence-backed clinical endpoints
* persistence-backed audit endpoints
* API error response envelope
* clinical Pydantic request/response schemas
* audit Pydantic response schemas
* seed data

These capabilities are intentionally deferred.

The API already contains read-side wiring for the current application use-cases, but no router consumes that wiring yet.

---

## Planned endpoints

The following endpoints are planned but not implemented yet.

### Patient search

```
GET /patients?search={text}
```

Related use-case:

```
SearchPatientsUseCase
```

Current persistence/wiring status:

* Patient ORM schema exists.
* Patient ORM/domain mapper exists.
* SQLAlchemy patient reader/search adapter exists.
* HTTP dependency wiring for `SearchPatientsUseCase` exists.
* HTTP endpoint is not implemented yet.

Expected persistence behavior:

* should query `patients`
* should search by patient id, patient name fields, and patient identifiers where supported by the adapter
* should hide logically deleted patients by default using `patients.deleted_at IS NULL`

---

### Patient summary

```
GET /patients/{patient_id}/summary
```

Related use-case:

```
GetPatientSummaryUseCase
```

Current persistence/wiring status:

* Patient, Observation, Condition, and Encounter ORM schemas exist.
* ORM/domain mappers exist for the involved resources.
* SQLAlchemy read adapters exist for the involved resources.
* HTTP dependency wiring for `GetPatientSummaryUseCase` exists.
* HTTP endpoint is not implemented yet.

Expected persistence behavior:

* should query Patient data
* should include related Observations, Conditions, and Encounters
* should hide logically deleted resources by default

---

### Observations by code

```
GET /patients/{patient_id}/observations?system={system}&code={code}
```

Related use-case:

```
ListObservationsByCodeUseCase
```

Clinical code identity should be based on:

* `system`
* `code`

The display text should not be used as the code identity.

Current persistence/wiring status:

* Observation ORM schema exists.
* Observation code catalog ORM schema exists.
* Observation ORM/domain mapper exists.
* SQLAlchemy observation reader/by-code adapter exists.
* HTTP dependency wiring for `ListObservationsByCodeUseCase` exists.
* HTTP endpoint is not implemented yet.

Expected persistence behavior:

* should query `observations`
* should join or resolve `observation_codes`
* should hide logically deleted observations by default

---

### Patient bundle export

```
GET /patients/{patient_id}/bundle
```

Related use-case:

```
ExportPatientBundleUseCase
```

The application layer returns a `PatientBundle` application model.

Final HTTP JSON serialization will be handled in the API/interface layer later.

Current persistence/wiring status:

* Patient, Observation, Condition, and Encounter ORM schemas exist.
* ORM/domain mappers exist for the involved resources.
* SQLAlchemy read adapters exist for the involved resources.
* HTTP dependency wiring for `ExportPatientBundleUseCase` exists.
* HTTP endpoint is not implemented yet.

Expected persistence behavior:

* should export the patient bundle from persistence-backed data
* should exclude logically deleted resources by default for ordinary clinical reads unless a later design explicitly says otherwise

---

### Audit events

```
GET /audit-events?limit={limit}
```

Related use-case:

```
ListAuditEventsUseCase
```

Initial expected behavior:

* default limit: `50`
* maximum limit: `100`
* ordered from newest to oldest

Current persistence/wiring status:

* `audit_events` table exists
* AuditEvent ORM/domain mapper exists
* SQLAlchemy audit event reader adapter exists
* HTTP dependency wiring for `ListAuditEventsUseCase` exists
* HTTP endpoint is not implemented yet

Advanced audit filtering and pagination are deferred.

---

## Logical deletion API behavior

Logical deletion has been introduced at the persistence schema level.

Affected tables:

* `patients`
* `observations`
* `conditions`
* `encounters`

Current API behavior:

* no endpoint exposes `deleted_at`
* no endpoint performs logical deletion
* no endpoint restores logically deleted resources
* no endpoint includes deleted resources by explicit option
* no clinical endpoint is currently exposed over persistence-backed data

Current persistence adapter behavior:

* ordinary read adapters hide logically deleted top-level clinical resources by default

Future ordinary clinical endpoints should preserve that behavior and hide logically deleted resources by default.

Future admin/audit endpoints may decide whether deleted resources can be queried explicitly.

The exact HTTP response behavior for logically deleted resources, such as `404 Not Found`, will be decided when persistence-backed endpoints are implemented.

---

## Audit API behavior

AuditEvent persistence exists at the database schema level.

Current table:

```
audit_events
```

Current API behavior:

* no `/audit-events` endpoint exists yet
* no audit write pipeline exists yet
* no current-agent provider exists yet
* no authentication or authorization exists yet

Current read-side wiring status:

* `ListAuditEventsUseCase` exists
* SQLAlchemy audit event reader adapter exists
* HTTP dependency wiring for audit event listing exists
* audit events would be read from persistence once an endpoint consumes the dependency

Future audit listing should use:

```
ListAuditEventsUseCase
```

and return audit events ordered from newest to oldest.

Future audit creation must not allow arbitrary user-controlled request bodies to decide the `agent` value.

The `agent` should come from trusted runtime context, such as:

* authenticated principal
* system identity
* background job identity
* local/demo identity

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
9. Use HTTP dependencies as the runtime composition layer for sessions, adapters, and use-cases.
10. Preserve structured clinical evidence in API responses.
11. Avoid broad generic repositories until repeated adapter needs justify them.
12. Hide logically deleted clinical resources from ordinary public reads by default.
13. Do not expose technical persistence metadata unless explicitly designed.
14. Do not let arbitrary request input define audit `agent`.

---

## Error handling

A standard API error response envelope has not been defined yet.

Future HTTP endpoints will need to map application errors such as:

* `ApplicationValidationError`
* `ApplicationNotFoundError`

to HTTP responses such as:

* `400 Bad Request`
* `404 Not Found`

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

```
docs/persistence/README.md
```

Related ADRs:

* ADR 0011: HTTP API structure and runtime composition
* ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
* ADR 0013: Centralized runtime configuration
* ADR 0014: Database timestamp and audit metadata strategy
* ADR 0015: AuditEvent persistence strategy
* ADR 0016: Clinical resource logical deletion strategy
