# Repository Structure

```text
civitas/
|- apps/
|  |- backend/
|  |  |- src/civitas/
|  |  |  |- domain/
|  |  |  |- application/
|  |  |  |- infrastructure/
|  |  |  |- api/
|  |  |  |- cli/
|  |  |  `- bootstrap/
|  |  `- tests/
|  `- web/
|- packages/
|  |- python/
|  `- ts/
|- docs/
|- .agents/
|- data/
`- tools/
```

## Placement quick-reference

- Business logic: `apps/backend/src/civitas/domain/*`
- Use-cases + ports: `apps/backend/src/civitas/application/*`
- Infrastructure implementations: `apps/backend/src/civitas/infrastructure/*`
- HTTP/CLI entrypoints only: `apps/backend/src/civitas/api`, `cli`
- Dependency composition only: `apps/backend/src/civitas/bootstrap/*`
- Canonical Bronze root for pipelines: `data/bronze`

