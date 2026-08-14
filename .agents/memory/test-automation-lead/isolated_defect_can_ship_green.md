---
name: An isolated-defect assertion can legitimately ship GREEN, not just RED
description: a soft-assertion tied to an open, isolated defect may not reproduce at merge-gate time when the trigger is data/account-state-dependent (conversation size, record count) rather than universally reproducible — that's fine if the assertion is honestly checking correct behavior, not reverse-masked; what actually matters is verifying the assertion's LOGIC is sound, since a subtle bug there is the real risk of shipping a check that would never catch anything
type: feedback
---

## What happened (ELITEA-1799, issue #148, PR #608, defect #607)

Directed the implementer to add a soft-assertion for an isolated, already-
filed defect (#607: Support Assistant conversation-restore truncates to the
oldest 100 message groups on large conversations) per this project's
Sanctioned-RED merge-gate convention, expecting it to reproduce RED
deterministically like the precedent cases (#26/#27).

It didn't. The implementer honestly reported GREEN 3/3: this test's own
pre-New-Chat conversation is freshly created within the test run (New Chat
resets it every run) and never accumulates past the ~100-group threshold,
unlike the analyst's manual pass which happened to catch the shared test
account mid a long, un-reset 218-group conversation. The trigger condition
(conversation size) is account-state-dependent, not something this specific
automated flow reliably reproduces on its own.

This is a **legitimate, non-masking outcome** — the assertion checks
*correct* behavior (message/response preserved across New-Chat + History
restore), not the current buggy behavior reverse-masked to look right. It
functions as a forward-looking regression net: it will start failing if the
account's active conversation ever does exceed the threshold again.

## The actual risk this near-missed

The real danger wasn't "it's green instead of red" — it was that the
implementer's first draft of the assertion had a genuine unit-mismatch bug
(compared a TOTAL message count against an ASSISTANT-ONLY baseline) that
the R1 reviewer proved would NOT have caught the analyst's own confirmed
repro numbers even if the account state HAD been right. A green assertion
built on broken comparison logic is silent dead coverage — indistinguishable
from a correct-but-currently-untriggered one unless someone actually verifies
the comparison logic against known repro numbers.

## The lesson

Don't treat "an isolated-defect assertion didn't reproduce RED at merge
time" as a failure signal by itself, and don't push an implementer to force
an artificial repro (e.g. seeding artificial data) unless the AFS/case
data-strategy calls for it. Instead verify the assertion's *logic*: would it
have caught the defect's own documented repro numbers, worked through by
hand? That's the check that actually protects against shipping a soft-assert
that never fires for the wrong reason. See the companion entry
`afs_defect_found_can_be_extend_existing_shaped.md` for the routing side of
this same case.
