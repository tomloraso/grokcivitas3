# Architecture

This template uses an apps-first monorepo with a hexagonal backend and React web app.

- `apps/backend`: Python API and CLI with domain/application/adapters boundaries.
- `apps/web`: React frontend consuming backend contracts.
- `packages`: optional shared libraries for Python/TypeScript.

Read these pages before changing structure:

- `docs/architecture/principles.md`
- `docs/architecture/boundaries.md`
- `docs/architecture/testing-strategy.md`
