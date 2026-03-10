# AGENTS.md

Civitas is an apps-first Python/TypeScript monorepo for backend + web delivery.

## Product context

1. **Start with the project brief:** read `.planning/project-brief.md` before planning or implementing product features.
2. **Treat the brief as product source of truth:** if implementation/docs drift from the brief, update the brief or explicitly record the decision.

## Essential rules

1. **Read `docs/architecture.md`** before any non-trivial change. Follow layering and dependency rules.
2. **Read `docs/architecture/backend-conventions.md`** for backend model/contract/port/mapping conventions before implementing backend features.
3. **Read `docs/architecture/frontend-conventions.md`** for frontend layering, contract, and API-boundary conventions before implementing web features.
3b. **Read `docs/architecture/design-system.md`** before building any UI — it codifies the Loira Voss visual language, button variants, StatCard rules, trend indicator neutrality, mobile-first breakpoints, and anti-patterns. Every new page, feature, or data stat must follow these standards.
4. **Keep documentation in sync.** Update `docs/` when behavior changes and add new pages to `docs/index.md`.
5. **Run commands from repo root.** Use canonical commands in `.agents/tooling.md`.
6. **Use shared settings, not ad hoc env parsing.** Runtime code, CLI entrypoints, scripts, and test fixtures must read env-backed config through `civitas.infrastructure.config.settings`. Fix settings/bootstrap issues there; do not rely on shell-session exports or fixture-local dotenv parsing.
7. **Follow ownership + leaf-import rules.** Domain helpers go in `apps/backend/src/civitas/domain/shared/helpers`; application helpers go in `apps/backend/src/civitas/application/shared/utils`; avoid barrel re-exports.
8. **Enforce inward imports.** Domain has zero outward dependencies; infrastructure depends on application/domain ports; entrypoints (`api`, `cli`) stay thin and bootstrap handles composition.
9. **Contracts source of truth is backend OpenAPI.** Frontend consumes generated or typed clients derived from backend contracts.
10. **Use the golden path workflow.** Tests first, then implementation, then run `make lint` and `make test`.
11. **For auth/session foundation work, read `docs/runbooks/auth-development-provider.md` and `.agents/auth.md`.** Keep the development provider local/test-only and keep origin/cookie guardrails documented.
12. **For pipeline work, read `docs/runbooks/pipelines.md` and `.agents/pipelines.md`.** All runs must flow Bronze -> Silver -> Gold, starting from canonical `data/bronze` unless an explicitly documented exception is approved. Keep benchmark cache materialization (`metric_benchmarks_yearly`) on the post-promote/manual workflow, not on the web request path.
13. **For premium-access or billing workflow changes, read `docs/runbooks/local-development.md`, `docs/runbooks/premium-access-release.md`, and `.agents/documentation.md`.** Keep local entitlement-seeding guidance, Stripe test-mode rehearsal steps, and rollback notes current.

## Agent guides

| Topic | Guide |
|------|-------|
| Architecture | [.agents/architecture.md](.agents/architecture.md) |
| Design System | [docs/architecture/design-system.md](docs/architecture/design-system.md) |
| Workflow | [.agents/workflow.md](.agents/workflow.md) |
| Auth | [.agents/auth.md](.agents/auth.md) |
| Tooling | [.agents/tooling.md](.agents/tooling.md) |
| Testing | [.agents/testing.md](.agents/testing.md) |
| Repo structure | [.agents/repo-structure.md](.agents/repo-structure.md) |
| Documentation | [.agents/documentation.md](.agents/documentation.md) |
| Pipelines | [.agents/pipelines.md](.agents/pipelines.md) |

Use native planning workflows for large features/refactors.

