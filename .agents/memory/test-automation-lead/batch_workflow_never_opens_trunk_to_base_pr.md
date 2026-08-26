---
name: batch-build never opens the trunk→base landing PR
description: The workflow's report ends at gate-green on the batch trunk; the lead always opens + merges the trunk→base PR by hand, every batch, even size 1
type: feedback
---

## Rule

`batch-build.workflow.mjs`'s report (`next` field) says to land the trunk, but
the workflow itself **never calls `gh pr create` for the trunk → base PR** — it
only merges each case PR *into the trunk* (that step IS automated: `merge:<id>`
agent + `merge-back`). The gate proving `tests/batch-<slug>` green is not the
same act as landing it.

**After every green gate, by hand:**

```bash
git fetch origin
env -u GITHUB_TOKEN gh pr create --repo <owner>/<repo> \
  --base <base branch, e.g. automation/base> --head tests/batch-<slug> \
  --title "..." --body "..."
env -u GITHUB_TOKEN gh pr merge <N> --repo <owner>/<repo> --squash --delete-branch
```

No separate lead-run gate is needed first — the workflow's gate agent already
ran N× green strictly before this point, dispatched by a party other than the
implementer, which satisfies `.agents/testing.md` § Merge gate's "not the
implementer's own work" requirement even though it isn't literally "you, the
lead" running pytest again. (A post-gate commit landing on the trunk — e.g. a
fix-only dispatch after the gate ran — is the one case that DOES need a fresh
lead-run 3× gate before opening the PR, because the gate's proof no longer
covers the trunk's current tip.)

## Seen 5×

#505/ELITEA-2068, #734/ELITEA-2227, #764/ELITEA-2257, #766/ELITEA-2259,
#779/ELITEA-2272 — every single-case batch today needed this same manual
landing step; the workflow never does it itself.

## New wrinkle: batch-stabilize's fix round can leave the trunk unpushed

#967/ELITEA-2459 (2026-08-08): after a green re-gate from
`batch-stabilize.workflow.mjs`, `git fetch origin` + `gh pr create --head
tests/batch-<slug>` used the STALE origin ref — the fix+re-gate agents had
committed the diagnosed fix on the *local* trunk checkout but never pushed it,
so the PR would have landed the pre-fix tree even though the reported gate
verdict was green. Caught by `git log --oneline origin/tests/batch-<slug>..
tests/batch-<slug>` showing 2 unpushed commits before opening the PR — pushed
them, then proceeded as normal. **Always run that diff (or `git status
-sb` after `git checkout tests/batch-<slug>`) right after a stabilize round,
before `gh pr create`** — a green re-gate verdict proves the code is right, not
that origin has it.
