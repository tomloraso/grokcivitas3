# ADR 0001: Hexagonal Apps-First Monorepo

## Status
Accepted

## Context
The Civitas codebase needs a production-ready full-stack structure with clear ownership and minimal architectural drift.

## Decision
Adopt an apps-first monorepo:

- `apps/backend` with domain/application/adapters/api/cli layering.
- `apps/web` for React frontend.
- `packages/*` reserved for optional shared modules.

Use backend OpenAPI as API contract source of truth.

## Consequences

- Easier onboarding through one structure and one tooling baseline.
- Strong testability from port-based design.
- Requires boundary enforcement in tests/CI to keep discipline.
