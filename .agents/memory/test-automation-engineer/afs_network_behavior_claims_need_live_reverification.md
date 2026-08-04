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
