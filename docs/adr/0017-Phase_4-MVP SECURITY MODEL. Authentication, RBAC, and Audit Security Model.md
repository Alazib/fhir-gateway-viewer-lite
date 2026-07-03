# ADR 0017 — MVP Authentication, RBAC, and Audit Security Model

## Status

Proposed

## Context

The project has completed its backend foundation phase.

The API now has:

* FastAPI application structure
* centralized settings
* logging baseline
* SQLAlchemy/Alembic persistence foundation
* ORM/domain mappers
* SQLAlchemy read adapters
* HTTP dependency wiring
* AuditEvent persistence schema
* API quality gate and CI baseline

The next architectural problem is security.

Before exposing persistence-backed clinical endpoints, the API needs a professional MVP security model that answers:

* who is making the request
* how the caller is authenticated
* what the caller is allowed to do
* how authorization is enforced
* how audit events identify the trusted actor
* how security failures are represented over HTTP

The project is a portfolio/demo healthcare backend and must only use synthetic data.

Even as an MVP, the security model must be credible, explicit, and compatible with later production-grade evolution.

However, the MVP should not implement unnecessary production identity infrastructure too early.

## Decision

For the MVP, the API will use an OAuth2-compatible Bearer token model based on signed JWTs.

The API will validate incoming Bearer tokens locally and derive a trusted current principal from validated claims.

The MVP will use role-based access control with a small explicit permission model.

The audit actor will always be derived from the trusted current principal.

Request bodies must not be allowed to define the audit actor or audit agent.

The MVP will not implement user registration, password login, refresh tokens, external identity provider integration, or database-backed user accounts.

These capabilities are deferred to post-MVP backlog items referenced at the end of this ADR.

## Authentication model

### MVP mechanism

The API will use:

```
Authorization: Bearer <token>
```

The token will be a signed JWT.

The API will validate:

* token signature
* expiration
* issuer
* audience
* subject
* roles claim

For the MVP, local/demo signed JWTs are acceptable if they are validated through a proper verifier and configured through centralized runtime settings.

This means the MVP does not simply accept arbitrary headers or mock users. It still uses a standard Bearer-token flow and validates token integrity.

### Token algorithm

For the MVP, symmetric signing is acceptable:

```
HS256
```

The signing secret must come from environment-backed settings.

The signing secret must not be hardcoded in source code.

A later production-grade version should migrate to asymmetric verification with JWKS.

### Required claims

The MVP JWT should include at least:

```
iss
aud
sub
exp
iat
roles
```

Recommended optional claims:

```
name
email
```

The `sub` claim is the stable technical identity of the caller.

The `roles` claim determines the caller's assigned roles.

Permissions are derived by the API from roles.

The token should not be trusted if required claims are missing or invalid.

## Current principal model

After successful authentication, the API will create a trusted current-principal object.

Conceptually, the principal contains:

```
subject
display_name
roles
```

The principal represents the authenticated caller.

It is not the same as a Patient.

It is not a database user entity in the MVP.

It is a trusted runtime identity derived from validated token claims.

The principal is the object that later authorization and audit logic will use.

## Role model

The MVP will use a deliberately small role model.

Initial roles:

```
clinician
auditor
admin
```

### clinician

A clinician can read ordinary clinical data exposed by the API.

Expected permissions:

```
patient:read
observation:read
condition:read
encounter:read
bundle:export
```

### auditor

An auditor can read audit events.

Expected permissions:

```
audit:read
```

An auditor should not automatically have clinical read permissions.

### admin

An admin can perform all MVP read operations.

Expected permissions:

```
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

Admin does not mean unrestricted production superuser behavior.

It only means full access within the current MVP feature set.

## Permission model

The MVP will use explicit permissions rather than checking role names directly inside routers.

Initial permissions:

```
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

Authorization should be expressed in terms of permissions.

For example:

```
require_permission("patient:read")
require_permission("audit:read")
```

This keeps routers thin and avoids scattering role logic across HTTP endpoint functions.

The role-to-permission mapping should be centralized and independently testable.

## Authorization behavior

Protected endpoints must require an authenticated principal.

If no token is provided, or the token is invalid, the API should respond with:

```
401 Unauthorized
```

If a valid principal is authenticated but lacks the required permission, the API should respond with:

```
403 Forbidden
```

The `/health` endpoint remains public.

Future clinical endpoints must not be public by default.

## Audit actor derivation

Audit events must identify the actor from trusted runtime context.

The audit actor must be derived from the current principal.

The audit actor must not be accepted from arbitrary request payloads.

For example:

```
current_principal.subject -> audit_event.agent
```

Optional display fields may be used for readability, but the stable audit identity must be based on the trusted subject.

This design prevents clients from spoofing audit actors by sending arbitrary agent values in request bodies.

## HTTP dependency model

The HTTP layer may provide dependencies such as:

```
get_current_principal()
require_permission(...)
get_current_audit_actor()
```

These dependencies may use FastAPI.

The domain and application layers must not depend on FastAPI.

Authorization logic should be implemented in a way that can be tested without running a real HTTP server.

Routers should receive already-resolved principals, permissions, or use-cases through dependencies.

Routers must not manually parse tokens.

Routers must not manually instantiate security infrastructure.

## Settings

Security configuration should be centralized through the existing settings system.

Potential MVP settings:

```
FHIR_GATEWAY_AUTH_JWT_SECRET
FHIR_GATEWAY_AUTH_JWT_ISSUER
FHIR_GATEWAY_AUTH_JWT_AUDIENCE
FHIR_GATEWAY_AUTH_JWT_ALGORITHM
```

The signing secret must not be committed to the repository.

Local development may use a documented demo secret through `.env`, but production secrets must come from a secure environment or future secrets management strategy.

## Error handling

Security failures must use consistent HTTP semantics:

```
401 Unauthorized
403 Forbidden
```

A full API error response envelope is still deferred unless Phase 4 explicitly introduces it.

If no shared error envelope exists yet, Phase 4 should still ensure consistent status codes and predictable error messages for security failures.

## MVP limitations

The MVP does not include:

* external OAuth/OIDC provider integration
* JWKS validation
* asymmetric signing
* key rotation
* refresh tokens
* token revocation
* database-backed user accounts
* password authentication
* user registration
* frontend login flow
* fine-grained patient-level authorization
* consent management
* break-glass access workflows
* production audit immutability controls

These are deliberately deferred because they would expand the MVP beyond its current goal.

The MVP goal is to establish a clean, testable, professional security foundation that can evolve later.

## Consequences

### Positive consequences

* The API uses standard HTTP Bearer authentication semantics.
* The model is compatible with later OAuth/OIDC integration.
* Role and permission logic is explicit.
* Routers can stay thin.
* Authorization can be tested independently.
* Audit events get their actor from trusted runtime context.
* The MVP avoids premature identity-provider complexity.
* Future clinical endpoints can be protected consistently.

### Negative consequences

* The MVP still does not provide production-grade identity management.
* Local/demo JWT handling requires careful documentation.
* There is no token revocation in the MVP.
* There is no database-backed user management in the MVP.
* There is no fine-grained patient-level access control in the MVP.

### Mitigations

* Document the MVP limitations clearly.
* Keep secrets out of source code.
* Keep the token verifier isolated behind clear interfaces.
* Add tests for invalid tokens, expired tokens, missing roles, and forbidden access.
* Track production-grade security improvements as backlog items.

## Post-MVP backlog references

The following improvements are intentionally deferred and should be tracked as separate backlog issues:

* BACKLOG / HARDEN — Integrate external OAuth2/OIDC provider with JWKS validation
* BACKLOG / HARDEN — Add token revocation and session management strategy
* BACKLOG / EXPAND — Add fine-grained patient-level authorization and consent rules
* BACKLOG / HARDEN — Add tamper-evident audit trail controls
* BACKLOG / ARCH — Introduce policy engine for complex authorization rules
* BACKLOG / AI-READY — Add security-aware audit context for future AI-assisted access

These backlog items are not part of the MVP security model.

They are referenced here to make the architectural trade-off explicit: the MVP security model is intentionally professional but deliberately scoped.
