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
implementation, and correct the AFS provenance note **in the AFS file
itself** — a `docs(afs): …` commit amending the § Concrete Handles table row
by row (provenance column + originating commit SHA) — not just narrated in
the PR description or Run Report.

**Round-1 correction (same case, review round):** the first implementation
pass DID mention the true provenance — but only in the PR body's "Testid
provenance" paragraph and the Run Report, never as an edit to the AFS's own
Concrete Handles table, which still read "All handles below are pre-existing
testids — zero new `add-data-testid` work required" through the whole review
cycle. The reviewer's mechanical check reads the AFS file, not the PR prose —
narrating a correction anywhere other than the AFS itself does not close the
finding, even when the narration is accurate and even when it ships in the
same PR. If you know the provenance is wrong, edit the source-of-truth
document, don't just explain the discrepancy next to it.

**Round-2 confirmation — the rule generalizes past the Concrete Handles
table.** Round 2's finding was a DIFFERENT AFS section (`Known Defects Found
During Exploration` + `Expected Results`) still saying "None found" / "0
errors, 0 warnings" even though the implementation had, since round 0, been
soft-asserting a filed console-error defect (`#1203`) and declaring the spec
sanctioned-RED — the PR body / Run Report / test docstring all narrated this
accurately from round 0 onward, but nobody had edited those two AFS
sections. Same root cause as round 1, different section: **every AFS
section that states a fact the implementation later revises (handle
provenance, defects found, expected results) needs its OWN edit** — fixing
one drifted section doesn't imply the others got checked too. When a review
round flags "AFS section X wasn't amended," treat it as a cue to scan the
*whole* AFS for other stale factual claims before declaring the round done,
not just patch the one named section.

(from ELITEA-2336, round 1 + round 2 fixes)
