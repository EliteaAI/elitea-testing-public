---
name: Hardcoded count drift is rarely fixed by bumping the number
description: A count-mismatch FIX card usually means the assertion pinned frontend constants and backend data together; derive the expectation from the product's own response instead
type: feedback
aliases: [count mismatch, expected 11 found 12, chip count, hardcoded count, filter rail drift, exact-count assertion]
tags: [area/test-automation, type/triage-rule]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`[FIX]` cards from the CI intake pipeline arrive phrased as an arithmetic problem —
*"expected 11 filter chips, found 12"*. The obvious repair is `11 -> 12`. **That is
almost always wrong**, and it is wrong in a way that passes every gate: the bumped
test goes green, merges, and re-breaks on the next data change.

## The question to ask instead

**Does the asserted set mix things that change for unrelated reasons?**

Worked case (ELITEA-2367, card #2079, 2026-09-09) — the Catalog filter rail:

| Source | Members | Changes when |
|---|---|---|
| frontend constants | `Trending`, `My Liked`, `New`, trailing `Other` | the UI team ships a feature |
| **backend data** | the middle categories, from `GET /elitea_core/agent_categories/prompt_lib/{id}` | **an admin edits tags — no code change at all** |

One number pinned both. `12` re-arms the tripwire on the data half.

## The shape that survives

Derive the expected set from **the product's own response**, read passively
(`page.expect_response` around navigation — never `page.route`; that would be a
terminal substitution). This is canon, not improvisation: `.agents/testing.md`
§ Fidelity policy, *"the response is the oracle"*.

Then keep the teeth: **`to_have_count` matches attached-but-HIDDEN elements**, so a
count+set pair alone would pass on a collapsed rail. Add explicit `to_be_visible()`
on the head and tail members. In this case the *old* `count == 11` never checked
visibility either — so the replacement was **strictly stronger**, not looser. Say
that explicitly in the PR body; "you made the assertion tolerant" is the reading a
human will otherwise reach.

## Also mirror the composition function, not a snapshot of its input

The UI built the list as `[...FEATURED, ...apiNames.filter(n => n !== OTHER), OTHER]`.
Deriving `expected = FEATURED | apiNames` works only while the API happens to return
`Other`. Read the composition helper in `../EliteaUI/src` and mirror *it*.

## Check the TMS case before respeccing

Here the case text said only *"the layout remains consistent with no broken UI
elements"* — no count, no enumeration. The `11` was an **Axis-2 analyst addition in
the AFS**. So no product bug and no case-text clarification were owed; the only stale
artifact was our own spec. Confirm this before filing anything.

Related: [[control_run_before_blame]]
