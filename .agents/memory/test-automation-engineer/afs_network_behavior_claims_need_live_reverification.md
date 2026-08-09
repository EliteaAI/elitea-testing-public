---
name: AFS network-behavior claims need live re-verification, not trust-and-cite
description: ELITEA-2037's AFS claimed pipeline MCP-attach fires no persistence request ("only GET"), but the reused select_mcp_in_popper() hard-depends on a PATCH 201 — the AFS was simply wrong, confirmed by re-running the spec live
type: feedback
---

## What happened

ELITEA-2037's AFS (Test Steps step 4 + § Network Behavior) claimed: "unlike the
AGENT-level Tools section (#530), the PIPELINE-level Tools attach does **not**
auto-persist — no persistence request fires on attach (only GET calls)." The
clarification issue #1149 filed alongside it repeated the same claim.

The implementation's Step 3 calls the pre-existing `PipelineDetailPage.
select_mcp_in_popper()` (from ELITEA-1955), which hard-blocks on
`page.expect_response(... method == "PATCH" and status == 201 ...)` before
returning — if no PATCH fired, the call would time out and the step would
fail, not silently pass. It didn't time out; the spec passed clean on the
first implementer run and on 2 independent foreground re-runs during the fix
round. That's conclusive: the AFS's claim was factually wrong, not a stale
citation of some other endpoint.

## Lesson

- **A network-behavior claim in an AFS is a first-class assertion — verify it
  against what the reused page-object method actually depends on, not just
  against the AFS text.** If a pre-existing method the AFS's own case reuses
  hard-blocks on a specific request, and the test using it goes green, that
  IS the live re-verification — don't need a separate manual network capture
  if the implementation's own passing run already proves the point.
- When a sibling AFS + a filed clarification issue both repeat the same wrong
  network claim, fixing only the AFS isn't enough — the issue needs a
  correcting follow-up comment too (never silently edit somebody else's
  filed issue body; comment the correction, leave the original for audit
  trail), so anyone landing on the issue later doesn't re-propagate the error.
- When correcting AFS prose, keep a strikethrough audit trail of the original
  (wrong) claim next to the corrected one — cheaper for a future reader to
  see "this was corrected, here's what changed" than to silently overwrite it.
- The regression guard for this class of finding is usually already IN the
  code (the reused method's own hard-blocking wait) — the missing piece is
  documentation/assertion-message clarity tying that existing wait to the
  specific claim it disproves, not a brand-new assertion.

## Fix round 2 — the feature's `_surface.md` digest is a THIRD independent copy

A wrong network-behavior claim doesn't live in just the AFS + the clarification
issue. `test-specs/pipelines/_surface.md`'s MCP-node section carried its own,
independently-worded copy of the same "does NOT auto-persist / only GET calls"
claim — round 1 fixed the AFS and #1149 but missed it, and the reviewer caught
it as a fresh blocking finding in round 2. **When correcting a network-behavior
(or any live-product-fact) claim, grep the feature's `_surface.md` for the same
claim in its own words** — it's a separate hand-authored summary, not a
generated rollup of the AFS, so fixing the AFS never auto-fixes it.

Ownership note: `_surface.md` is normally analyst-owned (implementer reports
drift, doesn't edit) — but a fix-round dispatch that explicitly names the
`_surface.md` paragraph and directs the correction is a legitimate, narrow
exception; do the edit as instructed and flag the ownership boundary in the PR
comment for visibility rather than bouncing it back as `needs-analyst-rerun`.

## Recurrence — ELITEA-2072, self-caught pre-review (2026-08-09)

Wrote the AFS's Network Behavior section from a live browser probe that only
checked `console` entries after clicking a collapse/expand toggle — no actual
request capture. The claim ("zero network requests, either direction") was
wrong: expand remounts a child section that fetches its own supporting lists
on mount (7 legitimate `GET`s). The FIRST local test run (not a reviewer
round) failed on the over-broad assertion, which is the cheap place to catch
this — corrected the same session by narrowing to `method="PUT"` (the
assertion that actually matters: no accidental persist) and fixed the AFS +
`_surface.md` in the same commit. **Generalized rule: a console-only probe is
never sufficient evidence for a "zero network requests" claim on anything
that mounts/remounts a component with its own data-fetching hooks — capture
actual requests (`capture_requests_matching`) before writing that claim, or
scope the claim to the specific method/effect that matters (persist) instead
of "no requests of any kind."**

## Recurrence 2 — ELITEA-2070 (Pipeline Run History panel close, 2026-08-09)

Same shape again, different surface: the AFS claimed closing the Run History
panel (`X` button) "fires zero network requests" (confirmed live during
analysis via click + console check, no request capture). The implemented
test's first run failed: closing unmounts `RunHistoryContainer` and remounts
the Configuration form, which independently re-fires its own
view-population requests (tools/toolkits/tags/applications/index_types,
`upload_icon`) as a normal consequence of remounting — 8 requests, zero of
them Run-History-related. Corrected in the same run (1 rerun): narrowed the
assertion to "no re-fetch of the conversations list"
(`conversation`/`conversations` substring filter on captured request URLs)
— the claim that actually matters (closing isn't wastefully re-reading data
it's discarding) — and fixed the AFS + `_surface.md` (this file) in the same
commit, with a strikethrough audit trail per the rule above.

**Third occurrence of the identical root cause** (ELITEA-2037 persistence
claim, ELITEA-2072 collapse/expand, now ELITEA-2070 panel close) — all three
are "closing/collapsing/toggling one view remounts a sibling view that has
its own independent data-fetching effect." **Any AFS claim of "zero network
requests" tied to a view-switch (open/close, expand/collapse, tab switch,
panel toggle) should be treated as suspect by default** — the switch itself
may be a pure state flip, but whatever gets remounted almost always fetches
its own data. Capture requests, don't reason from the handler's source code
alone.
