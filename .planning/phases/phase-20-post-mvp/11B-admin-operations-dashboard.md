# 10B - Admin Operations Dashboard

## Goal

Provide an internal operations surface for data-refresh status, row counts, freshness, and failure visibility.

## Scope

- pipeline run history
- source freshness and drift visibility
- high-level quality and rejection counts
- operator links to runbooks or retry actions where appropriate

## Guardrails

- Admin tooling should consume existing operational data rather than inventing shadow status systems.
- Sensitive controls should remain authenticated and access-controlled.

## Acceptance Criteria

- Operators can see the health of the active source set in one place.
- Dashboard scope is clear and does not sprawl into generic internal tooling.
