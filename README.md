# Civitas

Civitas is a production-oriented full-stack monorepo for a UK public-data research platform.

Start with the product brief:
- `.planning/project-brief.md`

## Stack

- Backend: FastAPI + Python with layered architecture (`domain`, `application`, `infrastructure`, `api`, `cli`, `bootstrap`)
- Frontend: React + TypeScript
- Tooling: `uv`, npm, Makefile, pre-commit, Docker Compose
- Quality gates: lint, format, typecheck, unit/integration tests

## Repository layout

```text
apps/backend  # Python API + CLI service
apps/web      # Public-facing web app
docs          # Architecture, ADRs, runbooks
.planning     # Product/planning documents
.agents       # Agent execution guides
agents        # Prompt/eval scaffolding
tools         # Repo scripts
```

## Frontend component inventory

| Component | Path | Purpose |
|---|---|---|
| `StatCard` | `apps/web/src/components/ui/stat-card.tsx` | Canonical stat display primitive. Variants: `default`, `hero`, `mini`. Use `mini` when embedding inside another card. |
| `Card` / `Panel` | `apps/web/src/components/ui/Card.tsx` | Glass surface wrappers. |
| `MetricGrid` | `apps/web/src/components/data/MetricGrid.tsx` | Responsive grid container for `StatCard` collections. |
| `Sparkline` | `apps/web/src/components/data/Sparkline.tsx` | SVG trend line, always `width="100%"` with `preserveAspectRatio="none"`. |
| `TrendIndicator` | `apps/web/src/components/data/TrendIndicator.tsx` | Direction-only triangles ▲/▼ always teal. Never red, never conditional on good/bad. |

See `apps/web/README.md` for the full Loira Voss design system specification.

## Scaffold baseline

The repository currently includes a small `tasks` flow end-to-end as an architectural baseline.
It exists to validate wiring and quality gates and will be replaced by Civitas domain features.

## Quickstart

```bash
make setup
make lint
make test
make run
```

If `make` is unavailable (common on Windows shells), run the equivalent commands:

```bash
uv sync --project apps/backend --extra dev
cd apps/web && npm install
uv run --project apps/backend pytest
cd apps/web && npm run test
```

