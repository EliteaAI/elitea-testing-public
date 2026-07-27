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
element needs its own testid, add a boolean/variant prop that drives which
testid string renders, rather than sharing one testid (or no testid)
across visually-similar-but-semantically-different elements.

**Update — same-element conditional pairs (canon ruling #277, 2026-07-22).**
The specific `isOverflow ? 'entity-card-tag-overflow' : 'entity-card-tag-chip'`
shape ELITEA-1740 shipped is NOT the preferred default going forward. When
your test only exercises one branch of the pair, the compliant shapes are:

1. **Preferred:** name only the used branch, leave the other `undefined`:
   `data-testid={isOverflow ? undefined : 'entity-card-tag-chip'}`. The used
   branch's locator is still collision-safe (the overflow render has no
   attribute to match), and no orphan testid inflates the presence-based
   coverage metric.
2. **Both branches named** — only if your caller's test asserts the untested
   branch's absence on the elements it exercises
   (`expect(card.locator(OVERFLOW)).to_have_count(0)`). This turns the
   disambiguation into a test-enforced invariant.

Documentation-only justification (docstring / AFS PROVENANCE row) is NOT
compliant on its own — docs don't execute. See `.agents/testing.md`
§ Locator policy and `.claude/skills/add-data-testid/SKILL.md` § Scope
discipline for the full ruling.

ELITEA-1740's shipped shape (both branches named, no absence assertion) is
grandfathered but should be cleaned up either by amending EliteaUI#544 to
`undefined` on the overflow branch, or by adding a one-line absence
assertion in `SkillsListPage.get_card_tags()`. Don't repeat the shape in
new cases.
