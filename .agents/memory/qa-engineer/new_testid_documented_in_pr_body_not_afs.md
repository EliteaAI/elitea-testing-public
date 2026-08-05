---
name: New testid documented in PR body, not the AFS
description: An implementer-discovered testid the AFS never asked for gets written up in the PR body/memory but the AFS Concrete Handles table and Coverage Map are never amended — check the AFS diff itself, not just the narrative.
type: feedback
---

Pattern seen on ELITEA-2356 (PR #1219): the AFS's Coverage Map said "step 3 —
dialog visible" with no named handle. Mid-implementation the implementer hit
the MUI-dialog-needs-its-own-testid gotcha (their own memory:
`mui_dialog_needs_its_own_testid_not_role_dialog.md`) and added a brand-new
testid (`catalog-agent-modal`) that the AFS's Concrete Handles table had no
row for at all. It got a thorough write-up in the PR body ("Testids added"
bullet) and the implementer's own daily-log entry — but the actual AFS file
under `test-specs/` was never touched, and even the test file's own docstring
list of "new testids this implementation added" omitted it.

**Why this matters:** PR-body/memory documentation is ephemeral to THIS PR.
The AFS (and `_surface.md`) is what the NEXT case on the same component reads
— e.g. every ELITEA-2357/2358/2359/… sibling that also opens this modal now
has no record that `catalog-agent-modal` exists, and might rediscover it
under a different name or reach for `get_by_role("dialog")` again.

**Reviewer check, concretely:** when the diff adds a `LocatorDescriptor` whose
testid string doesn't appear anywhere in the AFS's Concrete Handles table —
`grep -o '"catalog-[a-z-]*"' <afs-diff>` vs the new field's testid — that is
exactly the drift `reviewer-contract.md` § Standing checks ("AFS amendments")
means to catch, even when the PR body/commit message documents it well. A
narrative writeup is not an AFS docs commit.
