---
name: An absence assertion guarded only by ordering is one refactor from vacuous
description: Make the "something actually rendered" guard explicit next to the absence, don't rely on an earlier positive on the same snapshot
type: feedback
aliases: [vacuous absence assertion, empty-state guard, absence assertion ordering]
tags: [area/review, type/assertion-design]
created: 2026-09-10
updated: 2026-09-10
---

## The pattern

```python
names = page.get_card_names()          # returns [] on timeout
assert wanted in names                 # positive — fails on an empty grid
assert unwanted not in names           # absence — vacuous on an empty grid
```

The absence IS guarded — but only because the positive reads the same snapshot and
raises first. Nothing in the absence line says so. Reorder the two, split them
across steps, or re-read the DOM between them, and the guard silently disappears.

## Do this

Put the discriminating guard **between** them, explicitly:

```python
assert wanted in names
assert list_page.empty_state_title.count() == 0   # NOT the empty state
assert unwanted not in names
```

It is redundant by construction and worth it twice over: it survives refactoring,
and it makes the failure message name the real failure ("dashboard is showing the
empty state") instead of a missing item.

⚠️ Ordering still matters the other way: during a list's loading window BOTH the
content testid and the empty-state testid read `0`, so the guard must come AFTER a
**waiting** positive assertion, never first.

Origin: ELITEA-2023 repair (`#2119`), generalising the `#2118` /
`CardList.jsx showEmptyOrError` finding.

Related: [[a_search_that_matches_description_breaks_the_only_matching_universal]]
