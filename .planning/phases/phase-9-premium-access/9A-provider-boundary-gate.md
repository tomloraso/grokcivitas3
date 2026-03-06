# 9A - Provider Boundary Gate

## Goal

Freeze the external-provider and architectural boundary decisions before auth and payment implementation begins.

## Decisions Required

- authentication provider
- session model
- payment provider
- webhook signing and retry model
- unlock scope and duration

## Boundary Rules

- Domain and application layers must remain provider-agnostic.
- Infrastructure adapters own provider SDKs, tokens, and webhook payload mapping.
- API routes must not contain provider-specific business logic.
- Frontend must consume typed API endpoints rather than calling provider SDKs directly for protected data decisions.

## Output

This gate should produce:

- chosen auth provider and integration pattern
- chosen payment provider and checkout pattern
- explicit callback and webhook endpoints
- data boundary definition for free versus premium fields

## Acceptance Criteria

- Provider choices are documented with enough specificity for implementation.
- Security-sensitive flows, including session and webhook verification, are defined.
- Remaining phase documents can reference the chosen boundaries without ambiguity.
