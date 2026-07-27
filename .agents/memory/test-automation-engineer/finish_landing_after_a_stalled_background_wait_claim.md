---
name: Finish-landing after a stalled "waiting for background regression" claim
description: A prior implementer session ending its turn on "waiting for a background suite to finish" is a dead end in this dispatch model (no monitor exists for a subagent's own started background processes) — the correct move is a fresh dispatch that re-verifies every described artifact from scratch, not one that trusts the description and skips to commit
type: feedback
---

## What happened (ELITEA-1840)

A prior implementer session did the real work correctly (EliteaUI testid
commit pushed, page object + test file written in the working tree) but
ended its turn saying it was "waiting for a background regression suite to
finish." That wait never resolves for a subagent — there is no monitor that
watches a subagent's own self-started background process across turns in
this dispatch model — so the branch sat uncommitted indefinitely until a
fresh dispatch picked it up.

## The trap

A dispatcher (or a fresh implementer) reading a detailed, confident
description of "already sitting correct and complete in the working tree"
is tempted to skip straight to commit/push/PR on the strength of the
description. That's the same "trusted a peer agent's self-report instead of
verifying independently" failure class as any other unverified handoff —
the description being unusually thorough doesn't change that.

## What to do instead

Treat a "waiting on background work" sign-off exactly like any other
unverified claim: re-derive it from scratch before acting on it.

- Confirm the described upstream commit actually exists where claimed
  (`git log --oneline -- <path>` / `git show --stat <sha>` on the
  *actual* dependency repo, not just trusting the SHA string).
- Confirm the working-tree diff is what's described — read it, don't
  skim the summary (in this case: additive-only check on the page object,
  full read of the new 381-line test file).
- Confirm every fixture / pre-existing page-object method the new test
  calls actually exists (`grep -n "def <method>"`) rather than assuming
  "prior session's work" implies it compiles.
- Then run the CI command yourself, blocking, 2-3x — the prior session's
  claimed intent to run a regression suite is not evidence a suite ran.

In this case everything held up clean on re-verification (GREEN 3/3,
21-29s each), so the fix was purely procedural — commit, push, PR #644,
comment on #222. The lesson is about the discipline of re-checking before
trusting a "sitting correct and complete, just needs a wait" claim, not
about anything being wrong with the prior session's actual code.

## Generalization

Any time a dispatch says "a prior session already did X, just verify and
ship it" — read that as "nothing here is verified yet from this session's
perspective," and run the full independent-verification pass anyway. The
cost of re-verifying a correct claim is a few minutes; the cost of shipping
an unverified one on trust is a broken PR with your name on the commit.
