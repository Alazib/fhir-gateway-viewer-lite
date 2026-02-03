This structure is designed for a **modular monolith** with a **hexagonal/clean architecture** in the backend and a minimal, iterative frontend. The "backend-first" concept and the FHIR-like scope plus clinical viewer are aligned with the project context.

## Directory Tree (high level)

.
├─ README.md
├─ LICENSE
├─ .gitignore
├─ .editorconfig
├─ .gitattributes
├─ .github/
│  ├─ ISSUE_TEMPLATE/
│  ├─ PULL_REQUEST_TEMPLATE.md
│  └─ workflows/
│     ├─ ci_backend.yml
│     └─ ci_frontend.yml
├─ docs/
│  ├─ roadmap.md
│  ├─ phase-0-preparacion-y-gobernanza.md
│  ├─ architecture/
│  │  ├─ overview.md
│  │  ├─ context-diagram.md
│  │  └─ data-model.md
│  ├─ adr/
│  │  ├─ ADR-0000-template.md
│  │  ├─ ADR-0001-repo-structure.md
│  │  └─ (más ADRs…)
│  └─ api/
│     ├─ openapi-public.md
│     └─ examples/
│        ├─ patient-summary.json
│        └─ bundle-export.json
├─ infra/
│  ├─ docker/
│  │  ├─ api.Dockerfile
│  │  └─ web.Dockerfile
│  └─ docker-compose.yml
├─ apps/
│  ├─ api/
│  │  ├─ pyproject.toml
│  │  ├─ poetry.lock              (or requirements*.txt)
│  │  ├─ alembic.ini
│  │  ├─ alembic/
│  │  │  ├─ env.py
│  │  │  └─ versions/
│  │  ├─ src/
│  │  │  └─ fhir_gateway/
│  │  │     ├─ __init__.py
│  │  │     ├─ domain/
│  │  │     │  ├─ model/
│  │  │     │  │  ├─ patient.py
│  │  │     │  │  ├─ observation.py
│  │  │     │  │  ├─ condition.py
│  │  │     │  │  ├─ encounter.py
│  │  │     │  │  └─ audit_event.py
│  │  │     │  ├─ services/
│  │  │     │  └─ errors.py
│  │  │     ├─ application/
│  │  │     │  ├─ ports/
│  │  │     │  │  ├─ repositories.py
│  │  │     │  │  ├─ auth.py
│  │  │     │  │  └─ audit.py
│  │  │     │  ├─ use_cases/
│  │  │     │  │  ├─ get_patient_summary.py
│  │  │     │  │  ├─ search_patients.py
│  │  │     │  │  ├─ create_observation.py
│  │  │     │  │  └─ export_bundle.py
│  │  │     │  └─ dtos/
│  │  │     ├─ infrastructure/
│  │  │     │  ├─ db/
│  │  │     │  │  ├─ sqlalchemy/
│  │  │     │  │  │  ├─ base.py
│  │  │     │  │  │  ├─ session.py
│  │  │     │  │  │  └─ models.py
│  │  │     │  │  └─ migrations/
│  │  │     │  ├─ repositories/
│  │  │     │  ├─ auth/
│  │  │     │  └─ audit/
│  │  │     ├─ interfaces/
│  │  │     │  ├─ http/
│  │  │     │  │  ├─ main.py
│  │  │     │  │  ├─ dependencies.py
│  │  │     │  │  ├─ routes/
│  │  │     │  │  │  ├─ patients.py
│  │  │     │  │  │  ├─ observations.py
│  │  │     │  │  │  ├─ conditions.py
│  │  │     │  │  │  ├─ encounters.py
│  │  │     │  │  │  └─ export.py
│  │  │     │  │  └─ schemas/
│  │  │     │  │     ├─ fhir_like.py
│  │  │     │  │     └─ api.py
│  │  │     │  └─ cli/
│  │  │     ├─ catalogs/
│  │  │     │  ├─ loinc_min.json
│  │  │     │  └─ conditions_min.json  (evitar dependencias externas)
│  │  │     └─ config/
│  │  │        ├─ settings.py
│  │  │        └─ logging.py
│  │  ├─ tests/
│  │  │  ├─ unit/
│  │  │  ├─ integration/
│  │  │  └─ contract/
│  │  └─ tools/
│  │     ├─ seed_synthetic_data.py
│  │     └─ generate_examples.py
│  └─ web/
│     ├─ package.json
│     ├─ tsconfig.json
│     ├─ vite.config.ts
│     ├─ src/
│     │  ├─ app/
│     │  ├─ pages/
│     │  │  ├─ PatientSearch.tsx
│     │  │  ├─ PatientSummary.tsx
│     │  │  └─ AuditLog.tsx
│     │  ├─ components/
│     │  ├─ api/
│     │  │  └─ client.ts
│     │  └─ charts/
│     └─ tests/
│        └─ (opcionales)
└─ .vscode/
   ├─ settings.json
   └─ extensions.json

