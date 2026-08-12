---
name: Reviewer verify shared-component fix by running the sibling test
description: PR #657/ELITEA-1868 — when a PR's Run Report claims "re-verified an already-merged sibling test still passes" after touching a SHARED component, actually run that sibling test against the same live commit instead of only reading the diff for compatibility
type: feedback
---

## What happened

PR #657 (ELITEA-1868, Cancel-during-toolkit-creation) touched `DiscardButton.jsx`
— a shared component also used by `CredentialsTabBar.jsx` — to fix a pre-existing
prop-name mismatch (`confirmButtonDataTestId` was forwarded to `Modal.BaseModal`
under the wrong prop name, so no caller's confirm-button testid ever reached the
DOM). The PR's Run Report claimed this was "verified via the already-merged
`test_credential_discard_changes.py`, which now passes cleanly."

## What I did instead of trusting the claim

1. Read the diff to confirm the change was internal-only (DiscardButton's own
   public prop name unchanged, so no caller's call-site signature changed) —
   necessary but not sufficient.
2. Confirmed live that `CredentialsTabBar.jsx` already passed
   `confirmButtonDataTestId="credential-discard-confirm-button"` *before* this
   PR (untouched file, not part of the diff) — meaning the bug this PR fixes
   would have affected that caller's testid too, before the fix.
3. **Actually ran** `HEADLESS=true pytest tests/ui/toolkits/test_credential_discard_changes.py -v`
   against the exact EliteaUI commit (`53a4b8cb` on `automation/testids`) the
   PR cites — PASSED, all 10 Allure steps green, including the exact
   Discard-confirm step that exercises the fixed code path. 12 seconds, fully
   conclusive.

## Why this matters generally

A diff-only read proves the change *could* be compatible. It doesn't prove the
already-merged test that exercises the shared component *actually* still
passes against the live app — there could be a second interaction the diff
read misses (CSS selector shift, timing change, an assumption the diff-reader
didn't think to check). When the sibling test is cheap to run (seconds, not
minutes) and the dev server is already up, there's no reason to settle for
"looks compatible" when "confirmed passing" is one command away.

**Rule of thumb**: any PR whose Run Report claims "re-ran sibling test X, still
passes" after touching a component with ≥2 callers — run X yourself in the
same review session, against the same commit the PR built against, before
accepting the claim.
