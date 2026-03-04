# Workflow Guide

## Planning

- For large features, write an explicit task list before coding.
- Keep tasks concrete and tied to file paths.

## Execution

- Work one task at a time unless phase parallelism is explicit.
- Run commands from repo root using `.agents/tooling.md`.
- Prefer direct changes over temporary compatibility shims.
- Follow the golden path: write/adjust tests first, implement, then run `make lint` and `make test`.

## Code hygiene

- Keep files ASCII-safe unless Unicode is required.
- Use leaf imports only.

## Documentation

- Update docs for behavior/config/API changes.
- Add new docs to `docs/index.md`.

## Pipelines

- Read `.agents/pipelines.md` and `docs/runbooks/pipelines.md` before pipeline changes.
- Use canonical Bronze root (`data/bronze`) for standard runs.
- Preserve mandatory Bronze -> Silver -> Gold flow for every source run.
