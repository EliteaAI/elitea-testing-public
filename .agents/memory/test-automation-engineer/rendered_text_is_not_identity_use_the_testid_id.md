---
name: A card's rendered text is not its identity — read the id out of its testid
description: Whole-card text_content() concatenates volatile siblings (like counts, author initials); compare by the dynamic testid's id, as a sorted multiset
type: feedback
aliases: [card identity, text_content identity, like count in card text, multiset compare, catalog-agent-card, ELITEA-2363]
tags: [area/ui, type/flake]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

A before/after comparison of a card grid that keys on each card's `text_content()` is keyed on
**everything rendered inside that card element**, not on the thing you meant. EliteaUI's
`AgentCard.jsx` puts the name `Typography`, the author-initials avatar and `AgentHubLike`'s live
like counter inside ONE `<Card>` with no separator, so the "name" reads `"Business Analyst9"`.
ELITEA-2363 went RED in CI (run 34436416962) when a sibling spec in the same suite liked an agent
mid-run: one string changed `...TB0` -> `...TB1`, and the likes-desc Trending section legitimately
re-ranked. Neither delta was the case's observable.

The helper was even called `get_visible_agent_card_names()` and its docstring called the like digit
*"harmless … since no like state changes during this case"* — a premise a read-only spec has no way
to guarantee on shared data.

## The shape that works

Identity comes from the card's own dynamic testid (`catalog-agent-card-{id}`): read
`get_attribute("data-testid")` and strip a class-level stem constant. Then:

- **Compare `sorted(a) == sorted(b)`, never `set(a) == set(b)`.** The same agent can render twice
  (Trending + its own category): 27 cards, 24 distinct ids. A set collapses that and stops
  detecting a dropped duplicate.
- **Wait on identity, not on a count.** Two auto-retrying Playwright assertions express it with no
  poll loop and no sleep: a comma-joined CSS union of the baseline's distinct ids asserted
  `to_have_count(len(baseline))` (a half-restored grid can't satisfy it, and it can't resolve on a
  transient pass-through of the old number), plus the prefix locator at the same count (catches an
  EXTRA card whose id is outside the set, which the union structurally cannot see).
- Keep a *separate* text helper for substring checks, and say in its docstring that it is not
  identity.

Related: [[a_settle_can_be_fragile_and_vacuous_at_once]]
