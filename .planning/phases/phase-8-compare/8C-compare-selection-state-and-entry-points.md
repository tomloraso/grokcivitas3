# 8C - Compare Selection State And Entry Points

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

## Frontend Ownership

- Selection state belongs in the web app layer, not in ad-hoc component local state.
- Feature modules should consume typed compare helpers, not raw storage or query parsing.
- Persistence may start with local browser storage plus URL query params; account-backed persistence is deferred to Phase 9 or later.

## UX Requirements

- Users can see current compare count from both search and profile routes.
- Add and remove actions must be explicit and reversible.
- When a fifth school is attempted, the UI should explain the limit rather than silently replacing an existing selection.

## Acceptance Criteria

- Compare entry points exist on search and profile routes.
- Selection state is stable across navigation.
- Compare route can reconstruct the compare set from URL state.
