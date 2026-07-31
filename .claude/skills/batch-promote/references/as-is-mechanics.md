# As-is promotion — mechanics

Concrete recipes for Mode A. Everything here was executed for real on 2026-07-31;
the traps are failures that actually happened, not hypotheticals.

---

## 1. Why a synthetic snapshot branch, and not a merge or a cherry-pick

Mode A promotes **the whole current state** of a long-lived integration branch, but
`automation/base` carries far more than the deliverable — `.claude/`, `.agents/`,
`docs/`, factory config. Three ways to get a `main`-parented branch containing only
the deliverable:

| Approach | Verdict |
|---|---|
| PR the integration branch directly | Ships `.agents/`, `.claude/`, everything. Scope is wrong. |
| Cherry-pick the relevant commits | Hundreds of commits, shared files, conflicts. That's Mode B's problem, and Mode A exists to avoid it. |
| **Build one squashed commit whose tree is `main`'s tree with chosen subtrees swapped in** | Exact scope, one reviewable diff, no conflict resolution. **Use this.** |

The result is a single commit whose parent is `origin/main` and whose tree differs
from `main` only in the promoted paths. `git diff origin/main...<branch>` is then a
precise statement of what is being promoted.

---

## 2. Building the snapshot branch

### 2a. Whole-subtree case (EliteaUI — `src/` only)

When the integration branch differs from `main` **only** inside the promoted scope,
its tree *is* the snapshot tree. Verify that first, then reuse it verbatim:

```bash
cd "$WORKSPACE/EliteaUI"
git fetch origin main --no-tags                     # see Trap 4

# The claim being tested: nothing outside src/ differs.
git diff --name-only origin/main HEAD -- . ':!src'   # MUST be empty
```

Empty ⇒ build directly from `HEAD`'s tree:

```bash
TREE=$(git rev-parse HEAD^{tree})
COMMIT=$(git commit-tree "$TREE" -p origin/main -F - <<'MSG'
test: [EL-0000] promote accumulated data-testids to main

<what changed, why, and the scope statement>
MSG
)
git branch -f testids/promote-<date> "$COMMIT"
```

Non-empty ⇒ use 2b instead; something outside the scope diverged and would ride along.

### 2b. Selected-subtrees case (tests repo — `automation/` + `test-specs/` only)

Here the integration branch legitimately differs from `main` outside the scope, so
the tree must be composed: start from `main`, strip the target paths, graft ours.

```bash
cd "$WORKSPACE/elitea-testing-public"
export GIT_INDEX_FILE=/tmp/promote-idx-$$          # scratch index; never touch the real one
rm -f "$GIT_INDEX_FILE"

git read-tree origin/main                          # index := main

# strip main's copies of the promoted paths  (see Trap 1 — do NOT use `git rm --cached`)
git ls-files -z --cached -- automation test-specs \
  | xargs -0 -n 200 git update-index --force-remove --

# graft the integration branch's copies
git ls-tree -r origin/automation/base -- automation test-specs \
  | git update-index --index-info

TREE=$(git write-tree)
unset GIT_INDEX_FILE
```

**Verify the scope before committing** — this is the check that catches a wrong graft:

```bash
git diff --name-only origin/main "$TREE" | sed 's|/.*||' | sort | uniq -c
#   73 automation
#   87 test-specs        <- ONLY the promoted prefixes may appear
```

And verify the grafted subtrees are byte-identical to the source:

```bash
for p in automation test-specs; do
  a=$(git rev-parse "$TREE:$p"); b=$(git rev-parse "origin/automation/base:$p")
  [ "$a" = "$b" ] && echo "$p identical" || echo "$p DIFFERS"
done
```

Then commit and branch as in 2a.

> **zsh gotcha:** `"$TREE:automation/..."` — zsh eats `:a` as a path modifier, silently
> mangling the path. Put the path in a variable (`P=automation/...; git show "$TREE:$P"`)
> or use a loop variable, as above.

---

## 3. Verification without a checkout (tree-SHA equivalence)

The suite must be verified against the promoted code. Checking out the promote branch
is both unnecessary and hazardous (Trap 2, and the no-worktrees policy in
`.agents/workflow.md`). Instead, **prove the promote branch and the integration branch
are the same content**, then verify on the integration branch you are already on:

```bash
# EliteaUI: whole tree (scope is all of src/, nothing else differs)
a=$(git -C "$WORKSPACE/EliteaUI" rev-parse "testids/promote-<date>^{tree}")
b=$(git -C "$WORKSPACE/EliteaUI" rev-parse "automation/testids^{tree}")
[ "$a" = "$b" ] && echo IDENTICAL

# tests repo: the promoted subtree only
a=$(git rev-parse "tests/promote-<date>:automation")
b=$(git rev-parse "origin/automation/base:automation")
[ "$a" = "$b" ] && echo IDENTICAL
```

Both identical ⇒ the dev server already running `automation/testids` is serving exactly
the promoted UI, and the suite in the working tree is exactly the promoted tests. The
run you do *is* the promote branches' verification. Nothing is checked out, nothing is
disturbed, the policy is respected.

**If they are NOT identical**, something changed after the branch was cut — rebuild it
(§2) rather than reasoning about the delta.

---

## 4. Rebuilding after a fix

Any fix landed during pre-flight or verification invalidates the snapshot. Rebuilding
is cheap — repeat §2 and force-update:

```bash
git push -f origin testids/promote-<date>
```

**Force-update is safe only while no PR is open on the branch.** Check first:

```bash
env -u GITHUB_TOKEN gh pr list --repo <repo> --head <branch> --state all --json number,state
```

Non-empty ⇒ do not force-push; push a normal commit onto the branch so the PR's review
history survives.

---

## 5. Traps (each of these actually bit)

**Trap 1 — `git rm -r --cached` silently no-ops on a scratch index.**
With `GIT_INDEX_FILE` set and no worktree context it fails quietly; `2>/dev/null` hides
it entirely. The result looks successful but the target path keeps `main`'s content, so
the promotion silently omits the work. Symptom: the scope check in §2b shows one prefix
instead of both. Use `git update-index --force-remove` and **always** re-check the count.

**Trap 2 — `skip-worktree` files block a checkout.**
`EliteaUI/vite.config.js` carries the local Support-Assistant alias and is
`skip-worktree`'d (parent `SETUP.md` § 6). Checking out another branch errors on it, and
"fixing" that by clearing the flag destroys operator-local config. The plumbing approach
(§2) never checks anything out, which sidesteps this entirely.

**Trap 3 — editing `EliteaUI/src` while a suite is running corrupts the run.**
Vite HMR pushes the edit into the browser mid-test. Any testid fix must land **before**
the verification run starts. If a fix becomes necessary during a run: kill the run, fix,
rebuild the snapshot, re-run from scratch. A partially-HMR'd run is not evidence.

**Trap 4 — a bare `git fetch origin` can hang for minutes.**
These clones sit on OneDrive with large histories. `git fetch origin main --no-tags`
returns in about a second and is all that is needed to refresh the promotion target.
Reserve the full fetch for when you genuinely need every ref.

**Trap 5 — a merge can silently drop testids.**
Always run the testid-loss guard (`sync-base-branches` § Testid-loss guard) around the
Stage-1 sync. A dropped testid surfaces days later as an unexplained red, far from its
cause. It has happened more than once, and one occurrence lost two testids from a single
file where only one was noticed at the time.
