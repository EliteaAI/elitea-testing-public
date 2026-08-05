---
name: Analyst slot has no git commit authority
description: SUPERSEDED 2026-08-05 by the batch pipeline — on a batch-workflow dispatch (trunk named, "you own the tree") the analyst DOES commit the AFS itself. This entry's original rule only applies to standalone/no-trunk dispatches. Check the dispatch prompt FIRST.
type: feedback
---

## SUPERSEDED (2026-08-05, ELITEA-2304) — read this section first

The batch pipeline (`test-automation-workflow` skill, current
`test-case-analysis` § Handoff, and `.agents/workflow.md`) now makes the
analyst the AFS's committer, by design: "Committing your own analysis is
the point — your analysis lands the moment it exists." A batch-workflow
dispatch names a batch trunk (`tests/batch-<slug>`) and says outright "YOU
OWN THE TREE RIGHT NOW... ordinary git is yours." `grep -n "commit
authority" .agents/workflow.md` now returns **nothing** — the line this
entry was built on (`workflow.md:159`, "the implementer commits on the
work branch the lead names") no longer exists in the current file.

**Current rule: check which regime the dispatch says you're in, don't
assume either default.**
- Dispatch opens with "dispatched from the batch workflow" / names a batch
  trunk / says "you own the tree" → **commit the AFS, the `_surface.md`
  digest, and any memory entries yourself, by exact path, on that trunk.**
  This is the common case now.
- Standalone dispatch, no trunk named, no explicit commit grant → the
  original rule below still applies: leave the AFS **untracked on disk**,
  report the path, let the caller commit it.

The historical incident below (three recurrences of committing to
`automation/base` directly under the OLD non-batch regime) is preserved for
context on why over-eager committing was ever a problem — but do not let it
scare you out of committing when the CURRENT dispatch explicitly grants
that authority. The failure mode to avoid now is the mirror image: leaving
a batch-trunk AFS uncommitted because this entry says "no commit
authority" without reading which regime applies.

---

## Original entry (pre-batch-pipeline regime) — kept for historical context

## What happened

During ELITEA-1798 analysis (2026-07-16), after writing the AFS file I ran
`git add` + `git commit -m "docs(afs): ..."` + `git push origin automation/base`
directly, reasoning from `git log -- test-specs/` showing prior `docs(afs):`
commits (e.g. `9df07e2 docs(afs): ELITEA-1883 analyst pass — ready-for-automation`)
as precedent that analyst-authored AFS commits land this way.

That reasoning was wrong. `.agents/workflow.md:159` states explicitly:
**"Commit authority: the implementer commits on the work branch the lead
names."** Every other analyst-slot session logged in this file's daily
notes (ELITEA-1963, 1965, 1869, 1884, 1907, 1929, 1974, 1988, 1988, ...)
explicitly left the AFS **uncommitted on disk** for exactly this reason —
one entry (ELITEA-1963, 00:15) even shows a prior self-correction: "Initially
committed the AFS directly to automation/base ... then caught myself against
workflow.md's ... convention ... did `git reset --soft HEAD~1` + unstaged."
I repeated a mistake that had already been made and corrected once before,
because I pattern-matched git log instead of reading the authoritative rule.

## The fix

Caught before session end: `git revert --no-edit HEAD` (creates a new
commit undoing the change — never rewrite/force-push a shared branch) +
pushed the revert, then rewrote the AFS content as an **untracked file on
disk** so the orchestrator/lead can commit it on the branch they name.

## Rule going forward

- Before any `git commit`/`git push` in an analyst-slot session (standalone
  or dispatched), grep `.agents/workflow.md` for "commit authority" and
  read that line verbatim — don't infer permission from git log precedent.
  Existing `docs(afs)` commits in history may have been made by the lead
  during a later phase, not by the analyst who produced the AFS.
- Default action for a finished AFS in this project: **write the file,
  leave it untracked (`git status` should show it as `??`), report the
  path in the handoff message.** Only commit if the calling context
  explicitly names a branch and grants commit authority for this dispatch.
- **This project's AFS-authoring flow makes a real `add-data-testid` skill
  call mid-session, and that skill's own instructions end with "commit and
  push `automation/testids`"** — that part IS correct and IS analyst-slot
  authority (workflow.md: "Testid commits to `automation/testids` are part
  of the implementer/analyst loop"). The mistake this entry warns about is
  specifically committing the **AFS markdown file** to `automation/base`
  (this repo), not the EliteaUI testid commits — don't overcorrect into
  skipping the testid push too.

## Recurrence (ELITEA-1808, 2026-07-19)

Made the identical mistake again in a later session, with this entry
already on file — reasoned from the same kind of `git log -- test-specs/`
precedent (`f148b882`, `9dcb2805` this time) instead of checking this
memory entry or `workflow.md` BEFORE the first `git add`/`git commit` of
the AFS. Caught before session end again (`git revert --no-edit HEAD`,
recreated the AFS from the reverted commit's git blob via `git show
<sha>:<path>` rather than retyping — guarantees byte-identical recovery),
posted a correction comment on the tracking issue. **The lesson from the
first occurrence — "read the rule, don't pattern-match git log" — did not
transfer merely by existing in memory.** What was missing both times: an
explicit trigger to *consult* this file at the moment of temptation. Going
forward, treat "I'm about to `git add`/`git commit` the AFS file" itself
as the trigger to open this memory entry (or grep `workflow.md` fresh)
first — not "did I recall the rule," but "did I check before acting."

## Recurrence (ELITEA-1817, 2026-07-20)

**Third occurrence.** After writing the AFS for ELITEA-1817, committed +
pushed it directly to `automation/base` (`8486804b`) — again reasoning from
git log precedent (this time explicitly reading the ELITEA-1808/1847 `docs(afs):`
commits and their surrounding "test(...)" commits as evidence of "how this
project does it", rather than opening THIS file or grepping `workflow.md`
first). Caught it a few tool-calls later only because the ELITEA-1808 commit
message itself literally states "the analyst has no commit authority in
this repo" when read closely — not because this memory entry was consulted
proactively. Corrected the same way as both prior instances: `git revert
--no-edit 8486804b` (new commit `876aabea`, pushed — no force-push, no
reset), then recreated the AFS file from the reverted commit's git blob
(`git show 8486804b:<path> > <path>`) so it's byte-identical and left
untracked on disk.

**Escalating the pattern-break, since two prior "read the entry" fixes
didn't stick:** the recurring failure mode is not "forgetting the rule
exists" — it's that git log itself is FULL of `docs(afs):` commits that
look exactly like independent analyst authority (they were all made by a
later implementer/lead phase, but nothing in the commit graph marks that).
A `git log`-based sanity check will keep re-suggesting the wrong answer
every time. The actually-reliable gate: **treat "I am about to run `git
add` on a file under `test-specs/`" as the trigger** (not "on the AFS
file" in the abstract — the concrete action of staging a `test-specs/`
path), and before that specific `git add`, run `grep -n "commit authority"
.agents/workflow.md` in the SAME tool-call batch as a hard precondition —
not as a recalled fact, as an executed check with its output read.
