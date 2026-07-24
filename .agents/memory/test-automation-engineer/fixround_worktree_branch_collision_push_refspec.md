---
name: fixround_worktree_branch_collision_push_refspec
description: A fix-round dispatch into a fresh isolated worktree can't checkout the PR's own branch name if it's already checked out in a sibling worktree — branch under a fixround/ name tracking origin's PR branch, then push with an explicit refspec back to the PR branch name
type: feedback
---

**Symptom.** Dispatched as an implementer fix-round for an existing PR, told
to work "on branch `tests/<CASE-ID>-<slug>`" — but `git checkout
tests/<CASE-ID>-<slug>` fails: `fatal: '<branch>' is already used by worktree
at '<path-to-some-other-worktree>'`. Git worktrees are one-branch-one-checkout;
a prior/parallel worktree still has that exact branch name checked out.

**Fix — branch under a different local name, push back to the real one:**

```bash
git fetch origin
git checkout -b fixround/<CASE-ID>-review-r1 origin/tests/<CASE-ID>-<slug>
# ... make the fix-round commits on this local branch ...

# immediately before pushing, re-fetch and confirm the remote hasn't moved
# (no other worktree/session pushed to the PR branch while you worked)
git fetch origin tests/<CASE-ID>-<slug>
git log --oneline -3 origin/tests/<CASE-ID>-<slug>   # should match what you branched from

# push with an EXPLICIT refspec — local-branch-name : remote-branch-name —
# NOT a bare `git push` (which would try to create/push a NEW remote branch
# named `fixround/<CASE-ID>-review-r1`, not update the PR's actual branch)
git push origin fixround/<CASE-ID>-review-r1:tests/<CASE-ID>-<slug>
```

This lands as a fast-forward onto the existing PR branch (same effect as if
you'd committed directly on `tests/<CASE-ID>-<slug>`), so the existing PR
(e.g. via `gh pr view <PR-URL>`) picks up the new commit automatically — no
new PR needed, no `--force` needed, as long as the remote genuinely didn't
move (checked by the immediately-prior fetch).

**Why this matters:** in a factory doing parallel batch work, a case's PR
branch is very often still checked out in the analyst's or the original
implementer's now-idle worktree at fix-round time. Don't ask the orchestrator
to free it up — branch-and-refspec-push is strictly local, costs nothing, and
leaves every other worktree untouched.

**Companion gotcha in the same isolated-worktree setup:** `automation/.env.test`
is a symlink (`../../.env.test` in the main checkout) that resolves relative
to the checkout's OWN depth — a worktree nested under
`.claude/worktrees/<name>/` sits several directories deeper, so the same
relative symlink target is wrong/missing there. Recreate it pointing at the
TRUE workspace root's `.env.test` (find the root by walking up until you see
the sibling `EliteaUI/`, `onetest-ai-tm-Elitea/` folders) — it's gitignored
(`**/.env*`) so this is a pure local fix, never a tracked change:
```bash
ln -s "<true-workspace-root>/.env.test" automation/.env.test
```
Likewise `.venv/bin/pytest`'s shebang is a copied venv's absolute path back to
the MAIN checkout's `.venv/bin/python3.13` (not this worktree's own copy) —
that's fine and expected as long as the main checkout's venv still exists at
that path; no action needed, just don't be surprised the interpreter path in
`pytest -v`'s banner points at the main checkout, not the worktree.
