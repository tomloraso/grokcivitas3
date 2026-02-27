# Architecture Principles

## 1) Imports point inward

- Domain: pure business logic, no infrastructure imports.
- Application: orchestrates use-cases via ports.
- Infrastructure: implements ports and performs IO.
- API/CLI: thin entrypoints only.
- Bootstrap: owns composition and concrete wiring.

## 2) Single source of truth for contracts

Backend OpenAPI is the canonical API contract. Frontend consumes generated/typed clients from backend schema.

## 3) Explicit ownership

- Domain helpers: `domain/shared/helpers`
- Application helpers: `application/shared/utils`
- Avoid global catch-all utility packages.

## 4) Test-first guardrails

Boundary tests and CI checks block architecture drift.

## 5) Golden path by example

The repository includes one small scaffold feature implemented end-to-end across domain, application, infrastructure, API, and web.
