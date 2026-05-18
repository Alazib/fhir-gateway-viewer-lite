# ADR 0012: SQLAlchemy persistence foundation and mapping boundaries

## Status

Accepted

## Context

Phase 3 introduces the backend persistence foundation.

The project already has:

- a framework-agnostic domain layer
- an application layer with use-cases and narrow ports
- an HTTP interface based on FastAPI
- infrastructure settings and logging baseline

The application layer currently defines ports such as:

- `PatientReader`
- `PatientSearchReader`
- `ConditionReader`
- `EncounterReader`
- `ObservationReader`
- `ObservationByCodeReader`
- `AuditEventReader`

Phase 3 must introduce concrete persistence infrastructure without breaking the existing architecture.

The key design question is how to add database support while keeping the domain and application layers independent from persistence details.

## Decision

Use:

- SQLAlchemy ORM for persistence models
- Alembic for database migrations
- Psycopg 3 as the PostgreSQL driver
- synchronous SQLAlchemy as the initial persistence approach
- separate ORM models from domain entities
- infrastructure adapters to implement application ports

Persistence code will live under the infrastructure layer.

Initial expected structure:

    fhir_gateway/
    ├── domain/
    ├── application/
    ├── interfaces/
    └── infrastructure/
        └── persistence/
            └── sqlalchemy/
                ├── base.py
                ├── database.py
                └── models/

Alembic migration files will live at the backend project level:

    apps/api/
    ├── alembic.ini
    └── alembic/
        ├── env.py
        └── versions/

## Rationale

The database is an infrastructure detail.

Domain entities must not inherit from SQLAlchemy classes, define database columns, or depend on ORM behavior.

Application use-cases must depend on ports, not on SQLAlchemy sessions or ORM models.

Infrastructure adapters will translate between:

- ORM persistence models
- domain entities
- application ports

This preserves the existing hexagonal architecture.

## Domain entity vs ORM model

Domain entities represent business meaning and invariants.

ORM models represent database persistence shape.

They may look similar, but they have different responsibilities and different reasons to change.

Example domain entity:

    @dataclass(frozen=True, slots=True)
    class Patient:
        id: ResourceId
        identifiers: tuple[Identifier, ...] = ()
        name: HumanName | None = None

Example ORM model:

    class PatientRecord(Base):
        __tablename__ = "patients"

        id: Mapped[str] = mapped_column(String, primary_key=True)
        family_name: Mapped[str | None] = mapped_column(String, nullable=True)

Example mapping direction:

    def patient_record_to_domain(record: PatientRecord) -> Patient:
        return Patient(
            id=ResourceId(record.id),
            name=HumanName(family=record.family_name) if record.family_name else None,
        )

This mapping code is infrastructure code.

It should not live in the domain layer.

## Why separate ORM models from domain entities

Keeping ORM models separate avoids coupling the clinical domain model to:

- SQLAlchemy base classes
- table names
- column definitions
- foreign keys
- lazy loading
- database session lifecycle
- persistence-specific compromises

This keeps domain tests fast and independent.

It also allows the database schema to evolve without forcing every persistence concern into the domain model.

## Why synchronous SQLAlchemy initially

Synchronous SQLAlchemy is selected for the first persistence foundation.

Reasons:

- simpler mental model
- easier to test initially
- easier to teach and explain
- sufficient for the current MVP and portfolio goals
- lower risk of session lifecycle mistakes

Async SQLAlchemy may be reconsidered later if there is a concrete need for high-concurrency async database access.

The project should first establish clean persistence boundaries, mappings, migrations, and adapters.

## Why Alembic

Alembic is used to version database schema changes.

It allows the project to evolve the schema through migrations instead of relying on ad-hoc table creation.

This is important for professional backend development because database schema changes must be reproducible and reviewable.

## Why Psycopg 3

Psycopg 3 is selected as the PostgreSQL driver for new development.

It is the current generation of the PostgreSQL adapter for Python and works with SQLAlchemy.

The initial setup will use the synchronous driver path.

## Alternatives considered

### 1. Use raw SQL only

Rejected.

Raw SQL gives full control, but it increases repetitive mapping code and makes the persistence layer more verbose for the current project stage.

Raw SQL may still be useful later for specific optimized queries.

### 2. Use SQLAlchemy Core only

Rejected for the initial foundation.

SQLAlchemy Core is powerful and explicit, but the ORM gives a clearer starting point for mapping persistence records to domain concepts.

Core may still be used later for specialized queries.

### 3. Use domain entities as ORM models

Rejected.

This would couple the domain layer to SQLAlchemy and persistence details.

It would weaken the clean architecture boundary and make domain tests depend on ORM behavior.

### 4. Use async SQLAlchemy immediately

Rejected for now.

Async persistence adds complexity around sessions, transactions, tests, and endpoint design.

It may be useful later, but it is not necessary for the current MVP.

### 5. Put Alembic inside the Python package

Rejected.

Alembic is a project-level migration tool.

Keeping it under `apps/api/alembic` is conventional and keeps migration scripts separate from the importable application package.

## Consequences

### Positive

- Domain remains persistence-agnostic.
- Application use-cases remain independent from SQLAlchemy.
- Infrastructure owns database details.
- Application ports remain the boundary between use-cases and persistence.
- Alembic provides reproducible schema evolution.
- The architecture is easier to explain in a portfolio or technical interview.
- Persistence can be introduced incrementally through concrete adapters.

### Negative / Trade-offs

- Separate ORM models and domain entities require mapper code.
- There will be some structural duplication between ORM records and domain objects.
- Developers must understand the difference between domain models and persistence models.
- Synchronous persistence may need to be revisited if future concurrency requirements become significant.

The trade-off is accepted because the project prioritizes clean boundaries, professional architecture, and pedagogical clarity.

## Notes

This ADR defines the persistence foundation strategy.

It does not yet define:

- the final database schema
- all ORM models
- all adapters
- seed data strategy
- Docker Compose setup
- PostgreSQL integration testing strategy
- production deployment settings

Those decisions will be handled in later Phase 3 sub-issues or future phases.
