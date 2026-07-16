---
name: promote-automation-batch
description: Promotes an accumulated batch of tests from automation/base to elitea-testing-public main, gated on a green CI run against a deployed env — after confirming the testids they depend on are on EliteaAI/EliteaUI main and deployed. Human-triggered only; never run autonomously. Does NOT promote testids: a human cherry-picks those from automation/testids to main (per-case draft-PR flow suspended 2026-07-16).
allowed-tools:
  - Bash
  - Read
---

# Promote Automation Batch

Promotes an accumulated batch of **tests** from `automation/base` into
`elitea-testing-public` `main`, gated on a green run against a deployed environment.

**HUMAN-TRIGGERED ONLY.** Never start this on your own initiative, never on a schedule, and never as a
follow-on from finishing a test. It gates a merge into `main`. Wait to be asked. If asked, confirm the
scope first: *which* tests, and against which environment.

> **This skill never promotes testids.** Its job is only the **tests** side; it does not open EliteaUI PRs.
> (History: it once batch-PR'd testids from a fork; the fork was retired 2026-07-13.) **Changed
> 2026-07-16:** testids live on `automation/testids` and are promoted to EliteaUI `main` by a **human
> cherry-pick** — agents no longer open per-case `main` PRs (`.agents/_reverted/`). This skill still just
> *verifies* the needed testids are already on `main` and deployed before promoting the tests.

## Why the order is fixed

Tests on `automation/base` use testids that may exist only on `automation/testids` — i.e. **not yet
cherry-picked to `main`** by a human. Such a test **cannot pass on a deployed env until its testid is on
`EliteaAI/EliteaUI` `main` and redeployed**. So the UI always lands first, and the green run against the
deployed env is the gate that proves it.

```
  1. confirm every testid this batch depends on is MERGED to EliteaUI main and LIVE on DEV
  2. run the suite from automation/base against DEV via GHA
  3. green? → PR automation/base → elitea-testing-public main
  4. merge
```

Do not reorder. Do not skip step 2 — it is the whole gate.

---

## Stage 1 — Confirm the testid prerequisites are on `main` AND live

Testid promotion (the human's cherry-pick to `main`) is not this skill's job, but testid *readiness* is its
precondition. Check each testid this batch depends on directly against `main`:

```bash
cd ../EliteaUI && git fetch origin
# For every testid the batch's tests use — is it on main yet (human already promoted)?
for t in <testids the batch depends on>; do
  printf "%-32s main:%s\n" "$t" \
    "$(git grep -q "data-testid=\"$t\"" origin/main -- src/ && echo YES || echo NO)"
done
```

Any test in this batch that depends on a testid **not yet on `main`** cannot be promoted. Two options,
both requiring the human's call:

- **Wait** — leave those tests on `automation/base` for the next batch (the default; nothing is blocked
  locally, the suite keeps running against `automation/testids`).
- **Nudge** — ask the human to cherry-pick the outstanding testids from `automation/testids` → `main` and
  deploy. Never promote the tests ahead of their testids.

Then confirm the merged testids are actually **live on DEV**, not merely merged. A merged PR that hasn't
deployed still fails every test.

```bash
# Testids are string literals compiled into the bundle.
curl -s https://dev.elitea.ai | grep -oE '/assets/[^"]+\.js' | head -3
# fetch each and grep for one of the batch's testids, e.g.:
#   curl -s https://dev.elitea.ai/assets/index-XXXX.js | grep -c 'agent-form-save-button'
```

A zero count means it has not deployed yet. Wait; do not proceed.

**If a reviewer renamed a testid** during review, that rename must be applied in three places before
continuing: the JSX (already done, on `main`), `automation/testids` (resolve the merge in favour of
`main`), and the `LocatorDescriptor` on `automation/base`. `main` is the source of truth.

---


## Stage 2 — The gate: run `automation/base` against DEV

```bash
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE/elitea-testing-public"
gh workflow run "UI Tests DEV" \
  -f ref=automation/base \
  -f suite=all \
  -f publish_to_tms=false

gh run list --workflow="UI Tests DEV" --limit 1
gh run watch <run-id>
```

**Green is the gate.** If anything fails, the batch is not ready — fix it on `automation/base` and
re-run. Do not open the promotion PR with a red run, and do not rationalize a failure as flaky without
evidence (re-run the single test and show the output).

---

## Stage 3 — PR `automation/base` → `main`

```bash
gh pr create --repo EliteaAI/elitea-testing-public \
  --base main --head automation/base \
  --title "test: promote automated UI tests (batch $(date +%Y-%m-%d))" \
  --body "Promotes tests accumulated on \`automation/base\`.

Depends on: EliteaAI/EliteaUI#<PR> (merged and deployed to DEV)

Gate: UI Tests DEV green on \`automation/base\` — <link to the run>

Tests in this batch:
<list test ids>"
```

Merge once reviewed. `automation/base` stays alive afterwards — it is long-lived, not consumed. It will
now be behind `main` by the merge commit, so finish by running **sync-base-branches** again.

---

## After promotion

- Re-run **sync-base-branches**. It merges `origin/main` into both long-lived branches. There is no
  boundary SHA and no replay to worry about any more: because `automation/testids` is *merged* rather than
  rebased, a testid that reached `main` is simply carried in — squash, merge, or rebase on the UI side all
  work out the same.
- `automation/base` is now behind `main` by the merge commit — sync it too (merge, never rebase).
- Merged `testids/<case>` branches are auto-deleted by GitHub (`delete_branch_on_merge`). Nothing to clean.
- Back-write the TMS per the project's seeded policy (`execution_type: automated`, `status: ready`,
  `automation_test_id`) — only if the seed establishes that; do not invent it.

## Do not

- Run any of this without being asked.
- Open, mark-ready, or merge a testid PR on `EliteaAI/EliteaUI`. Not this skill's job — `add-data-testid`
  opens them as drafts, and a **human** decides when the UI team sees them.
- Promote a test whose testid is still in an unmerged PR. It will fail on DEV. Wait for the next batch.
- Merge to `main` on a red or unrun CI gate.
- Force-push anything — in `elitea-testing-public` or on `automation/testids`.
- Rebase `automation/testids`. It is a shared org branch; merge it.
