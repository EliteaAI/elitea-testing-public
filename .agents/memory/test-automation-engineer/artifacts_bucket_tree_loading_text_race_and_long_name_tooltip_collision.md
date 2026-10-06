---
name: Artifacts bucket-tree sibling label races "Loading files..." + long bucket names collide with the info tooltip
description: ELITEA-1805 — the left-panel tree empty-state sibling div is briefly "Loading files..." before settling; a long/timestamp-suffixed bucket name overflows the row and opens a second, unrelated [role="tooltip"]
type: feedback
aliases: [artifacts bucket tree empty state, No files in this bucket race, bucket info tooltip strict mode, overflow tooltip collision]
tags: [area/ui-tests, area/artifacts]
created: 2026-10-06
updated: 2026-10-06
---

## Trap 1 — the tree sibling's "No files in this bucket" label is preceded by "Loading files..."

`BUCKET_TREE_EMPTY_STATE` (`[data-testid="artifacts-bucket-row-{}"] + div`,
`automation/pages/artifacts_page.py`) renders `"Loading files..."` for a brief
window, THEN settles to `"No files in this bucket"` — both strings are on the
SAME element and both count as `state="visible"`. A plain
`label.wait_for(state="visible")` races this and can read the loading text,
producing a flaky `AssertionError` on the final content check (not even a
timeout — it resolves "successfully" with the wrong text).

**Fix:** wait on the exact expected text, not mere visibility —
`expect(label).to_have_text("No files in this bucket", timeout=...)`
(`expand_bucket_tree_if_needed()`). This also makes the "is it already
expanded?" short-poll correct (a short `to_have_text` catch on
`AssertionError`, not `PlaywrightTimeoutError` — `expect()` raises
`AssertionError` on timeout, not Playwright's own `TimeoutError`).

## Trap 2 — a long generated bucket name opens a SECOND tooltip that collides with Step 11's read

If the test's own generated bucket name is long (e.g. ELITEA-1808's own
`autotest-{node_name}-{ts}` convention, ~45+ chars), the left-panel row text
overflows and the row's OWN conditional MUI overflow-tooltip can be triggered
and lingers (NOT purely hover-driven — `page.mouse.move(0, 0)` before the
deliberate info-icon hover does **not** dismiss it). With that tooltip still
open, `get_bucket_info_tooltip_text()`'s `get_by_role("tooltip")` then hits a
Playwright **strict-mode violation**: 2 elements match
(`name="<bucket-name-prefix>"` and `name="Retention Policy: 1 Year"`).

**Fix:** keep bucket names SHORT for this flow — the AFS's own exploration
bucket (`elitea1805-empty`, 16 chars) never overflows and never triggers this.
`test_artifacts_landing_page_ui.py`'s `_generate_bucket_name()` deliberately
stays short (`elitea1805-{6-digit-ts}`) rather than reusing ELITEA-1808's
longer helper. If a future case genuinely needs a long bucket name AND the
info tooltip in the same flow, disambiguate by filtering on the known tooltip
content substring instead of a bare role query.

Related: [[afs_is_a_work_order_not_gospel]]
