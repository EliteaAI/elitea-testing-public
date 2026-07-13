---
name: promote-automation-batch
description: Promotes an accumulated batch of work upstream — first the testids from the EliteaUI fork to EliteaAI/EliteaUI main, then (after DEV redeploys) the tests from automation/base to elitea-testing-public main, gated on a green CI run. Human-triggered only; never run autonomously.
allowed-tools:
  - Bash
  - Read
---

# Promote Automation Batch

Moves accumulated work from the two long-lived branches into their mains.

**HUMAN-TRIGGERED ONLY.** Never start this on your own initiative, never on a schedule, and never as a
follow-on from finishing a test. It opens PRs against another team's repository and gates a merge into
`main`. Wait to be asked. If asked, confirm the scope first: *which* testids, *which* tests, and who
reviews on the EliteaUI side.

## Why the order is fixed

Tests on `automation/base` use testids that exist only in our fork. Those tests **cannot pass on
`dev.elitea.ai` until the testids are merged upstream and DEV is redeployed**. So the UI always goes
first, and the green CI run against DEV is the gate that proves it landed.

```
  1. PR testids → EliteaAI/EliteaUI main        (their review, their timeline)
  2. merge + DEV redeploys
  3. run the suite from automation/base against DEV via GHA
  4. green? → PR automation/base → elitea-testing-public main
  5. merge
```

Do not reorder. Do not skip step 3 — it is the whole gate.

---

## Stage 1 — PR the testids to EliteaAI/EliteaUI

**One batch PR in flight at a time.** Check first:

```bash
gh pr list --repo EliteaAI/EliteaUI --author "@me" --state open
```

If one is already open, **stop**. Do not open a second — a new snapshot cut now would still carry the
open PR's commits (they are not in `upstream/main` yet), so the two PRs would overlap and both would
annoy reviewers. New testids keep accumulating on `automation/testids` and ship in the next batch;
nothing local is blocked meanwhile. The one exception: if reviewers have not yet looked, you may append
commits to the existing snapshot branch rather than opening a second PR.

First run the **sync-base-branches** skill. `automation/testids` must be rebased onto current
`upstream/main`, or the PR diff will be full of unrelated upstream commits.

**Cut a frozen snapshot branch. Do NOT open the PR from `automation/testids` itself** — agents keep
pushing new testids to that branch, and every push would silently mutate the PR while reviewers are
looking at it.

```bash
# WORKSPACE = parent folder holding the three sibling clones (no env var needed)
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
cd "$WORKSPACE/EliteaUI"
git checkout automation/testids
git log --oneline upstream/main..HEAD          # review exactly what ships. Testid commits only.

BATCH="chore/testids-batch-$(date +%Y-%m-%d)"
git checkout -b "$BATCH"
git push -u origin "$BATCH"

# RECORD THIS. It is the boundary SHA that sync-base-branches needs after the PR merges,
# to replay only post-batch commits regardless of how EliteaUI merged (merge/squash/rebase).
git rev-parse HEAD | tee .git/LAST_BATCH_BOUNDARY
```

Put that SHA in the PR body and keep it. Without it, a squash-merge upstream will make the next rebase
try to re-apply every testid commit, each one re-adding an attribute that already exists.

Inspect that log. If it contains anything that is not a `data-testid` addition — a behaviour change, a
debug edit, a stray console.log — **stop and report it**. It must not reach an upstream PR.

```bash
# Must be additive-only. Expect 0.
git diff upstream/main...HEAD | grep -E '^[+-]' | grep -v '^[+-][+-]' | grep -vc 'data-testid'
# The testids this batch ships:
git diff upstream/main...HEAD | grep -o 'data-testid="[^"]*"' | sort -u
```

**Check naming against what upstream already uses.** The EliteaUI team adds testids too (PR #513,
EL-5634), so there is an established vocabulary — match it rather than inventing a parallel one:

```bash
git grep -ho 'data-testid="[^"]*"' upstream/main -- 'src/*' | sed 's/data-testid=//;s/"//g' | sort -u
```

Their convention is `{section}-{element}-{type}` (`agent-save-button`, `skill-name-input`), with plural
section prefixes for list/collection pages (`artifacts-file-list`). If one of ours collides with an
existing name, or names the same element differently, fix it **before** the PR — not after a reviewer
asks.

```bash
gh pr create --repo EliteaAI/EliteaUI \
  --base main --head "<your-gh-user>:$BATCH" \
  --title "test: add data-testid attributes for UI automation" \
  --body "Adds \`data-testid\` attributes to support automated UI tests.

No behaviour change — attributes only.

Testids in this batch:
<list each testid and the component file it was added to>

Consumed by: EliteaAI/elitea-testing-public @ automation/base"
```

Then **stop and hand back to the human.** Review is on the EliteaUI team's timeline, not ours. Do not
poll, do not nudge, do not proceed.

If a reviewer renames a testid, that rename must be applied in three places before continuing: the JSX,
the page object on `automation/base`, and `automation/testids`.

---

## Stage 2 — After the UI merges and DEV redeploys

Confirm the testids are actually **live on DEV**, not merely merged. A merged PR that hasn't deployed
still fails every test.

```bash
# Quick pre-check: testids are string literals compiled into the bundle.
curl -s https://dev.elitea.ai | grep -oE '/assets/[^"]+\.js' | head -3
# fetch each and grep for one of the new testids, e.g.:
#   curl -s https://dev.elitea.ai/assets/index-XXXX.js | grep -c 'agent-form-save-button'
```

A zero count means it has not deployed yet. Wait; do not proceed.

---

## Stage 3 — The gate: run `automation/base` against DEV

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

## Stage 4 — PR `automation/base` → `main`

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

- Re-run **sync-base-branches**, using its *post-merge* form with the boundary SHA you recorded in
  Stage 1 (`git rebase --onto upstream/main <BOUNDARY> automation/testids`). Do not rely on a plain
  rebase to drop the promoted commits — that only works if EliteaUI merged rather than squashed.
  `automation/testids` ending up level with `upstream/main` means the batch fully landed.
- Then delete the frozen snapshot branch: `git push origin --delete "$BATCH"`.
- `automation/base` is now behind `main` by the merge commit — sync it too (merge, never rebase).
- Back-write the TMS per the project's seeded policy (`execution_type: automated`, `status: ready`,
  `automation_test_id`) — only if the seed establishes that; do not invent it.

## Do not

- Run any of this without being asked.
- Open the upstream PR from the live `automation/testids` branch.
- Merge to `main` on a red or unrun CI gate.
- Force-push anything in `elitea-testing-public`.
- Ship anything but `data-testid` attributes in the EliteaUI PR.
