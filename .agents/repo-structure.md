# Repository Structure

```text
civitas/
|- apps/
|  |- backend/
|  |  |- src/civitas/
|  |  |  |- domain/
|  |  |  |- application/
|  |  |  |- adapters/
|  |  |  |- contracts/
|  |  |  |- api/
|  |  |  `- cli/
|  |  `- tests/
|  `- web/
|- packages/
|  |- python/
|  `- ts/
|- docs/
|- agents/
|- .agents/
`- tools/
```

## Placement quick-reference

- Business logic: `apps/backend/src/civitas/domain/*`
- Use-cases + ports: `apps/backend/src/civitas/application/*`
- Adapter implementations: `apps/backend/src/civitas/adapters/*`
- DTO/schemas/contracts: `apps/backend/src/civitas/contracts/*`
- HTTP/CLI entrypoints only: `apps/backend/src/civitas/api`, `cli`

