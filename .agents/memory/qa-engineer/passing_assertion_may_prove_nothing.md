---
name: Assertion honesty — an assertion can pass without proving its claim
description: "There is an expect() at this step" is not "this step fails when the product is broken." Ten shapes where a real assertion is present and still vacuous, and the one question that catches all of them.
type: feedback
---

## Rule

For every assertion, ask: **in the broken case, would this exact call return a
different value?** If both branches of the failure mode produce the same
observable, the assertion is vacuous — an Important finding even though the
per-step-assertion gate is literally satisfied.

## The ten shapes and their remedies

1. **Wrong comparison target.** A positional/bounding-box check can be
   non-tautological (fails when inverted) and still compare against a
   structurally fixed sibling container instead of the claimed ordering.
   Invert-and-verify rules out tautology, never scope mismatch. Verify by
   manipulating the compared-against sibling (create a second real item) and
   confirming the result depends on it.
2. **Purpose-built handle, weakest assertion.** A testid added specifically to
   reach a live-verified string, then checked only with `to_be_visible()` —
   while a sibling one block later does `to_have_text()` for the same reason.
   Grep the actual assertion on any handle the PR narrates as "built to
   verify X"; the infra was done, the payoff wasn't collected.
3. **Contentless fixtures.** "Panel now shows B, not A" degenerates to vacuous
   when both A and B were created empty by fast API fixtures. Prefer an
   identity signal (a specific network response's target id) over a content
   signal.
4. **Timeout-swallowing getters.** `get_card_names()`-style helpers catch a
   `wait_for` timeout and return `[]`, so "genuinely 0 items" and "page failed
   to render" are indistinguishable — a post-delete absence assertion passes
   either way. Pair absence checks with a positive liveness check.
5. **Soft-assert step status.** `expect.soft()` never raises inline, so its
   `allure.step` reports `passed`; only the aggregated test status turns
   `failed` at teardown. Verify a sanctioned-RED from the raised
   `AssertionError` text; use the step tree only to confirm no OTHER step
   failed.
6. **Inherited settle.** A raw `.is_enabled()/.is_visible()` read may be safe
   only because a called method's internal fixed sleep + visibility wait
   precedes it, not because the transition is synchronous. When a PR fixes one
   raw read into a polling `expect(...)`, trace every sibling raw read on the
   same element; flag inherited-settle safety as a robustness note so a future
   cleanup of that upstream wait doesn't reintroduce the race.
7. **Filter-then-count hides over-firing.** `[r for r in captured if r.query ==
   EXPECTED][... ] == 1` only proves "the request I wanted eventually showed
   up with the right params" — it cannot see whether OTHER requests (a
   per-keystroke fetch instead of a debounced one, say `query=s`/`st`/`sto`/…)
   also fired and got filtered out before the count. When the claim under
   test IS the absence of extra firings (a debounce, a dedup, an
   at-most-once), assert the length of the UNFILTERED capture, not a
   post-filter subset — the two read identically once the wanted request
   shows up at all.
8. **Wait inherited from the wrong signal.** A baseline/first-read is "safe"
   because a preceding navigate/wait touched a RELATED but distinct element —
   e.g. a page heading becoming visible says nothing about an async
   data-fetch that populates a card grid underneath it. Every retrying wait
   added later in the same test (post-search, post-clear) is a tell: if step
   N's read needed a `wait_for_X_count`, step 1's read of the same collection
   needs one too, even though nothing forced it to fail yet.
9. **Relative-diff-only, no absolute baseline check.** A round-trip/preserve
   case ("field X survives export→import", "config survives fork/copy")
   captures the ORIGINAL value only to diff it against the COPY later —
   `assert copy[x] == original[x]` — and never independently asserts the
   original value was itself correct. If the baseline was already wrong (a
   node never wired to END, a default that never got set), the diff still
   passes because both sides carry the identical wrong value. Whenever the
   AFS Coverage Map names a step-1 observable ("canvas shows node wired to
   END") that ends up captured only for a later relative comparison, that
   observable needs its OWN absolute assertion at capture time, in addition
   to the equality check downstream — the two questions ("is the original
   right" vs "did the copy preserve it") are both real and neither implies
   the other.
10. **Sibling-signal substitution.** A "content switched" claim gets proven by
    (a) the OLD content's absence + (b) an unrelated sibling element's state
    change, instead of (c) the NEW content's own presence — when a testid for
    (c) already exists and was simply not reached for. (a)+(b) can both hold
    while (c) is false if (b)'s data source isn't causally coupled to (c)'s —
    e.g. two sibling sub-trees under the same parent, fed by *different*
    hook state, so one can render while the other silently fails/empties.
    Read the actual component source the AFS's own reasoning cites (not just
    the AFS's prose) to check whether the substituted signal and the claimed
    observable really share a data source, or merely share a mount/unmount
    boundary.

## Seen 10×

- PR #698/ELITEA-2132 R3 — bbox check proved Folders-vs-Conversations layout separation, never folder insertion order; an append-instead-of-prepend regression would pass.
- PR #696/ELITEA-2114 — `delete-confirm-title` (built to route around #694, text live-verified in the AFS) asserted visible-only.
- PR #696/ELITEA-2114 R2 — `get_message_count() == 0` after switching between two deliberately empty conversations: true whether the switch happened or the panel is stale.
- ELITEA-1947/PR #621 — `mcp_list_page.get_card_names()` returns `[]` on any timeout; shared across 6+ specs.
- PR #675/ELITEA-1835 — every allure step `passed` while the test was correctly sanctioned-RED from a soft assert.
- PR #682/ELITEA-2090 — GA3's race fixed to polling; GA1's bare `is_disabled()` on the same button safe only via `click_create_conversation()`'s internal 1 s sleep.
- PR #1230/ELITEA-2363 — Step 4 filters captured `public_applications` requests down to `query=="story"` before asserting `len()==1`; a broken debounce firing one request per keystroke would still leave exactly one entry with the final query value, so the "single debounced request" claim (the AFS's own Axis-2 addition) goes unverified. Same PR, Step 1: `get_visible_agent_card_names()` read right after `navigate()` (which only waits on `page_heading`, not the bulk applications fetch) — the identical async-render race the implementer had *just* fixed for `clear_search()` (steps 5/6 use `wait_for_agent_card_count[_not]`), left unfixed on the baseline read those two steps compare against.
- PR #1335/ELITEA-2012 — `test_pipeline_import_via_file.py` step 1 captures `original_yaml`'s LLM-node `transition` purely to diff against the imported copy at step 7 (`imported_llm_node["transition"] == original_llm_node["transition"]`); the AFS Coverage Map names "canvas node wiring" as asserted AT step 1, but no absolute check (`== "END"`) exists — a creation-time wiring regression would round-trip identically and stay invisible.
- ELITEA-2370 R3 (`tests/2370-catalog-tabs`) — Step 8 ("main content switches to Skills content") proven only via agent-card absence + the RIGHT-PANEL filter-chip prefix flipping to skill-scoped; `CatalogBody.jsx` shows the chip rail is fed by `allCategories`/`categoryNames` while the main-content grid is fed by the separate `groupedItems` — a failed/empty skills fetch would leave the grid on its "No skills found" empty state while chips still count correctly. A pre-existing `skill-card-{id}` testid (`SkillCard.jsx:48`, already on `automation/testids`) — the direct analog of the `AGENT_CARD_PREFIX`/`wait_for_any_agent_card()` pair used to prove the symmetric Step 5 claim — sat unused.

See also: positional_assertion_wrong_comparison_target_survives_invert_sanity_check.md ·
purpose_built_handle_asserted_visible_not_text_elitea2114.md ·
empty_test_data_can_defeat_content_based_assertions.md ·
list_page_getter_timeout_swallow_masks_load_failure.md ·
allure_soft_assert_step_status_does_not_fail.md ·
raw_read_safe_only_via_inherited_settle_review_heuristic.md
