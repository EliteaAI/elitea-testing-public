---
name: sync-base-branches
description: Brings the two long-lived automation branches up to date with their mains — automation/base with elitea-testing-public main, and EliteaAI/EliteaUI's automation/testids integration branch with its main. Both by merge; neither is ever rebased or force-pushed. Use before starting a new test, after a promotion, or when a test fails against unexpectedly-changed UI.
allowed-tools:
  - Bash
  - Read
---

# Sync Base Branches

Two long-lived branches drift from their mains. This brings both current. Run it **before starting a
new test**, **after a batch promotion**, or when a test fails against UI that looks unexpectedly changed.

| Branch | Repo | Base it tracks | Strategy |
|---|---|---|---|
| `automation/base` | `EliteaAI/elitea-testing-public` | `origin/main` | **merge** |
| `automation/testids` | `EliteaAI/EliteaUI` (no fork) | `origin/main` | **merge** |

**Both are merged. Neither is ever rebased or force-pushed.**

Both are shared, published branches that other people and other agents build on. Rebasing either would
rewrite published history and break open PRs and teammates' clones. `automation/testids` additionally
lives on an org repo we have push — but *not* admin — on. **Merge them. Never rebase. Never force-push.**

> Changed 2026-07-13: `automation/testids` used to live on a personal fork and was *rebased* onto upstream
> so a batched promotion PR would stay reviewable. The fork is retired and testids now promote **per case**
> via draft PRs cut from `main`, so the rebase — and all the squash-boundary machinery it needed — is gone.

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

## Part 2 — UI: merge `origin/main` into `automation/testids`

`automation/testids` is a **permanent integration branch on `EliteaAI/EliteaUI`** (there is no fork).
It accumulates every testid the team ever wrote — the ones already merged to `main` **and** the ones
still sitting in draft review PRs. The local dev server runs it, so agents never wait on the UI team.

**Merge. Never rebase. Never force-push.** It is a shared branch on an org repo we do not own; rewriting
its history can clobber a colleague. There is **no legitimate use** of `--force` or `--force-with-lease`
on it. If a push is rejected, you are behind — pull and merge, never force.

Because we merge rather than rebase, the old squash/boundary machinery is gone: once a testid reaches
`main`, merging `main` in simply carries it, and the copy already on the branch is recognised as the same
content. Nothing to replay, nothing to drop.

```bash
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE/EliteaUI"

git fetch origin
git checkout automation/testids

# What is ours (testids not yet merged to main) vs what main has for us:
git log --oneline origin/main..automation/testids
git log --oneline automation/testids..origin/main

# Our diff vs main must be strictly additive testids. Any non-testid line is a red flag:
# report it, do NOT merge over it.
git diff origin/main...automation/testids --stat
git diff origin/main...automation/testids | grep -E '^[+-]' | grep -v '^[+-][+-]' | grep -vc 'data-testid'

git merge origin/main
git push origin automation/testids     # plain FF push. If this wants --force, STOP.
```

### Conflicts

Testid edits are additive JSX attributes, so a conflict almost always means the UI team edited the same
JSX line. Keep **main's** version of the line and re-add our `data-testid` attribute. Then
`git add <file>` && `git merge --continue`. `git merge --abort` returns you to safety at any point.

**Divergence rule — the one case that needs judgement.** If the UI team *changed* a testid during review
(renamed it, moved it to another element) before merging our draft PR, then `main` now disagrees with the
copy on `automation/testids`. **Resolve in favour of `main` — it is the source of truth.** Then update the
matching `LocatorDescriptor` in `elitea-testing-public`, and re-run the affected tests. This is inherent
to the dual-target design, not a bug. Report it to the human; the tests it touches will fail loudly
otherwise.

### Restart the dev server

```bash
# HMR does not survive a branch-level merge — restart so it serves the merged code.
pkill -f "vite" ; (cd "$WORKSPACE/EliteaUI" && npm run dev &)
```

If `package.json` / `package-lock.json` changed in what main gave you → re-run `npm install` first (a
bare version bump does not require it).

### Check what main just gave you for free

The UI team adds their own testids. After a sync the local UI may already expose an element you were
about to hand to `add-data-testid`.

```bash
cd "$WORKSPACE/EliteaUI"
# Total testids the local UI now serves (theirs + ours):
grep -roh 'data-testid="[^"]*"' src/ | sort -u | wc -l
# What main added since the last sync:
git log --oneline 'origin/main@{1}..origin/main' --grep='test-id\|testid\|test id' -i
```

### Open draft PRs — nothing to do here

Testid promotion is **per-case and continuous**: each testid commit is born on `automation/testids`,
cherry-picked onto its `testids/<case>` branch (built on fresh `main`), and opened as its own draft PR
to `main`. Those PRs are independent of this sync — you do
not rebase them, do not batch them, and do not need "one in flight at a time". Merging `main` into
`automation/testids` does not touch them.

If GitHub marks one **conflicted** because `main` moved under it, that is ordinary PR hygiene: rebase that
`testids/<case>` branch onto `origin/main` and force-push **it** (a short-lived single-case branch — force
is fine *there*, never on `automation/testids`).


You do not need a "does this testid already exist" guard before calling `add-data-testid`: agents
discover elements by snapshotting the **live DOM**, which after a sync already contains the UI team's
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
git -C "$WORKSPACE/EliteaUI"              rev-list --left-right --count origin/main...automation/testids

# 2. The UI still serves (dev server restarted after the merge)
curl -s -o /dev/null -w "localhost:5173 -> %{http_code}\n" http://localhost:5173

# 3. The suite still passes against it. This is the real check.
cd "$WORKSPACE/elitea-testing-public/automation"
HEADLESS=true ../.venv/bin/pytest tests/ui/smoke/ -v -p no:cacheprovider
```

Report the actual numbers and the actual pass/fail line. Do not claim success without running these —
a green sync with a broken UI is the failure mode this catches.

## Do not

- Rebase or force-push `automation/base` or `automation/testids`. Ever. Both are shared branches;
  `--force` has no legitimate use on either. (Force-pushing a short-lived `testids/<case>` branch to
  resolve a PR conflict is fine — that is a different branch.)
- Cut a `testids/<case>` review branch FROM `automation/testids`. Testid commits are born ON the
  integration branch (that's the norm — the dev server serves it), but the review branch is built on
  fresh `origin/main` and receives them by cherry-pick — that is what keeps each review PR a clean
  single-case diff.
- Push to the retired `fork` remote (`bermudas/EliteaUI`) if it still exists locally.
- Silently resolve a testid divergence in favour of our branch. `main` wins; then fix the LocatorDescriptor.
- Sync while another agent has uncommitted testid work.
- Dead-stop on a dirty tree. Classify it (Step 0), commit the deliverables, leave the strays.
- Push to this public repo without running the secret scan (Step 0b).
- Report success from branch counts alone — the suite must still import and collect.
