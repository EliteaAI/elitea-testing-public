---
name: An absence assertion is vacuous when the list it reads is empty — establish the precondition
description: "\"Zero card elements ⇒ table view rendered\" is also true when NOTHING rendered. Establish the ≥1-entity precondition in the test, never inherit the ambient project's data."
type: feedback
aliases: [vacuous absence, empty list assertion, missing precondition, entity-card-name count 0, empty state short-circuit, green locally red in CI]
tags: [area/analysis, type/gotcha]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

A layout/branch assertion of the shape *"component X does not render ⇒ the other
branch must be mounted"* silently admits a **third** branch: nothing rendered at all,
because the list was empty.

Worked example — Elitea's `CardList.jsx:40-44`:

```js
const showEmptyOrError = !rest.isLoading && (isError || isEmptyList);
const showTable = !showEmptyOrError && shouldRenderTable;
const showCards = !showEmptyOrError && !shouldRenderTable;
```

`showEmptyOrError` short-circuits **both** view branches. So `entity_card_name.count() == 0`
in table view is satisfied by a real table AND by the "No pipelines yet" empty state.
On the DEV CI matrix project (which holds no pipelines of its own) the test's Step 5
passed in 0.00 s having proven nothing, and Step 7 — the *positive* half — is what
finally went red, naming the wrong subsystem.

## Why it survives every gate

The suite runs against a shared dev project that happens to hold data (14 pipelines on
project 399). The assumption "the dashboard has content" is invisible, ambient, and
true everywhere the author looked. **Green locally + red in CI is the tell**
(`adjust-automated-test` class D), not drift and not a product bug.

## The two moves

1. **Establish the precondition in the test.** If the case says *"the dashboard contains
   at least one X"*, the test creates one (API fixture = transit substitution, declared)
   and asserts it is visible **before** exercising anything. That assertion also waits out
   the loading window — during load *both* the content testid and the empty-state testid
   read 0, so a bare count is vacuous there too.
2. **Pair every absence with a "something rendered" guard.** On Elitea that is
   `empty-state-title` (`EmptyStatePage.jsx:49`, generic + shared, on-main):
   `empty_state_title.count() == 0` next to the content-absence check. Page-wide count is
   0 on any populated list page, so it is unambiguous.

Origin: `[FIX][ELITEA-2024]` / board `#2118`, CI run 34331579791, triaged 2026-09-09.

Related: [[absence_assertion_needs_a_proven_detector]] ·
[[absence_assertion_can_pass_before_the_thing_could_appear]]
