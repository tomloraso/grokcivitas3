# Web

React + TypeScript frontend for Civitas, consuming backend API contracts.

## Commands

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm run test
npm run build
npm run generate:types
```

## Contract typing

- Backend OpenAPI is the contract source of truth.
- Generated types live in `src/api/generated-types.ts`.
- Frontend should consume aliases from `src/api/types.ts`.
