---
name: Sibling clone may lack git identity — commit fails but push looks fine
description: onetest-ai-tm-Elitea (and potentially other freshly-cloned siblings) can be missing user.name/user.email, so `git commit` errors ("Author identity unknown") — but if you don't notice that error and run `git push` anyway, it succeeds trivially because there's nothing new to push, silently no-op'ing your intended change.
type: feedback
---

## The trap

`elitea-testing-public` gets its git identity set explicitly by `docker-entrypoint.sh`
(`git -C "$WORK" config user.name/user.email`) on every pod start. The sibling clones
(`onetest-ai-tm-Elitea`, `EliteaUI`) do NOT get this treatment — they're cloned fresh
but never configured. The first time you try to commit in one of them in a session,
you get:

```
Author identity unknown

*** Please tell me who you are.

Run
  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"
...
fatal: unable to auto-detect email address (got 'factory@automation-factory-...')
```

**The danger isn't the error — it's what happens if you don't notice it and proceed
anyway.** If your next command is `git push origin <branch>` (especially one chained
in the same breath, or if you're scanning output quickly), the push succeeds and
prints normal-looking "branch -> branch" output — because there's nothing new to
push; the commit never happened, so the remote branch is identical to its base. A
PR opened from that branch (if you don't check) carries zero content changes.

## The fix

Before committing in ANY sibling clone for the first time in a session:

```bash
cd <sibling-clone>
git config user.name "${FACTORY_GIT_USER_NAME:-automation-factory}"
git config user.email "${FACTORY_GIT_USER_EMAIL:-automation-factory@users.noreply.github.com}"
```
(local to that repo, not `--global` — matches what the main repo's entrypoint does).

**Always verify a commit actually landed before trusting a subsequent push's output**
— `git log --oneline -3` right after `git commit`, independent of whatever the commit
command printed. If the HEAD sha didn't move, the commit silently failed (identity
gap, pre-commit hook rejection, empty diff after `git add`, etc.) and the push that
follows will look fine while doing nothing.

## Seen 1×

- #2408/ELITEA-2059/onetest-ai-tm-Elitea#167 (2026-10-15) — opening the TMS case-text
  PR, the first `git commit` in a fresh session's `onetest-ai-tm-Elitea` clone hit this
  exactly. Caught it by checking `git log --oneline -3` after the commit+push block
  (habit, not luck) and seeing the old `551df00` tip still there instead of a new sha —
  re-set identity, re-committed (this time it took), re-pushed, confirmed the new sha
  reached origin before opening the PR.
