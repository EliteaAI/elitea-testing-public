---
name: Loop redispatch on a terminal Ready card can trigger a false-positive Blocked auto-park
description: after a card reaches its terminal Ready state, the factory loop can keep re-dispatching the SAME issue; each re-dispatch correctly finds nothing to do and takes no action (per protocol — no card-status write on a no-op turn), but a separate safety valve watching "session count without the card leaving the loop's queue" reads that correct inaction as stuck and auto-parks the card Blocked; the fix on pickup is verify-the-delivery-end-to-end-then-unblock, never redo the pipeline
type: feedback
---

## What happened (#228, ELITEA-1824)

Delivered ELITEA-1824 fully on 2026-07-19 (PR #653 merged, independent 3× gate, TMS
back-write, closure record) and moved the card to `Ready`. The loop then re-dispatched
me on the SAME issue #228 two more times. Both times, per protocol (`YOUR FIRST
ACTION... read ALL comments newer than your last work-log entry`), I re-checked the
issue: no new human comments, board status still `Ready`, nothing to do — and correctly
took no action (no card-status write, no new comment beyond confirming this) each time.

A separate mechanism — not part of this pipeline's own rules, a factory-level safety
valve — then posted: *"3 sessions without the card leaving this loop's queue. Parking
it as `Blocked`."* This is a false positive: the card DID leave the loop's queue (it
reached `Ready`, its correct terminal state) — the valve's heuristic apparently counts
"sessions dispatched on this issue" rather than "sessions since the card last changed
FROM a non-terminal state," so continued redispatch on an already-`Ready` card looks
identical to a stuck-in-progress card from outside.

4 days later a human commented "let's complete it if possible" and dragged the card
back to `Approved` (the correct un-block move per Rule 1).

## The fix (what NOT to do, what TO do)

**Wrong instinct**: seeing `Blocked` + "let's complete it" and inferring the work must
be incomplete, then re-running the pipeline (re-dispatching analyst/implementer/
reviewer) from scratch. This would duplicate a fully-shipped delivery.

**Right response**: treat this exactly like `interrupted_dispatch_recovery.md`'s
pattern one level up — re-verify the ACTUAL delivered state independently before
assuming anything is missing:
1. Is the PR still `MERGED`? (`gh pr view --json state,mergedAt,mergeCommit`)
2. Has the shared test/page-object file been touched since by another case? If so,
   confirm additive-only (`git show <commit> -- <file> | grep '^-[^-]'` empty) — a
   sibling `extend-existing` delivery landing cleanly is not a regression.
3. Re-run the specific test node once (not a full fresh 3× gate — that's the NEW-delivery
   merge gate, not required for a no-op re-verification) against a freshly-started local
   UI, and confirm the signature matches the original closure record (same known-defect
   IDs, still OPEN).
4. Re-check testid promotability fresh (`git fetch` + grep against `origin/main`) —
   don't assume it's unchanged, but don't be surprised if it is (promotion is
   human-paced and can sit for days).
5. Confirm the TMS back-write and closure record are both still intact.

If all of that holds — as it did here — post a re-confirmation comment (what was
checked, what's unchanged) and move the card straight back to `Ready`. No pipeline
dispatch needed. This is strictly cheaper than a redelivery and is the only way to
avoid shipping a duplicate PR for already-merged work.

## Broader lesson

A card's `Blocked` state is not always evidence of an unresolved blocker in the WORK —
it can be an artifact of the surrounding orchestration/loop machinery misreading
correct inaction as stuck. The signal to distinguish the two: read the `Blocked`
comment's own text. `"Waiting on #N"` (a real filed question/bug) means something is
actually incomplete. `"N sessions without the card leaving this loop's queue"` (this
project's specific auto-park phrasing) means the loop's own bookkeeping flagged
something, and the FIRST move on pickup is to check whether the card was already
terminal, not to assume the delivery needs redoing.
