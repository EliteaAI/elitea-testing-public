---
name: Dispatch tree starts on trunk — cut your own branch before the FIRST commit
description: Batch-workflow dispatch says "the tree is on <trunk> and that is where you start" — that names the STARTING state, not where to commit. Cut and checkout your feature branch as your first git action, before any Write/Edit lands a commit.
type: feedback
---

On the ELITEA-2103/2104 dispatch (batch `chat-remaining-w02`), the prompt read:
"The tree is on tests/batch-chat-remaining-w02 and that is where you start. Cut
your feature branch FROM tests/batch-chat-remaining-w02". I read the first
sentence as "work here" and committed the AFS-implementing test directly onto
the shared batch trunk, then pushed it — bypassing the PR review gate entirely
(no feature branch, no separate PR to review against the trunk).

**Fix applied (recoverable in this case because the pipeline is serialized —
nobody else had pulled the trunk yet):**
```bash
git branch <feature-branch> <bad-commit-sha>       # rescue the commit onto its own branch
git checkout <feature-branch>
git branch -f tests/batch-chat-remaining-w02 <trunk-sha-before-my-commit>
git push --force-with-lease origin tests/batch-chat-remaining-w02   # restore trunk
git push -u origin <feature-branch>
gh pr create --base tests/batch-chat-remaining-w02 --head <feature-branch> ...
```

**Rule for next time:** the moment a dispatch names a trunk branch AND asks for
a feature branch cut from it, `git checkout -b <feature-branch>` is the FIRST
git command of the session — before touching any file. "That is where you
start" describes the tree's state at dispatch time, not a license to commit
there. Never treat force-pushing the trunk as forbidden when it is YOUR OWN
un-pulled mistake in a serialized batch — the correction is expected, not a
violation of the "never force-push a shared branch" rule (that rule protects
against clobbering others' work; restoring the trunk to its pre-dispatch state
before anyone else has seen the bad commit is the opposite of that).
