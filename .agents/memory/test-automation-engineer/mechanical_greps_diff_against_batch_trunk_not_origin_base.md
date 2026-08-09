---
name: Mechanical greps (additive-only, non-testid-handle) must diff against the batch trunk, not origin/automation/base
description: Inside a live batch, origin/automation/base lags the batch trunk by every already-merged-but-not-yet-promoted unit — diffing against it pollutes BOTH the additive-only ('^-[^-]') and the non-testid-handle ('^[+]...') greps with unrelated prior units' lines, not just your own change.
type: feedback
---

## What happened (ELITEA-2044, combined analyst+implementer slot)

Ran the two mandatory mechanical checks (Hard Rule 3 additive-only, and the
reviewer-style non-testid-handle grep) against `origin/automation/base` while
standing on a batch feature branch cut from `tests/batch-pipelines-remaining-w6`.
The batch trunk was several units ahead of `origin/automation/base` (e.g.
ELITEA-2043's `is_state_variable_present` method, already merged to the trunk
but not yet promoted to `automation/base`). The non-testid-handle grep then
showed THAT unrelated method's `self.page.locator(...)` line as a "new" `+`
hit in my diff — not a real finding, just batch-trunk-vs-base drift. The
additive-only check happened to still come back empty in this case, but the
same drift can just as easily produce a false `-` hit if an earlier unit in
the batch had reordered or touched nearby lines.

This is a distinct trap from `additive_only_grep_scope_your_own_unmerged_commits.md`
(which covers a FIX-ROUND's working-tree-vs-last-commit noise) — this one is
about picking the wrong **base ref** during the very first implementation pass,
and it affects the `+`-side grep too, not just the `-`-side one.

## The fix

Inside a batch, always diff against the trunk you actually branched from:

```bash
git diff <batch-trunk> -- automation/ | grep -nE '^[+].*(get_by_role|...)'   # non-testid handles
git diff <batch-trunk> -- <shared-file> | grep -E '^-[^-]'                   # additive-only
```

Never `origin/automation/base` while a batch trunk exists — it is stale by
design (batch trunk merges to base only at Report/Close time) and every hit
needs a "is this actually mine?" triage that a correct base ref makes
unnecessary.
