# 9C - Compare Selection State And Entry Points

## Goal

Let users build a compare set naturally from the existing search and profile experiences.

## Entry Points

- search result cards
- map popup or result actions where appropriate
- school profile header or summary actions

## State Rules

- Compare set supports between two and four schools.
- Duplicate schools cannot be added.
- Compare selection should survive route changes during the browsing session.
- URL state on the compare route should remain shareable.
- The compare route should remain usable when it contains zero or one valid URN by showing explicit empty or underfilled states.

## Frontend Ownership

- Selection state belongs in the web app layer, not in ad-hoc component local state.
- Add a dedicated compare selection provider in the app shell alongside the existing search context provider.
- Feature modules should consume typed compare helpers, not raw storage or query parsing.
- Persistence may start with local browser storage plus URL query params; account-backed persistence is deferred to Phase 10 or later.

## Canonical Route And Authority Rules

- The canonical compare route is `/compare?urns=<urn1>,<urn2>,...`.
- Query-string URN order is the authoritative column order for the compare page.
- Local browser storage is a convenience for persistence across route changes, but it must never override explicit URL order on the compare route.
- Adding or removing a school from the compare page must update the `urns` query parameter immediately.

## Selection Item Shape

Selection state should keep the minimum metadata needed to render compare affordances before the compare API responds:

- `urn`
- `name`
- `phase`
- `type`
- `postcode`
- optional `distance_miles`
- `source` of `search`, `profile`, or `compare`

The compare API remains responsible for the canonical compare header data used on the compare page itself.

## UX Requirements

- Users can see current compare count from both search and profile routes.
- Add and remove actions must be explicit and reversible.
- When a fifth school is attempted, the UI should explain the limit rather than silently replacing an existing selection.
- Compare CTA affordances should be disabled until at least two schools are selected.
- Removing a school on the compare page should keep the user on the compare route and fall back to the underfilled state when fewer than two schools remain.

## Navigation Context

- Search result cards may add `distance_miles` to selection state when the school was chosen from a postcode result.
- Profile routes opened from compare should receive lightweight `fromCompare` location state so the profile page can offer a "Back to compare" affordance without changing canonical profile URLs.

## Acceptance Criteria

- Compare entry points exist on search and profile routes.
- Selection state is stable across navigation.
- Compare route can reconstruct the compare set from URL state.
