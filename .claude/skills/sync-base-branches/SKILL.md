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
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE"
# Both repos must be FULL clones. A shallow clone has no merge base: rebase misbehaves
# and rev-list reports nonsense ahead/behind counts.
for d in elitea-testing-public EliteaUI; do
  test -f "$d/.git/shallow" && echo "SHALLOW: $d — run: git -C $d fetch --unshallow origin"
done
git -C elitea-testing-public status --porcelain
git -C EliteaUI status --porcelain
```

### Step 0 — Land the working tree before syncing

Never merge or rebase over uncommitted work: if it conflicts, your changes get tangled into the
resolution. But a dirty tree is **normal** here — agents accumulate memories and specs as they go. Do
not dead-stop on it. Classify what's there and land it:

**Commit** (these are deliverables):
- `.agents/**` — agent memories, briefings, daily logs, seeded config
- `.claude/skills/**`, `.claude/rules/**`, `CLAUDE.md`, `AGENTS.md`
- `test-specs/**` — test specs are part of the deliverable
- `automation/**` — tests, page objects, fixtures
- Test *data* a test genuinely needs (e.g. an example attachment to upload)

**Leave untracked** (strays — do not commit, do not delete; a human reviews them periodically):
- Screenshots and Playwright-MCP leftovers (`*.png` at the repo root, trace dumps)
- Scratch files, one-off debug output

**Never commit:** `.env`, `.env.test`, `.claude/settings.local.json`, or any file containing a token,
password, or key. (They are gitignored — keep it that way.)

### Step 0b — Secret scan. This repo is PUBLIC.

`elitea-testing-public` is a public repository, and `.env.test` holds a live API token, a test-user
password, a GitHub PAT, and a Jira key. Before committing, verify none of those **values** appear in
what you are about to push — an agent memory or a test spec can easily quote one by accident.

```bash
git add <the deliverables>
python3 scripts/scan-secrets.py        # exit 0 = clean, 1 = leak found
```

A non-zero exit means **stop and do not push** — remove the value, and rotate the credential, because
if it reached a commit it must be assumed compromised. Public URLs (`localhost:5173`, `dev.elitea.ai`)
are not secrets; tokens, passwords, keys, and the test-user credentials are.

The scanner reads the real values out of `.env.test` and greps staged files for them, so it catches a
pasted token even when it is not in an obvious `KEY=value` shape. Confirm it is actually working with
`python3 scripts/scan-secrets.py --selftest` (it plants a real secret in a temp file and asserts it
catches it) — a scanner that silently passes everything is worse than no scanner at all.

Then commit, and only then proceed to Part 1.

## Part 1 — Test repo: merge `origin/main` into `automation/base`

```bash
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE/elitea-testing-public"
git fetch origin
git checkout automation/base
git merge origin/main
```

On conflict: resolve, `git add`, `git merge --continue`. Conflicts here are usually two tests touching
the same page object — keep both locators.

**Then check what you just pulled in.** `main` carries framework changes, not just tests — a merge can
alter `config.py`, `conftest.py`, `api/client.py`, or fixtures, and a new *required* config field will
break every test at import time before a single one runs.

```bash
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE/elitea-testing-public"
git diff ORIG_HEAD..HEAD --stat -- automation/config.py automation/conftest.py automation/fixtures automation/api

# Did config.py gain a setting? If it has no default, .env.test needs a new key.
git diff ORIG_HEAD..HEAD -- automation/config.py | grep -E '^\+\s+\w+:' || echo "  no new settings"

# The suite must still import and collect. This is the real check.
cd automation
../.venv/bin/python -c "from config import settings; from api.client import APIClient; print('imports OK')"
../.venv/bin/pytest tests/ui/smoke/ --collect-only -q -p no:cacheprovider 2>&1 | tail -2
```

If a new setting has a default (e.g. `cf_ext_rate: str = ""`), it is optional — nothing to do. If it has
no default, add the key to `.env.test` **and tell the human**, because every teammate's `.env.test`
needs it too.

```bash
git push origin automation/base      # plain push. If this needs --force, STOP: something is wrong.
```

## Part 2 — UI fork: rebase `automation/testids` onto `upstream/main`

**GUARD — read before force-pushing.** The force-push below rewrites a shared branch. If a teammate or
another agent has commits on `automation/testids` that you don't have locally, `--force-with-lease` will
refuse — that refusal is correct, do not override it with `--force`. Announce the sync, make sure nobody
is mid-commit, and never run this while another agent is adding testids.

```bash
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE/EliteaUI"
git fetch upstream
git fetch origin

# 0. Look at what you are about to replay, and what is coming in.
git log --oneline upstream/main..automation/testids     # ours — should be testid commits only
git log --oneline automation/testids..upstream/main     # theirs — what lands on top

# Our commits must be strictly additive. Any non-testid line is a red flag: report it, do not rebase
# it into a batch that will be PR'd to another team's repo.
git diff upstream/main...automation/testids --stat
git diff upstream/main...automation/testids | grep -E '^[+-]' | grep -v '^[+-][+-]' | grep -vc 'data-testid'
#   ^ expect 0. Non-zero = someone slipped a behaviour change onto the testid branch.

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

**Confirm the replay did not lose anything.** A rebase can silently drop an edit through a careless
conflict resolution, and the branch will look perfectly healthy afterwards.

```bash
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE/EliteaUI"

# Our testids must still be there, and the diff must still be additive-only.
git diff upstream/main...automation/testids --stat
git diff upstream/main...automation/testids | grep -o 'data-testid="[^"]*"' | sort -u

# Dependencies: a bare "version" bump in package.json does NOT need a reinstall.
git diff ORIG_HEAD..HEAD --name-only -- package-lock.json
```

If `package-lock.json` appears, run `npm install`.

Restart the dev server so it serves the new code — HMR does not survive a rebase:

```bash
pkill -f vite
# then use the start-ui-localhost skill
```

### Check what upstream just gave you for free

**The EliteaUI team adds `data-testid` attributes too** (e.g. PR #513, EL-5634). A sync can therefore
*remove* work you were about to do — an element you planned to instrument may already be covered.

```bash
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE/EliteaUI"
# Total testids the local UI now serves (upstream's + ours):
git grep -ho 'data-testid="[^"]*"' HEAD -- 'src/*' | sed 's/data-testid=//;s/"//g' | sort -u | wc -l

# Did UPSTREAM merge any testid work in this fetch? Use the remote-tracking reflog —
# NOT `ORIG_HEAD..HEAD`, which after a rebase also lists our own replayed commits and misleads you.
git log --oneline 'upstream/main@{1}..upstream/main' --grep='test-id\|testid\|test id' -i
```

You do not need a "does this testid already exist" guard before calling `add-data-testid`: agents
discover elements by snapshotting the **live DOM**, which after a sync already contains upstream's
testids, so a covered element never reaches the skill. But if you sync mid-task, re-snapshot — an
element that lacked a testid ten minutes ago may have one now.

## Verify before you report

Branch counts alone are not verification — they prove git moved, not that anything still works. You
pulled in real framework changes and real UI changes; run the smoke suite against the restarted local UI.

```bash
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"

# 1. Both branches level with their bases (left = behind, must be 0; right = our commits, fine)
git -C "$WORKSPACE/elitea-testing-public" rev-list --left-right --count origin/main...automation/base
git -C "$WORKSPACE/EliteaUI"              rev-list --left-right --count upstream/main...automation/testids

# 2. The UI still serves (dev server restarted after the rebase)
curl -s -o /dev/null -w "localhost:5173 -> %{http_code}\n" http://localhost:5173

# 3. The suite still passes against it. This is the real check.
cd "$WORKSPACE/elitea-testing-public/automation"
HEADLESS=true ../.venv/bin/pytest tests/ui/smoke/ -v -p no:cacheprovider
```

Report the actual numbers and the actual pass/fail line. Do not claim success without running these —
a green sync with a broken UI is the failure mode this catches.

## Do not

- Rebase or force-push `automation/base`. Ever.
- Commit anything to the fork's `main`. It is a mirror of upstream, nothing else.
- Use bare `--force`. `--force-with-lease` refusing is a signal, not an obstacle.
- Sync while another agent has uncommitted testid work.
- Dead-stop on a dirty tree. Classify it (Step 0), commit the deliverables, leave the strays.
- Push to this public repo without running the secret scan (Step 0b).
- Report success from branch counts alone — the suite must still import and collect.
