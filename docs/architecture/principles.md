# Architecture Principles

## 1) Imports point inward

- Domain: pure business logic, no infrastructure imports.
- Application: orchestrates use-cases via ports.
- Infrastructure: implements ports and performs IO.
- API/CLI: thin entrypoints only.
- Bootstrap: owns composition and concrete wiring.

## 2) Single source of truth for contracts

Backend OpenAPI is the canonical API contract. Frontend consumes generated/typed clients from backend schema.

## 3) Frontend is contract-driven

- Frontend network IO stays in `apps/web/src/api/*`.
- Frontend wire types are derived from backend OpenAPI contracts.
- UI layers consume typed API clients instead of direct transport concerns.

## 4) Explicit ownership

- Domain helpers: `domain/shared/helpers`
- Application helpers: `application/shared/utils`
- Avoid global catch-all utility packages.

## 5) Test-first guardrails

Boundary tests and CI checks block architecture drift.

## 6) Golden path by example

The repository includes one small scaffold feature implemented end-to-end across domain, application, infrastructure, API, and web.
