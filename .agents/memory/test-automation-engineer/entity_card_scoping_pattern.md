---
name: Entity card scoping pattern (implementer)
description: entity-card / entity-card-tag-chip testids for scoping per-card queries on the shared Card.jsx component (skills/agents/pipelines); isOverflow prop distinguishes real tag chips from the "+N" badge
type: feedback
---

## Context (from ELITEA-1740 testid rework)

`EliteaUI/src/components/Card.jsx` is a shared component rendering skill /
agent / pipeline / toolkit cards alike. Before this rework, per-card scoped
queries (e.g. "get this specific card's tag chips") had no clean handle —
the only anchor was `entity-card-name` (the title), and code had to walk
up via an xpath `ancestor::div[...MuiCard-root...]` to reach the card
container, then fall back to a shared MUI CSS class
(`.MuiTypography-bodySmall`) to find sub-elements — which collided with
unrelated same-class elements (the "+N" tag-overflow badge, `Like.jsx`'s
like-count).

## The fix (now on `automation/testids`, EliteaUI PR #544)

- **`entity-card`** — testid on `Card.jsx`'s outer wrapper `Box`. Any
  future per-card scoped query should filter this locator by an inner
  locator via `.filter(has=...)`, e.g.:
  ```python
  card = self.skill_card.filter(has=self.skill_card_name.filter(has_text=...)).first
  ```
  This replaces xpath-ancestor entirely — `.filter(has=locator)` matches
  ancestors containing a descendant regardless of nesting depth, so it's
  more robust than a specific xpath ancestor chain.
- **`entity-card-tag-chip`** vs **`entity-card-tag-overflow`** —
  `CardTagSectionItem.jsx` takes a new `isOverflow` boolean prop; the "+N"
  badge render sites in `CardTagSection.jsx` pass `isOverflow`, the
  per-tag render site does not. This makes the tag-chip and overflow-badge
  DOM-distinguishable for the first time — no more shared-CSS-class
  ambiguity.

## Reusable pattern for future cases

Any test needing to scope a query to "this specific card" (agents list,
pipelines list, toolkit list — all render through the same `Card.jsx`)
should reach for `entity-card` + `.filter(has=...)` rather than inventing
another xpath-ancestor or CSS-class workaround. If a future card-adjacent
element needs its own testid, follow the `isOverflow`-prop pattern: add a
boolean/variant prop that drives which testid string renders, rather than
sharing one testid (or no testid) across visually-similar-but-semantically-
different elements.
