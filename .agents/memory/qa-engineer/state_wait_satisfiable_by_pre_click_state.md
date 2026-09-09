---
name: A state wait satisfiable by pre-click state is not a completion signal
description: When a repair swaps expect_response for a state wait, check EVERY caller's index/state — the wait may pre-exist the action for some of them
type: feedback
aliases: [state wait, expect_response replacement, auto-select tautology, shared page-object wait]
tags: [area/page-objects, type/review-trap]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

A repair replaces `page.expect_response(...)` around a click with a "state wait"
(`expect(row).to_have_attribute("data-selected","true")` + `some_item.first.wait_for(visible)`)
because the awaited request stopped firing for the row the repair cares about.

Both halves of such a wait can be **satisfied by state that existed before the click**:

- a `data-*` selection attribute flips synchronously with React state, *before* the
  detail fetch it triggers resolves;
- a `.first.wait_for(visible)` on a shared list is satisfied by the **previously**
  rendered content, if the component keeps rendering stale data while refetching.

The method then returns immediately and the caller reads stale content.

## How to check it statically (ELITEA-2070 repair, PR #2068)

1. Enumerate EVERY caller of the shared method and the **index/state each passes** —
   the repair only proved index 0; index 1 was another merged case (ELITEA-2011).
2. For the "content rendered" half, read the render path, not the fetch:
   `RunHistoryChat.jsx` derives `chatHistory` from RTK-Query lazy `data` (which
   persists across arg changes — that is why `currentData` exists), and
   `ChatMessageList.jsx` maps `chat_history` **unconditionally** (its `Skeleton` is
   gated on `isLoadingMore`, not `isLoading`). So the old conversation's
   `chat-message-item` nodes stay in the DOM during the new fetch.
3. Ask the tautology question in both directions: *would this assertion still pass if
   the click were deleted?* If yes for the repaired caller, that is fine only when
   another spec carries the causal proof — and then that spec's determinism becomes
   load-bearing for this case's coverage claim.

## Related

`RunHistoryContainer.jsx:93-95` auto-selects row 0 on open (EliteaAI/EliteaUI@84025881),
which is what made the index-0 `expect_response` a race in the first place. The honest
fix keeps the response wait for rows that are **not** already selected.

## A probe that does not reproduce is not a refutation (PR #2068, fix round 1)

The live probe clicked a non-selected row and saw `data-selected=true` with **0**
message items — so the stale-message half did not appear. That is not evidence the
wait was safe; it is evidence the outcome is **ordering-dependent**, which is the
definition of a race:

- *messages not yet rendered at click time* → `.first.wait_for` genuinely waits → safe;
- *messages already rendered* (the previous row's) → satisfied instantly by stale nodes → unsafe.

The second ordering is reachable whenever the caller spends round trips between opening
and clicking (ELITEA-2011's Step 5 iterates every row's text first). Ask which orderings
exist before reading a green probe as an all-clear.

**Residual after the conditional fix:** `expect_response` returning means the response
*arrived*, not that React *committed* it — so a caller reading content immediately after
can still catch a stale frame. That gap is pre-existing (the original docstring called it
a "transient" read) and is only closed by an auto-retrying assertion
(`expect(...).to_contain_text(...)`) at the call site, not by any page-object wait.
