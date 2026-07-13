---
name: sync-base-branches
description: Brings the two long-lived automation branches up to date with their mains — automation/base with elitea-testing-public main (merge), and the EliteaUI fork's automation/testids with upstream main (rebase). Use before starting a new test, after a batch promotion, or when a test fails against unexpectedly-changed UI.
allowed-tools:
  - Bash
  - Read
---

# Sync Base Branches

Two long-lived branches drift from their mains. This brings both current. Run it **before starting a
new test**, **after a batch promotion**, or when a test fails against UI that looks unexpectedly changed.

| Branch | Repo | Base it tracks | Strategy |
|---|---|---|---|
| `automation/base` | `elitea-testing-public` | `origin/main` | **merge** |
| `automation/testids` | `EliteaUI` (fork) | `upstream/main` | **rebase** |

**The strategies differ and are not interchangeable.**

`automation/base` is shared and published — the whole team opens PRs into it. Rebasing it would rewrite
published history and break every open PR and every teammate's clone. **Merge it. Never rebase it. Never
force-push it.**

`automation/testids` is rebased so that testid commits stay a clean, replayable stack on top of upstream —
that's what makes the eventual batched PR reviewable. Rebasing rewrites history, so it **requires a
force-push**. See the guard below.

## Preconditions

```bash
cd "$LOCAL_ELITEA_FOLDER"
# Both repos must be FULL clones. A shallow clone has no merge base: rebase misbehaves
# and rev-list reports nonsense ahead/behind counts.
for d in elitea-testing-public EliteaUI; do
  test -f "$d/.git/shallow" && echo "SHALLOW: $d — run: git -C $d fetch --unshallow origin"
done
# Both trees must be clean. Stop if not — never sync over uncommitted work.
git -C elitea-testing-public status --porcelain
git -C EliteaUI status --porcelain
```

## Part 1 — Test repo: merge `origin/main` into `automation/base`

```bash
cd "$LOCAL_ELITEA_FOLDER/elitea-testing-public"
git fetch origin
git checkout automation/base
git merge origin/main
```

On conflict: resolve, `git add`, `git merge --continue`. Conflicts here are usually two tests touching
the same page object — keep both locators. Then:

```bash
git push origin automation/base      # plain push. If this needs --force, STOP: something is wrong.
```

## Part 2 — UI fork: rebase `automation/testids` onto `upstream/main`

**GUARD — read before force-pushing.** The force-push below rewrites a shared branch. If a teammate or
another agent has commits on `automation/testids` that you don't have locally, `--force-with-lease` will
refuse — that refusal is correct, do not override it with `--force`. Announce the sync, make sure nobody
is mid-commit, and never run this while another agent is adding testids.

```bash
cd "$LOCAL_ELITEA_FOLDER/EliteaUI"
git fetch upstream
git fetch origin

# 1. Fast-forward the fork's own main to upstream. Never commit to this branch.
git checkout main
git merge --ff-only upstream/main
git push origin main

# 2. Replay our testid commits on top of the new upstream head.
git checkout automation/testids
git rebase upstream/main
```

On conflict: testid edits are additive JSX attributes, so a conflict almost always means upstream
edited the same JSX line. Keep upstream's version of the line **and** re-add our `data-testid`
attribute. Then `git add <file>` and `git rebase --continue`.

If the rebase goes wrong at any point, `git rebase --abort` returns you to safety. Nothing is lost.

```bash
# 3. Publish the rewritten branch. --force-with-lease, never bare --force.
git push --force-with-lease origin automation/testids
```

### If a batch PR to EliteaAI/EliteaUI is currently open

**Sync anyway — an open PR does not block catching up.** Our testid commits simply replay on top of the
newer upstream head, so agents keep working against a current UI while EliteaUI reviews at their own pace.

Two things to keep straight:

- **Do not touch the PR's frozen snapshot branch** (`chore/testids-batch-<date>`). It is deliberately
  frozen so the diff reviewers see stays stable. Rebasing `automation/testids` does not affect it; the
  two will hold the same edits under different SHAs, which is expected. The *only* reason to touch the
  snapshot branch is if GitHub marks the PR conflicted because upstream changed a line our testids sit
  on — then rebase that branch onto `upstream/main` and force-push it. Ordinary PR hygiene.
- **Do not open a second upstream PR.** One batch PR in flight at a time. New testids keep accumulating
  on `automation/testids` and ship in the *next* batch. A second snapshot cut now would still contain
  the first batch's commits (they are not in `upstream/main` yet), so the two PRs would overlap.

### After a batch PR merges upstream — use an explicit boundary

Do **not** assume the plain rebase drops the promoted commits. It does only if EliteaUI used a merge or
rebase merge. **If they squash-merged**, our N testid commits became one upstream commit with a
different patch identity, git will not recognize them as already applied, and it will try to replay all
N — each re-adding a `data-testid` that already exists, producing a pile of pointless conflicts.

This form is correct under merge, squash, *and* rebase — replay only what came after the promoted batch:

```bash
git fetch upstream
# BOUNDARY = tip of the snapshot branch that was just merged (record this SHA when you open the PR)
git rebase --onto upstream/main <BOUNDARY> automation/testids
git push --force-with-lease origin automation/testids
```

If `automation/testids` ends up with no commits ahead of `upstream/main`, that is success — the batch
landed completely. Then delete the merged snapshot branch:
`git push origin --delete chore/testids-batch-<date>`.

## Part 3 — Post-sync

```bash
cd "$LOCAL_ELITEA_FOLDER/EliteaUI"
# Did dependencies actually change? A bare "version" bump in package.json does NOT need a reinstall.
git diff ORIG_HEAD..HEAD --name-only -- package-lock.json
```

If `package-lock.json` appears, run `npm install`.

Restart the dev server so it serves the new code — HMR does not survive a rebase:

```bash
pkill -f vite
# then use the start-ui-localhost skill
```

## Verify before you report

```bash
git -C "$LOCAL_ELITEA_FOLDER/elitea-testing-public" rev-list --left-right --count origin/main...automation/base
git -C "$LOCAL_ELITEA_FOLDER/EliteaUI"              rev-list --left-right --count upstream/main...automation/testids
```

Left number = commits you are behind and should now be `0` in both. Right = our own commits ahead, which
is expected and fine. Report the actual numbers; do not claim success without running this.

## Do not

- Rebase or force-push `automation/base`. Ever.
- Commit anything to the fork's `main`. It is a mirror of upstream, nothing else.
- Use bare `--force`. `--force-with-lease` refusing is a signal, not an obstacle.
- Sync while another agent has uncommitted testid work.
