---
name: Analyst slot has no git commit authority
description: workflow.md:159 reserves commits to "the implementer, on the work branch the lead names" — the analyst slot writes/edits the AFS file but never runs git commit/push on it, even though prior docs(afs) commits exist in git log (those were made by the lead, not inferred permission for the analyst). RECURRED once already (ELITEA-1808, 2026-07-19) after this entry existed — reading the entry is not enough, actively check it BEFORE the first `git commit` of every analyst-slot session.
type: feedback
---

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
