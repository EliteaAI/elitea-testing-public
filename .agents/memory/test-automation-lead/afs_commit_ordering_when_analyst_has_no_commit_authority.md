---
name: AFS commit ordering when analyst has no commit authority
description: when a standalone-dispatched analyst leaves the AFS uncommitted, commit it in its own commit on the feature branch — keep agent-memory-landing commits separate, on automation/base directly, not mixed into the AFS commit
type: feedback
---

Analyst dispatches in this project don't carry explicit commit authority for a
standalone session (workflow.md only names commit authority for the
implementer). When the analyst's final message says the AFS was "left
uncommitted... for the orchestrator/lead to commit," that's expected, not a
gap to chase.

Sequence that worked cleanly (ELITEA-1884, issue #76):
1. `git checkout automation/base`, pull fresh.
2. Cut the feature branch (`tests/<CASE>-<slug>`) from `automation/base`.
3. `git add` ONLY the AFS file, commit it alone (`docs(afs): add AFS for
   <CASE> ...`) on the feature branch.
4. Switch back to `automation/base`, commit the analyst's (and your own)
   agent-memory changes there directly (`chore: land agent memory (...)`),
   push `automation/base`.
5. Rebase the feature branch on the now-updated `automation/base` (short-lived
   unpushed feature branch — rebasing it is fine, unlike the two shared
   long-lived branches which must only ever be merged).
6. Push the feature branch, dispatch the implementer.

Why bother separating: the AFS commit is a deliverable that belongs in the
case's PR history (implementer's diff extends the same branch); agent-memory
files are a housekeeping side-channel that belongs directly on `automation/base`
regardless of which case is in flight, and mixing them into the case's feature
branch would surface as unrelated noise in the eventual PR diff.
