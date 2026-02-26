# Repository Structure

```text
strategic-bootstrap-template/
|- apps/
|  |- backend/
|  |  |- src/bootstrap_app/
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

- Business logic: `apps/backend/src/bootstrap_app/domain/*`
- Use-cases + ports: `apps/backend/src/bootstrap_app/application/*`
- Adapter implementations: `apps/backend/src/bootstrap_app/adapters/*`
- DTO/schemas/contracts: `apps/backend/src/bootstrap_app/contracts/*`
- HTTP/CLI entrypoints only: `apps/backend/src/bootstrap_app/api`, `cli`
