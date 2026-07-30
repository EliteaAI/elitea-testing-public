---
name: Assertion honesty — an assertion can pass without proving its claim
description: "There is an expect() at this step" is not "this step fails when the product is broken." Six shapes where a real assertion is present and still vacuous, and the one question that catches all of them.
type: feedback
---

## Rule

For every assertion, ask: **in the broken case, would this exact call return a
different value?** If both branches of the failure mode produce the same
observable, the assertion is vacuous — an Important finding even though the
per-step-assertion gate is literally satisfied.

## The six shapes and their remedies

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

## Seen 6×

- PR #698/ELITEA-2132 R3 — bbox check proved Folders-vs-Conversations layout separation, never folder insertion order; an append-instead-of-prepend regression would pass.
- PR #696/ELITEA-2114 — `delete-confirm-title` (built to route around #694, text live-verified in the AFS) asserted visible-only.
- PR #696/ELITEA-2114 R2 — `get_message_count() == 0` after switching between two deliberately empty conversations: true whether the switch happened or the panel is stale.
- ELITEA-1947/PR #621 — `mcp_list_page.get_card_names()` returns `[]` on any timeout; shared across 6+ specs.
- PR #675/ELITEA-1835 — every allure step `passed` while the test was correctly sanctioned-RED from a soft assert.
- PR #682/ELITEA-2090 — GA3's race fixed to polling; GA1's bare `is_disabled()` on the same button safe only via `click_create_conversation()`'s internal 1 s sleep.

See also: positional_assertion_wrong_comparison_target_survives_invert_sanity_check.md ·
purpose_built_handle_asserted_visible_not_text_elitea2114.md ·
empty_test_data_can_defeat_content_based_assertions.md ·
list_page_getter_timeout_swallow_masks_load_failure.md ·
allure_soft_assert_step_status_does_not_fail.md ·
raw_read_safe_only_via_inherited_settle_review_heuristic.md
