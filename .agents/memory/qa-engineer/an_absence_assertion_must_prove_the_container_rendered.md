---
name: An absence assertion must prove the container rendered
description: to_have_count(0) passes vacuously against a skeleton/unmounted list — require the container to have RENDERED between the two absence checks.
type: feedback
aliases: [vacuous absence, to_have_count(0) trap, skeleton grid, deleted card still listed, empty state or first card]
tags: [area/review, type/assertion-strength]
created: 2026-09-10
updated: 2026-09-10
---

## The two ways an absence check lies

1. **Vacuous pass.** A mid-refetch grid renders skeletons and **zero**
   `entity-card-name` nodes, so `expect(card).to_have_count(0)` passes against a list
   that has not rendered at all. (Positive-direction twin: ELITEA-2024 / board #2118.)
2. **Page-wide text match.** `pipeline_exists_in_list()`-style
   `page.locator('text="<name>"')` cannot separate "gone from the list" from "named in
   the success toast" — Elitea's delete toast reads *"The `<name>` pipeline has been
   successfully deleted."* and is still on screen. Scope absence to the LIST handle.

Third, related: a *sampled* helper (`…_exists_in_list()` returns bool, waits only for
APPEARANCE) cannot express "becomes absent". After an in-app delete the dashboard
history-backs and repaints its **cached** list — deleted card still on it — dropping it
only when the refetch lands. A manual `list_page.navigate()` used to hide this by
forcing goto + networkidle; removing that navigation exposes it.

## The shape that holds

```python
card = self.entity_card_name.filter(has_text=name)
expect(card).to_have_count(0, timeout=t)                                   # wait it OUT
expect(self.entity_card_name.first.or_(self.empty_state_title)).to_be_visible(timeout=t)
expect(card).to_have_count(0, timeout=t)                                   # re-assert
```

`PipelinesListPage.wait_for_pipeline_absent()` (PR #2161) is the reference
implementation. The middle assertion is the whole point: it converts "nothing matched"
into "the container rendered and nothing matched". `.or_()` keeps it a single strict
match whether the list has content or is legitimately empty.

**Review rule:** any `to_have_count(0)` / `not_to_be_visible()` on a list item is
`CHANGES_REQUESTED`-worthy unless something in the same step proves the container
rendered — and the prior positive step (e.g. clicking that same card) counts as proof
that the item is renderable in the default grid.
