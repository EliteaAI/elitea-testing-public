---
name: Never amend after a failed husky commit on a shared branch
description: git commit --amend after a rejected commitlint hook silently rewrites someone else's already-pushed commit
type: feedback
---

## What happened (ELITEA-2064 session, EliteaUI `automation/testids`)

`git commit -m "test: [ELITEA-2064] add data-testid for TOOLS section '+
Pipeline' button"` **failed** — the repo's commitlint/husky `commit-msg` hook
rejected the message (subject must contain `[EL-XXXX]`, not `[ELITEA-XXXX]`).
The failure looked like an aborted commit (non-zero exit, error text), so the
natural next move was `git commit --amend -m "<fixed message>"`.

**That amend did NOT create a new commit on top of nothing — it amended the
LAST REAL commit on the branch**, which was someone else's already-pushed
testid commit (`22184211`, ELITEA-2056's "Information section Show link").
The amended commit's tree still contained ELITEA-2056's file changes (my
newly staged file was added on top), so no data was lost — but the commit
**message** now claimed to be about the Pipeline button, silently mislabeling
ELITEA-2056's work, and `git push` correctly rejected it as non-fast-forward
(caught before it reached `origin/automation/testids` — but only by luck of
the push failing, not by any check that caught the amend itself).

## Why this happens

A commit-msg hook rejecting the message still leaves the **staged index**
populated (`git add` already ran). `git commit --amend` doesn't care whether
the immediately-prior `git commit` succeeded or failed — it always amends
whatever the current `HEAD` points at, which on a shared branch that other
agents/humans have already pushed to is very likely NOT the commit you just
tried to make.

## The fix

1. **After ANY failed `git commit`, run `git log -1 --oneline` before touching
   the commit again** — confirm HEAD is still what you expect (not a stranger's
   commit you're about to swallow).
2. **Never `--amend` to "retry" a message rejected by a hook.** Fix the message
   and run a **fresh** `git commit -m "<fixed>"` instead — the index is still
   staged, so this is a normal new commit, not an amend.
3. If an amend already happened by mistake: `git diff origin/<branch> HEAD --stat`
   tells you whether the tree actually changed (safe — just a mislabeled
   commit) or something was dropped. Recover with
   `git reset --mixed origin/<branch>` (moves HEAD back, keeps your own
   uncommitted diff in the working tree), then commit cleanly.
4. This project's EliteaUI commit convention is `[EL-0000] <text> (ELITEA-<id>)`
   — NOT `[ELITEA-<id>] <text>` — check `git log --oneline -5` for the pattern
   before composing a testid commit message, so the hook doesn't reject it in
   the first place.
