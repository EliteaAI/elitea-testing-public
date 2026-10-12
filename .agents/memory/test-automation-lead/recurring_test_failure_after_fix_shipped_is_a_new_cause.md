---
name: Recurring CI timeout on a test already covered by a merged fix — check ancestry before assuming it rides the old PR
description: "#2419 (ELITEA-2493) repeated #2403/#2407's CI timeout signature AFTER PR #2404 merged+promoted; git merge-base proved the old fix was already live, so it had to be a NEW cause — correctly diagnosed as shared-state leak, not re-filed as a duplicate"
type: feedback
---

## What happened (2026-10-08, #2419)

`test_no_access_permission_blocks_all_api_operations` (ELITEA-2493) timed out
in CI again (run #37718019323, commit `2594a66` on `main`) — superficially the
same shape as #2403/#2407 (same test file, same "Manage Permissions" area,
same `Locator.wait_for: Timeout 10000ms exceeded`). The precedent in this exact
suite (#2407) had already established "ELITEA-2493 is the same root cause as
ELITEA-2494, rides the existing fix PR, no second PR needed" — it would have
been easy, and *consistent with the last session's own conclusion*, to write
the same verdict again.

**That would have been wrong this time.** Before diagnosing, I ran:
```
git merge-base --is-ancestor <fix-commit> <failing-run's-commit> && echo YES
```
and confirmed the DotMenu-hover fix (`f791447a`, PR #2404/#2417) was already an
ancestor of BOTH `automation/factory` and the exact commit (`2594a66`) this new
run failed against — merged and PROMOTED to `main` well before this run. A fix
that is already live and the failure still happens cannot be the same cause by
definition. Live analyst triage then found a genuinely different mechanism
(shared/never-rotated bucket name leaking a stale permission exception across
runs — see the traceback line number, which also differed from #2403's: a
different method entirely, `add_permission_exception` vs `open_manage_permissions`).

## Rule of thumb

A recurring failure with an identical generic signature on a test that was
already "fixed" is NOT automatically a duplicate verdict. Before writing
"rides the existing PR, no new work needed":
1. Confirm the fix commit is an ancestor of the NEW failing run's commit
   (`git merge-base --is-ancestor <fix-sha> <failing-sha>`) — not just that a
   fix exists for a similarly-named issue.
2. Read the actual traceback/line number from the new failure — a shared
   symptom (same error class, same general UI area) can come from a different
   method/line than the one the old fix touched.
3. Only conclude "same cause, no new work" when the fix is confirmed NOT yet
   live on the failing commit, or when the new traceback points at the exact
   same line the old fix changed.
