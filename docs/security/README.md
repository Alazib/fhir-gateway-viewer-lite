# Security Documentation

## 1. Purpose

This document explains the MVP security model for the `FHIR Gateway Viewer Lite` backend.

It documents how the project handles, or plans to handle during Phase 4:

* authentication
* JWT validation
* current-principal extraction
* role-based access control
* permission checks
* public vs protected endpoints
* audit actor derivation
* security error behavior
* security-related settings
* MVP limitations
* post-MVP security hardening

This document is living documentation.

The related ADR explains why the MVP security model was chosen.

This README explains how the current security model works, or is intended to work, from a maintainer/developer point of view.

Related ADR:

```text
docs/adr/0017-mvp-authentication-rbac-and-audit-security-model.md
```

---

## 2. Current status

Current security status: **Phase 4 / Security foundation in progress**

The following security-related work is already defined:

* MVP security model ADR
* standard API error response envelope
* error mapping foundation for validation, not-found, and internal errors
* planned Bearer-token-based authentication model
* planned JWT-based current-principal extraction
* planned RBAC permission model
* planned trusted audit actor derivation

The following security capabilities are not implemented yet:

* JWT verification
* authentication HTTP dependency
* current-principal dependency
* RBAC authorization helpers
* protected clinical endpoints
* protected audit endpoints
* audit write-side pipeline
* external OAuth/OIDC integration
* JWKS validation
* token revocation
* session management
* database-backed users
* patient-level consent/access control

Current public endpoint:

```text
GET /health
```

Clinical and audit endpoints are not currently exposed.

Future clinical and audit endpoints should not be treated as public by default.

---

## 3. Security model overview

## 3.1. High-level flow

The intended MVP request flow is:

```text
HTTP request
    -> Authorization: Bearer <token>
        -> JWT validation
            -> CurrentPrincipal
                -> role-to-permission mapping
                    -> permission check
                        -> protected use-case
                            -> audit actor derived from principal
```

## 3.2. Main concepts

The main concepts are:

| Concept          | Meaning                                                        |
| ---------------- | -------------------------------------------------------------- |
| Bearer token     | Credential sent by the client in the `Authorization` header    |
| JWT              | Signed token containing trusted claims after validation        |
| CurrentPrincipal | Trusted runtime identity derived from a validated token        |
| Role             | Coarse-grained user category, such as `clinician` or `auditor` |
| Permission       | Fine-grained operation capability, such as `patient:read`      |
| Audit actor      | Trusted actor written to audit records                         |

## 3.3. Boundary rule

Security translation to HTTP belongs to the HTTP/interface layer.

Domain and application layers must remain independent from FastAPI.

Domain and application layers must not directly return HTTP responses, status codes, or FastAPI exceptions.

---

## 4. Authentication

## 4.1. Bearer token model

Protected endpoints will use the HTTP `Authorization` header:

```text
Authorization: Bearer <token>
```

The token represents the caller's credentials.

Example:

```text
GET /patients/pat-001/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## 4.2. JWT-based MVP authentication

The MVP authentication model uses signed JWTs.

A JWT acts as a signed digital credential.

The API validates the token before trusting any claims inside it.

The API must not trust a token only because it contains fields such as:

```json
{
  "sub": "admin-001",
  "roles": ["admin"]
}
```

The token must first pass validation.

## 4.3. Authentication result

A successful authentication process produces a trusted `CurrentPrincipal`.

An unsuccessful authentication process returns:

```text
401 Unauthorized
```

using the standard API error response envelope.

---

## 5. JWT requirements

## 5.1. Required claims

The MVP JWT must include:

| Claim   | Meaning                                    |
| ------- | ------------------------------------------ |
| `iss`   | Issuer: who issued the token               |
| `aud`   | Audience: which API the token is meant for |
| `sub`   | Subject: stable identity of the caller     |
| `exp`   | Expiration time                            |
| `iat`   | Issued-at time                             |
| `roles` | Roles assigned to the caller               |

## 5.2. Optional claims

Optional claims may include:

| Claim   | Meaning                     |
| ------- | --------------------------- |
| `name`  | Human-readable display name |
| `email` | Email address               |

Optional claims must not be required for authorization decisions.

Authorization must rely on validated identity and roles/permissions.

## 5.3. MVP signing strategy

The MVP uses symmetric JWT signing.

Initial algorithm:

```text
HS256
```

The signing secret must come from environment-backed settings.

The signing secret must not be hardcoded in source code.

## 5.4. Post-MVP signing strategy

A production-oriented implementation should move toward external OAuth2/OIDC provider integration with asymmetric signing and JWKS validation.

That is intentionally deferred to post-MVP backlog work.

---

## 6. Current principal

## 6.1. Definition

`CurrentPrincipal` is the trusted runtime identity of the caller after successful authentication.

Conceptual fields:

```text
subject
display_name
roles
```

Example:

```text
CurrentPrincipal(
    subject="clinician-001",
    display_name="Demo Clinician",
    roles=("clinician",),
)
```

## 6.2. Principal vs Patient

A principal is not a patient.

A principal is the actor using the system.

A patient is the clinical subject whose data may be read.

Example:

```text
Principal: clinician-001
Patient: pat-001
```

The clinician may read the patient's data if authorization allows it.

The two concepts must remain separate.

## 6.3. Principal vs database user

The MVP does not introduce database-backed users.

The principal is derived from a validated token.

Database-backed users, user registration, password login, and user lifecycle management are deferred.

---

## 7. Roles

## 7.1. Role list

The MVP defines these initial roles:

```text
clinician
auditor
admin
```

## 7.2. `clinician`

A `clinician` represents a clinical user allowed to read ordinary clinical data in the MVP.

Expected permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
```

## 7.3. `auditor`

An `auditor` represents a user allowed to inspect audit events.

Expected permissions:

```text
audit:read
```

An auditor does not automatically receive clinical read permissions.

## 7.4. `admin`

An `admin` represents a broad MVP administrator.

Expected permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

In this MVP, `admin` means full read access to the defined MVP operations.

It does not represent unrestricted production superuser behavior.

---

## 8. Permissions

## 8.1. Permission list

Initial MVP permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

## 8.2. Role-to-permission mapping

Initial mapping:

| Role        | Permissions                                                                                           |
| ----------- | ----------------------------------------------------------------------------------------------------- |
| `clinician` | `patient:read`, `observation:read`, `condition:read`, `encounter:read`, `bundle:export`               |
| `auditor`   | `audit:read`                                                                                          |
| `admin`     | `patient:read`, `observation:read`, `condition:read`, `encounter:read`, `bundle:export`, `audit:read` |

## 8.3. Permission checks

Endpoints should require permissions, not raw roles.

Preferred model:

```text
endpoint requires permission
principal has roles
roles map to permissions
permission check decides access
```

Example:

```text
GET /patients/{patient_id}/summary
    -> requires patient:read
```

A router should not scatter checks such as:

```text
if "clinician" in principal.roles
```

Instead, it should rely on centralized authorization helpers.

---

## 9. Authorization flow

## 9.1. Authentication vs authorization

Authentication answers:

```text
Who are you?
```

Authorization answers:

```text
Are you allowed to do this?
```

## 9.2. `401 Unauthorized`

Use `401 Unauthorized` when the API cannot establish a valid identity.

Examples:

* missing token
* malformed token
* invalid signature
* expired token
* wrong issuer
* wrong audience
* missing required claims

Meaning:

```text
The caller has not provided valid credentials.
```

## 9.3. `403 Forbidden`

Use `403 Forbidden` when the API knows who the caller is but the caller lacks permission.

Example:

```text
auditor-001 tries to read GET /patients/pat-001/summary
```

If the endpoint requires:

```text
patient:read
```

but the principal only has:

```text
audit:read
```

then the API should return:

```text
403 Forbidden
```

## 9.4. Simple rule

```text
401 = no valid identity
403 = valid identity, insufficient permission
```

---

## 10. Public vs protected endpoints

## 10.1. Public endpoints

Current public endpoint:

```text
GET /health
```

The health endpoint is technical.

It does not expose clinical data, audit data, or application use-cases.

## 10.2. Protected clinical endpoints

Future clinical endpoints should require authentication and authorization by default.

Planned clinical endpoint groups include:

```text
GET /patients
GET /patients/{patient_id}/summary
GET /patients/{patient_id}/observations
GET /patients/{patient_id}/bundle
```

These endpoints should not be public by default.

## 10.3. Protected audit endpoints

Future audit endpoints should require authentication and authorization.

Planned audit endpoint group:

```text
GET /audit-events
```

Expected permission:

```text
audit:read
```

---

## 11. Audit actor derivation

## 11.1. Trusted actor source

Future audit event creation must derive the audit actor from trusted runtime context.

Preferred source:

```text
CurrentPrincipal.subject
```

Example:

```text
CurrentPrincipal.subject = "clinician-001"
AuditEvent.agent = "clinician-001"
```

## 11.2. Request body must not define audit actor

Request bodies must not be allowed to define the audit actor.

Bad model:

```json
{
  "action": "read",
  "agent": "admin-001"
}
```

The client could lie.

Correct model:

```text
validated token
    -> CurrentPrincipal
        -> AuditEvent.agent
```

## 11.3. Future actor sources

Future non-human actors may include:

* system identity
* background job identity
* local/demo identity
* AI-assisted workflow identity

Those must still be trusted runtime identities, not arbitrary request body values.

---

## 12. Security error behavior

## 12.1. Standard API error envelope

Security errors must use the standard API error response envelope:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "field": null,
    "resource": null,
    "identifier": null
  }
}
```

The API error envelope is defined in the HTTP/interface layer.

## 12.2. Authentication error example

Status:

```text
401 Unauthorized
```

Body:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Authentication credentials were missing or invalid.",
    "field": null,
    "resource": null,
    "identifier": null
  }
}
```

## 12.3. Authorization error example

Status:

```text
403 Forbidden
```

Body:

```json
{
  "error": {
    "code": "forbidden",
    "message": "The authenticated principal does not have permission to perform this operation.",
    "field": null,
    "resource": null,
    "identifier": null
  }
}
```

## 12.4. Application and domain error relationship

The same API error envelope is also used for application/domain errors exposed through HTTP.

Examples:

```text
DomainValidationError      -> 400 Bad Request
ApplicationValidationError -> 400 Bad Request
ApplicationNotFoundError   -> 404 Not Found
Unexpected exception       -> 500 Internal Server Error
```

---

## 13. Settings

## 13.1. Planned security settings

Planned Phase 4 security settings:

| Setting              | Environment variable              | Purpose                      |
| -------------------- | --------------------------------- | ---------------------------- |
| `auth_jwt_secret`    | `FHIR_GATEWAY_AUTH_JWT_SECRET`    | Local/MVP JWT signing secret |
| `auth_jwt_issuer`    | `FHIR_GATEWAY_AUTH_JWT_ISSUER`    | Expected token issuer        |
| `auth_jwt_audience`  | `FHIR_GATEWAY_AUTH_JWT_AUDIENCE`  | Expected token audience      |
| `auth_jwt_algorithm` | `FHIR_GATEWAY_AUTH_JWT_ALGORITHM` | Expected JWT algorithm       |

Exact names may be adjusted during implementation if needed.

## 13.2. Secret handling rule

Secrets must not be committed to the repository.

The local/demo signing secret should be provided through environment-backed settings.

Production secrets should eventually come from a proper secrets management strategy.

## 13.3. Current status

These security settings are planned for Phase 4.

They are not all implemented yet.

---

## 14. Testing strategy

## 14.1. Authentication tests

Future authentication tests should cover:

* missing token
* malformed token
* invalid signature
* expired token
* wrong issuer
* wrong audience
* missing required claims
* valid token

Expected behavior:

```text
missing/invalid token -> 401 unauthorized
valid token           -> CurrentPrincipal
```

## 14.2. Authorization tests

Future authorization tests should cover:

* principal has required permission
* principal lacks required permission
* unknown role
* multiple roles
* admin permissions

Expected behavior:

```text
missing permission -> 403 forbidden
allowed permission -> request continues
```

## 14.3. Audit actor tests

Future audit actor tests should cover:

* audit actor comes from `CurrentPrincipal.subject`
* request body cannot override audit actor
* audit actor derivation is stable and explicit

## 14.4. Error envelope tests

Security errors should reuse the standard API error envelope.

Expected tests:

```text
401 -> {"error": {...}}
403 -> {"error": {...}}
```

---

## 15. MVP limitations

The MVP security model deliberately does not implement:

* external OAuth/OIDC provider integration
* JWKS validation
* asymmetric signing
* key rotation
* refresh tokens
* token revocation
* session management
* user registration
* password login
* database-backed users
* fine-grained patient-level authorization
* consent rules
* break-glass access
* production-grade audit immutability
* real patient data
* frontend authentication flow

These limitations are intentional.

The MVP goal is to create a clean, testable, extensible security foundation without over-building production identity infrastructure too early.

---

## 16. Post-MVP backlog references

Deferred security hardening and expansion items include:

```text
BACKLOG / POST-MVP / HARDEN / Integrate external OAuth2/OIDC provider with JWKS validation
```

```text
BACKLOG / POST-MVP / HARDEN / Add token revocation and session management strategy
```

```text
BACKLOG / I2+ / EXPAND / Add fine-grained patient-level authorization and consent rules
```

```text
BACKLOG / POST-MVP / HARDEN / Add tamper-evident audit trail controls
```

```text
BACKLOG / I2+ / ARCH / Introduce policy engine for complex authorization rules
```

```text
BACKLOG / FUTURE-AI / AI-READY / Add security-aware audit context for future AI-assisted access
```

---

## 17. Related ADRs

Security model:

```text
docs/adr/0017-mvp-authentication-rbac-and-audit-security-model.md
```

AuditEvent persistence strategy:

```text
docs/adr/0015-audit-event-persistence-strategy.md
```

HTTP API structure and runtime composition:

```text
docs/adr/0011-http-api-structure-and-runtime-composition.md
```

Centralized runtime configuration:

```text
docs/adr/0013-centralized-runtime-configuration.md
```

---

## 18. Summary

The MVP security model is intentionally simple:

```text
Bearer token
    -> validated JWT
        -> CurrentPrincipal
            -> roles
                -> permissions
                    -> protected endpoint
                        -> trusted audit actor
```

The key rule is:

```text
Security decisions must be explicit, centralized, testable, and documented.
```

The current project is still in Phase 4 security foundation work.

Security features must not be documented as production-grade until the corresponding hardening backlog items are implemented.
