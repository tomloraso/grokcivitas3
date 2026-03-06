# 9E - Premium API And Web Paywall

## Goal

Wire premium entitlements into the product surface by enforcing backend data boundaries and adding a clear paywall experience in the web app.

## Backend Scope

- protect premium-only profile, compare, or postcode-level data paths
- return only the allowed free subset when no entitlement exists
- expose entitlement state and paywall-relevant metadata through typed API responses

## Frontend Scope

- sign-in and upgrade entry points
- premium preview or locked-state rendering
- post-purchase refresh flow that unlocks newly available data

## Guardrails

- Premium enforcement must happen server-side.
- Free and paid states must remain understandable to the user.
- Paywall copy should explain what unlocks without overstating unsupported metrics.

## Acceptance Criteria

- Free users cannot access protected data through API or UI loopholes.
- Paid users receive the unlocked data set immediately after reconciliation.
- Compare and profile surfaces render a consistent paywall model where relevant.
