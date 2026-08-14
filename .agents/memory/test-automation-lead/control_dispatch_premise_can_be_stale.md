---
name: Control dispatch premise can be stale
description: A control/audit dispatch's framing ("a delivery in Ready awaiting routing") is a claim, not a fact — verify board status and merge/PR state directly before scoring a checklist; if nothing was actually delivered, use a distinct not-ready verdict instead of FAIL
type: feedback
---

## What happened

Dispatched as an independent Control auditor for issue #26 (ELITEA-1735
testid-rework), framed as "ONE card in `Ready`... a delivery (test merged,
closure record posted) awaiting the human's routing." Ground truth
contradicted this on every axis:

- Board status was `In Progress`, not `Ready`.
- No closure record existed — the last comment was a mid-rework dispatch note.
- No successor PR to the original #39 existed on `elitea-testing-public`.
- The "delivery" was actually a stalled/interrupted session: real uncommitted
  work sat on a local branch (`tests/ELITEA-1735-testid-rework`, 0 commits
  ahead of base — page objects + AFS reworked, but the test file itself
  untouched), while the companion EliteaUI side was further along (a real
  commit on `automation/testids` + an open draft PR).

## Why it matters

The 8-point checklist (locator policy, testid delivery, promotability,
closure record, merge gate, reviewer gate, AFS traceability) presumes a
merged PR and a posted closure record exist to check against. Scoring it
anyway would force a false choice: either fabricate compliance findings
against nothing, or mark **FAIL** — which reads to the human as "this
delivery was audited and rejected on quality grounds," when the actual
situation is "no delivery happened yet, a session got interrupted mid-flight
with real WIP on disk." Those need different human responses (resume the
stalled session vs. re-do rejected work) and conflating them wastes the
human's routing decision.

## Rule going forward

Before scoring the checklist on any control-audit dispatch:

1. **Verify board status directly** (`gh project item-list`) — don't trust
   the dispatch text's framing of "in Ready."
2. **Verify a PR was actually merged** for the specific rework/case being
   audited (not an older, already-known-noncompliant PR the rework is
   superseding) — `gh pr list --search "<id>"`.
3. **Verify a closure record was posted** — the last comment, not assumed.
4. If any of these come back negative, this is **not a delivery to audit
   against the checklist** — it's an incomplete/stalled delivery. Use a
   distinct verdict (e.g. "NOT-READY — audit cannot run, delivery
   incomplete") rather than FAIL, cite the exact evidence (board status,
   `gh pr list` output, last-comment timestamp), and — since real WIP may
   exist — check for it (git branches, uncommitted diffs, companion-repo PRs)
   so the recommendation to the human is "resume from X," not "start over."
5. Still add the `control:audited` label and leave the card untouched
   (verdict-only contract) — the label is the completion signal regardless
   of which verdict shape you used.

This is a distinct failure mode from `interrupted_dispatch_recovery.md`
(which is about the deliverer's own recovery after an interruption) — this
entry is about the AUDITOR correctly recognizing an interrupted delivery
instead of misjudging it as a completed one.
