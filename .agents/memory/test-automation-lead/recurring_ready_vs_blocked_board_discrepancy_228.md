---
name: Recurring Ready-vs-Blocked board discrepancy (#228 pattern)
description: a card's own work-log can say "Card → Ready" (correct, delivery-complete) while the board later shows Blocked, because a SEPARATE loop mechanism re-queues an already-terminal card and parks it after "N sessions without leaving queue" — distinguish this from a genuine Blocked (real Waiting-on-#N) before flagging it as a defect
type: feedback
---

## What happened

Issue #228 (ELITEA-1824) has now shown up in 3 consecutive same-day control
audits (#257 09:40, #260 10:01, #262 10:26 — 2026-07-20) as a standing-watch
item: its own work-log closes cleanly — closure record posted, then
`"✅ Done. ... Card → Ready. Issue stays OPEN..."` (2026-07-19T18:30:08Z) — but
23 minutes later a DIFFERENT comment appears: `"🚫 Factory (test-automation-lead):
3 sessions without the card leaving this loop's queue. Parking it as Blocked —
a human should look, then drag back to Approved to retry."` and the board
status is `Blocked` ever since.

## Why this isn't a delivery defect

The delivery itself (PR #653, merge `79fe4e84`) is fine — sanctioned-RED gate
passed, TMS back-written, closure record complete. The `Blocked` status is a
symptom of a SEPARATE control-loop mechanism that re-queues cards and, after
some session-count threshold, parks them regardless of whether the
underlying work already reached a terminal state. This is an infra/loop-config
issue, not something the delivering session or a control audit of THAT
delivery can fix.

## How to tell the difference during standing watch

Before flagging a `Blocked` card as a discrepancy worth a human's attention,
read its last 2-3 comments:
- **Genuine Blocked** (like #108/#110 on 2026-07-20): the last comment is a
  real open question to a human (e.g. "@person, have a look at...", "need to
  check session..."), consistent with `Waiting on #N` semantics. Not a
  discrepancy — this is `Blocked` working as intended.
- **Loop-requeue artifact** (like #228): the last comment BEFORE the `Blocked`
  parking is the card's own closure record + "Card → Ready", and the parking
  comment itself cites a session/queue-count threshold, not a real blocker.
  This is the pattern worth flagging.

## Action

Keep re-flagging it in the standing-watch note each audit that touches it
(cheap, catches recurrence) but don't spend a full audit cycle re-verifying
#228's own delivery quality each time — that was already independently
confirmed by the #260 audit's item-3 promotability trace (#228's 19-row table
checked out clean). The fix is orchestrator/loop-config, escalate via the
watch note's language, not via re-auditing the same delivery repeatedly.
