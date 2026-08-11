---
name: Cherry-pick clean units off a broken/messy batch trunk
description: When a batch-build trunk's gate goes red because ONE unit regressed (or the trunk otherwise carries stray/broken content), don't discard the whole batch — cherry-pick the good units' specific commits onto a fresh branch off automation/base, strip anything broken, verify green, gate independently, land alone.
type: feedback
---

## The pattern, confirmed twice in one session (#1391, 2026-08-11)

A batch-build run merges several units onto a shared trunk before the final
gate; if the LAST-merged unit (or any one unit) introduces a real regression
(a referenced-but-never-pushed testid, a debug-scaffolding file, a genuinely
broken spec), the trunk's own hardening gate goes red for the WHOLE trunk —
even though the other, earlier-merged units are individually clean and
already reviewed APPROVED.

**Don't treat this as "the batch failed, redo everything."** The clean units'
work is real, committed, reviewed — only the trunk-as-a-whole is unsafe to
land as one PR.

## Recovery

1. Identify exactly which unit(s) are broken from the gate's failure
   signature + `report.json`'s per-case findings (which units got
   `outcome: blocked`/similar with a real defect, vs which show clean
   `reviewed, APPROVED, merged` with no findings).
2. `git fetch origin`, branch fresh from `origin/automation/base` (NOT from
   the messy trunk).
3. Cherry-pick per FILE, not per merge-commit, when the trunk's history is
   interleaved across units touching the same shared file (page objects
   especially) — `git show <trunk>:<path>` per file is safer than
   `git cherry-pick` across merge commits with shared-file conflicts. Strip
   anything the broken unit added that the clean units don't actually use
   (check with `grep`/`git diff --stat` before assuming a shared-file change
   is safe to carry).
4. Run your own mechanical grep + gate on the cherry-picked branch — don't
   assume "it was clean on the trunk" transfers; re-verify from scratch,
   because the cherry-pick itself can introduce new issues (e.g. a dispatched
   implementer's self-reported grep only checking `automation/pages/`, missing
   real violations in the test file itself — caught by the LEAD's own grep,
   not the implementer's).
5. Land the salvaged branch as its own small PR; leave the broken unit(s) and
   the messy trunk's remainder as documented follow-up work (a status comment
   naming exactly what's still needed), not silently dropped.

## Confirmed instances

- ELITEA-2359 alone, off a trunk whose 3rd unit (2360) had a genuine
  navigation-timeout blocker and carried debug scaffolding.
- ELITEA-2366+2367 together, off a trunk whose 3rd unit (2370) referenced a
  testid never actually pushed to EliteaUI — stripped that unit's
  unused/non-compliant page-object addition, which a SECOND fix-only dispatch
  had to further clean (own grep on the FULL diff, not just `automation/pages/`,
  found 4 more violations the cherry-pick's own author's self-check missed).
