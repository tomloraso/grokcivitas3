# AGENTS.md

Fullstack Bootstrap Template is an apps-first Python/TypeScript monorepo baseline for backend + web delivery.

## Essential rules

1. **Read `docs/architecture.md`** before any non-trivial change. Follow layering and dependency rules.
2. **Keep documentation in sync.** Update `docs/` when behavior changes and add new pages to `docs/index.md`.
3. **Run commands from repo root.** Use canonical commands in `.agents/tooling.md`.
4. **Follow ownership + leaf-import rules.** Domain helpers go in `apps/backend/src/bootstrap_app/domain/shared/helpers`; application helpers go in `apps/backend/src/bootstrap_app/application/shared/utils`; avoid barrel re-exports.
5. **Enforce inward imports.** Domain has zero outward dependencies; adapters depend on application/domain ports; entrypoints (`api`, `cli`) stay thin.
6. **Contracts source of truth is backend OpenAPI.** Frontend consumes generated or typed clients derived from backend contracts.
7. **Use the golden path workflow.** Tests first, then implementation, then run `make lint` and `make test`.

## Agent guides

| Topic | Guide |
|------|-------|
| Architecture | [.agents/architecture.md](.agents/architecture.md) |
| Workflow | [.agents/workflow.md](.agents/workflow.md) |
| Tooling | [.agents/tooling.md](.agents/tooling.md) |
| Testing | [.agents/testing.md](.agents/testing.md) |
| Repo structure | [.agents/repo-structure.md](.agents/repo-structure.md) |
| Documentation | [.agents/documentation.md](.agents/documentation.md) |

Use native planning workflows for large features/refactors.
