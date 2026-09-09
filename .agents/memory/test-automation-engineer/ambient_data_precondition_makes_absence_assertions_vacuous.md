---
name: A list test that inherits the ambient project's data has a vacuous absence assertion and an environment-dependent verdict
description: Establish the >=1-entity precondition with a fixture and pair every "zero items" assertion with an empty-state absence guard
type: feedback
aliases: [empty list vacuous assertion, ambient project data, dashboard precondition, green locally red in CI, empty-state-title, showEmptyOrError]
tags: [area/ui-tests, type/assertion-quality]
created: 2026-09-09
updated: 2026-09-09
---

## The failure shape

A list/dashboard test that reads "whatever entities happen to exist" fails in two
ways at once, and only one of them is visible:

1. **The visible half** — it is green on a populated project and red on an empty
   one, with the product identical on both. Localhost dev projects are populated;
   CI matrix projects often hold nothing of their own.
2. **The invisible half, which is worse** — any `count() == 0` assertion in that
   test is ALSO satisfied by the empty state, so it passes *while proving nothing*.

Elitea's `CardList.jsx` is the canonical mechanism:

```js
const showEmptyOrError = !rest.isLoading && (isError || isEmptyList);
const showTable = !showEmptyOrError && shouldRenderTable;
const showCards = !showEmptyOrError && !shouldRenderTable;
```

The empty branch short-circuits **both** layout branches. So on an empty list,
*table view renders no table at all* — and "zero card elements while in table view"
is true for entirely the wrong reason. Caught on ELITEA-2024 / `#2118` (CI run
34331579791): Step 7 failed loudly on `assert []`, while Step 5 had been passing
vacuously in 0.00 s for weeks.

## The rule

- **Establish the precondition, never inherit it.** If the case says "the dashboard
  contains at least one X", the test creates one (a `*_id` API fixture) and asserts
  it is rendered **before** exercising anything. A waiting *positive* assertion, at
  the first step — so this failure class reports where the cause is, not three steps
  later at whatever read the empty list.
- **Pair every absence assertion with a presence guard** that distinguishes "the
  thing I expect really mounted" from "nothing mounted". Here: `empty-state-title`
  (generic shared `EmptyStatePage` testid, present on the Toolkits/MCP/Pipelines
  list pages) reads 0 on a populated list in *either* view, 1 on an empty one.
- **Timing trap:** during the list's load window BOTH the item testid and the
  empty-state testid read 0. A bare count assertion right after `navigate()` is
  vacuous there too. Lead with the waiting positive assertion, and give it the real
  timeout (10 s) — a helper's 5 s default is exactly the kind of thing that expires
  in CI and not locally.

## Proving the guard is not vacuous, without destroying data

Reach the empty-list state with a **no-match search filter**. It is free, fully
reversible, and mutates nothing — never delete real entities to manufacture an
empty state. Then run the assertion and watch it raise. A guard nobody has seen
fail is unverified.

Related: [[list_swap_transient_empty_state]] · [[absence_guards_must_watch_the_real_mechanism]]
