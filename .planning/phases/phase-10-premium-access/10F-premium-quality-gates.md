# 10F - Premium Quality Gates

## Goal

Close Phase 10 with evidence that auth, entitlements, and payment enforcement work together safely.

## Required Checks

- backend tests for auth, entitlement, and payment flows
- contract export and frontend type generation
- frontend lint, typecheck, tests, and build
- end-to-end coverage for sign-in, locked state, checkout, and post-purchase unlock
- repository `make lint`
- repository `make test`

## Acceptance Evidence

- premium-only data is blocked without entitlement
- unlock state is granted and revoked correctly
- checkout and webhook flows are idempotent
- web UI reflects the real backend entitlement state

## Sign-Off Condition

Phase 10 is complete only when staging-validated auth and payment flows align with passing repository quality gates.
