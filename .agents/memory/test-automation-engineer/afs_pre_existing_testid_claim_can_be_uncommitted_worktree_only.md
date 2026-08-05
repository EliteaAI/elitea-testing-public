---
name: AFS "pre-existing testid" claim can mean uncommitted EliteaUI worktree only
description: An AFS's "zero new add-data-testid work required" claim can be true of the LIVE dev-server DOM (HMR-served) while the testids are still uncommitted in the EliteaUI working tree — check `git diff`/`git log`, not just the DOM, before trusting "pre-existing"
type: feedback
---

## What happened (ELITEA-2336)

The AFS for ELITEA-2336 stated all 9 core Secrets-page testids were
"pre-existing — zero new `add-data-testid` work required for this case's own
9 steps." Live DOM inspection (`document.querySelectorAll('[data-testid=...]')`)
confirmed all 9 were present and functioning. But `cd ../EliteaUI && git
status` showed those exact 9 attributes as **uncommitted working-tree
modifications** — `git log` on the same files showed no commit introducing
them. The analyst (or an earlier session) had evidently added them live via
HMR during exploration, confirmed them working in the DOM, and never
committed.

**Why the DOM check alone is insufficient:** Vite HMR serves whatever is on
disk in the working tree instantly, whether or not it's committed. A live
`document.querySelectorAll` proves the testid EXISTS RIGHT NOW on THIS
machine's dev server — it says nothing about whether it will survive a
`git stash`, a branch switch, or reach `automation/testids`/`main` for any
other environment (deployed envs, another contributor's clone, CI).

## The check that catches this

Before trusting an AFS's "pre-existing, no testid work needed" claim, run
in `../EliteaUI`:
```bash
git status --short                    # uncommitted?
git log --oneline -1 -- <file>        # committed, and when?
git diff -- <file>                    # what's actually uncommitted, if anything
```
If the testids show up in `git diff` (uncommitted) rather than `git log`
(committed history), they are NOT actually "pre-existing" in the sense the
locator-policy provenance table means (on `automation/testids` / `main`) —
they're scratch work sitting in the shared working tree, one `git clean`/
`git checkout` away from vanishing for anyone else. Commit them onto
`automation/testids` (same `add-data-testid` flow) as part of your
implementation, and correct the AFS provenance note in your Run Report
rather than silently trusting it.

(from ELITEA-2336)
