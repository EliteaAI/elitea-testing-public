---
name: Verify feature branch before first commit
description: A batch dispatch's tree starts checked out ON the batch trunk name — check `git branch --show-current` and cut your OWN branch before committing anything, even though the prompt already told you to.
type: feedback
---

## What happened (2026-08-02, ELITEA-1828/1829/1831, batch wave-01 artifacts-upload-dup unit)

The dispatch prompt said "The tree is on `tests/batch-wave-01-heads_...` and
that is where you start. Cut your feature branch FROM it." I read the AFS,
implemented the three specs, ran them green, then went straight to
`git add` / `git commit` / `git push` — without first running
`git checkout -b <feature-branch>`. Because the tree was ALREADY checked out
on the trunk's own branch name when the dispatch started, my commit landed
directly on the trunk, and my push sent it straight to `origin/<trunk>` with
no PR in between.

By the time I noticed (right before opening the PR) it was too late to fix
non-destructively: creating a feature branch retroactively at the same
commit just gives two refs pointing at the identical commit, and
`gh pr create --base <trunk> --head <feature>` fails outright:
`GraphQL: No commits between <trunk> and <feature>` — GitHub has nothing to
diff. The only real fix is moving the trunk ref back one commit, which is a
force-push (`git push --force` or an equivalent history rewrite of a branch
other units may already be building on) — outside an implementer's authority
without explicit operator request, per the Git Safety Protocol.

## The fix — do this FIRST, unconditionally, on every dispatch

Before the first `git commit` of any implementer/batch-unit session:

```bash
git branch --show-current
```

If the answer is the batch trunk name itself (`tests/batch-...`) or
`automation/base` — **not** a case-scoped feature branch — stop and cut one
NOW, before touching git any further:

```bash
git checkout -b tests/<case-id(s)>-<slug>
```

Only commit after this returns a name that is clearly YOUR branch, not the
trunk's. The dispatch prompt telling you "cut your branch from X" is an
instruction to execute, not a description of a state that already holds.

## Why this is a dead end, not just an ugly one

Once the trunk and a feature branch share a tip, there is no non-destructive
path back to a reviewable PR — `gh pr create` refuses (empty diff), and
correcting it needs a force-push nobody but the human/orchestrator can
authorize. Catching it BEFORE the first commit costs one command; catching
it after costs a blocked PR and an escalation.
