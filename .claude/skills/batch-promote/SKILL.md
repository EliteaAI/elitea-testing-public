---
name: batch-promote
description: DRAFT / PROPOSAL (issue #703) — selective, batched promotion of chosen Ready tickets to main. Cherry-picks their testid + test commits onto batch branches cut from main (2 repos, or 3 when the batch touches the Support Assistant), stabilizes locally, opens BATCHED draft PRs, backports any divergence to the long-lived branches, and gates the deployed run BETWEEN the merges. Human-triggered. Sibling to promote-automation-batch (whole-branch). NOT YET ACTIVE — do not run.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Batch Promote  —  DRAFT / PROPOSAL (issue #703)

> ⚠️ **DRAFT — do not run.** This is the counter-design under discussion on issue #703
> (aliaksandr-valadzko's batch-promote proposal + the stabilize/backport refinement from the
> 2026-07-23 thread). It is **not yet active canon**. Genuine open questions are marked **`[DISCUSS]`**
> inline and rolled up at the bottom. Once agreed, the `[DISCUSS]` callouts get resolved and this
> banner is removed.

## What it is, and why it doesn't reverse the 2026-07-16 suspension

`promote-automation-batch` (the current skill) promotes the **whole** `automation/base` at once,
needs a human to have already cherry-picked **every** dependent testid to EliteaUI `main`, and gates
on a deployed run. That is **all-or-nothing**: one test whose testid isn't ready blocks the batch.

`batch-promote` promotes a **human-chosen subset** of Ready tickets by cherry-pick, and — the point —
**batches all their testids into ONE PR to EliteaUI `main`**.

The per-case testid draft-PR flow was suspended 2026-07-16 because **per-case PRs ballooned the PR
count and bothered the dev team**. A single consolidated PR per batch is the **cure** for exactly that
— so re-enabling agent-driven testid promotion **in batched form is not a reversal; it is the shape
the suspension was waiting for.**

| | `promote-automation-batch` | `batch-promote` (this) |
|---|---|---|
| Unit | whole `automation/base` | selected tickets (cherry-pick) |
| Testids → `main` | human cherry-picks per hand | **agent, batched into ONE PR** |
| PRs to `main` | 1 (tests) | 2 (testids + tests) — **3 if the batch touches the Support Assistant**; batched, draft |
| Blocks on | any not-ready testid blocks all | drop not-ready tickets, promote the rest |
| Gate | deployed run (testids already live) | local stabilize **+ deployed run between the merges** |

## HUMAN-TRIGGERED ONLY
Never autonomous, never on a schedule, never as a follow-on from finishing a test. It opens PRs into
`main` in two repos — three when the batch touches the Support Assistant. Wait to be asked; confirm scope first.

## Board setup (one-time — human/admin)
Two columns on Project #9: **To Promote** (human drops the collector issue here to trigger) and
**Promoted** (agent moves the batch's tickets here once the batch's PRs are open).
> **`[DISCUSS]`** column names; and whether **Promoted** is a new agent-terminal state *between*
> `Ready` and the human-only `Done`.

---

## Stage 0 — Read the collector
Find the single issue in **To Promote**:
```bash
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json --limit 200 \
  | jq '[.items[] | select(.status == "To Promote")]'
```
Parse its body for linked ticket numbers (`#N` / `Closes #N` / `References #N`). Present the resolved
list and **wait for human confirmation.** No collector, or no links → stop with a clear message.

## Stage 0.5 — Determine batch scope: 2 repos or 3?

Testids can live in **two** UI repos (`.agents/workflow.md` § Connected repos):

| Repo | Long-lived branch | Carries |
|---|---|---|
| `EliteaAI/EliteaUI` | `automation/testids` | the app's own testids |
| `EliteaAI/elitea_assistant` | `automation/testids` | **Support Assistant** testids (connected first-party repo, consumed as `@eliteaai/elitea-assistant`) |
| `EliteaAI/elitea-testing-public` | `automation/base` | the tests |

**Most batches touch only EliteaUI → the 2-repo flow below is unchanged.** Check whether this batch
has any Support-Assistant testid commits:

```bash
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
git -C "$WORKSPACE/elitea_assistant" fetch origin
git -C "$WORKSPACE/elitea_assistant" log --oneline origin/main..origin/automation/testids
```

Empty ⇒ **2-repo batch**; skip every "Assistant" step. Non-empty and any commit belongs to a selected
ticket ⇒ **3-repo batch**: the Assistant adds a branch, a PR, a backport target, and — the part that
actually bites — **an extra promotion hop with a lockfile bump** (Stage 6).

## Stage 1 — Identify each ticket's commits  *(parallelizable)*
Per ticket, locate its commits on the long-lived integration branches:
```bash
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
git -C "$WORKSPACE/EliteaUI" fetch origin
git -C "$WORKSPACE/EliteaUI" log --oneline origin/main..origin/automation/testids   # testid commits
git -C "$WORKSPACE/elitea-testing-public" fetch origin
git -C "$WORKSPACE/elitea-testing-public" log --oneline origin/main..origin/automation/base   # test commits
# 3-repo batch only — Support Assistant testids:
git -C "$WORKSPACE/elitea_assistant" log --oneline origin/main..origin/automation/testids
```
Filter by `ELITEA-<id>` in the message, or by diff touching the ticket's testids / test files. Build
`{ticket, ui_commits, assistant_commits, test_commits, test_files, testids}`. **Ambiguous or none found
→ ask the human (skip or investigate); never guess.**

> **`[DISCUSS]` — cherry-pick fragility (the main risk).** Commit→ticket mapping is heuristic: a
> testid commit can serve several tickets, and page objects / fixtures / `conftest` are **shared**, so
> a naive pick can drag in un-selected work or miss a dependency. This risk is **managed, not avoided**
> — by Stage 2's diff-verification (loud-stop on entanglement) and Stage 3's stabilization (a bad or
> missing pick surfaces as a **failing test, not a silent defect**). The alternative selection method
> is a **file-scoped checkout** (`git checkout automation/base -- <files>`), which has the same
> shared-file problem from the other side. Pick one on the #703 thread.

## Stage 2 — Cut the batch branches from `main` + cherry-pick
```
EliteaUI:              testids/batch-promote-<date>   from origin/main  ← the batch's testid commits
elitea-testing-public: tests/batch-promote-<date>     from origin/main  ← the batch's test commits
elitea_assistant:      testids/batch-promote-<date>   from origin/main  ← 3-repo batch ONLY
```
Cherry-pick in chronological order; on conflict keep the testid/test change and record the file for
Stage 5. **Verification (mandatory):**
```bash
git diff origin/main...<branch> --stat        # must be ONLY the selected tickets' files/changes
```
Any un-selected work (a shared file carrying another ticket's change) ⇒ **loud stop, report it, do not
proceed.** Nothing silently ships or drops.

## Stage 3 — Stabilize locally (this is what catches the fragility)
Start the local UI from the UI batch branch, run the batch's tests from the test batch branch:
```bash
pkill -f vite || true
git -C "$WORKSPACE/EliteaUI" checkout testids/batch-promote-<date>
# 3-repo batch: the dev server serves the Assistant from the sibling clone's WORKING TREE
# (vite.config.js aliases '@eliteaai/elitea-assistant' → ../elitea_assistant/src when
# VITE_ASSISTANT_LOCAL=1), so the Assistant batch branch must be CHECKED OUT there or you
# stabilize against the wrong Assistant code:
git -C "$WORKSPACE/elitea_assistant" checkout testids/batch-promote-<date>
(cd "$WORKSPACE/EliteaUI" && npm run dev &)   # :5173  — expect the "[vite] Support Assistant → LOCAL source" line
cd "$WORKSPACE/elitea-testing-public/automation"
HEADLESS=true ../.venv/bin/pytest <batch_test_files> -v --tb=short 2>&1 | tee /tmp/batch-promote-run.log
```
> ⚠️ **The local run proves nothing about the Assistant's deployed path.** Locally the alias serves
> Assistant *source*, bypassing the package entirely — so Assistant testids are green here even though
> a deployed env has no idea they exist. That gap is closed only by Stage 6's lockfile bump.
Green ⇒ the cherry-picked set is internally consistent. **Red ⇒ a pick is wrong/missing or a test needs
a fix — resolve on the batch branch and note it for Stage 5 backport.** This is a **pre-check**, not the
deployed gate (Stage 6).

## Stage 4 — Open the DRAFT PRs to `main` (batched, cross-linked)
- **PR-Assistant** *(3-repo batch only)* — `testids/batch-promote-<date>` → **elitea_assistant `main`**:
  all the batch's Assistant testids in one PR. Body = ticket links, testid list, and **"merge this
  FIRST — EliteaUI's lockfile bump (PR-UI) depends on this commit landing on `main`."**
- **PR-UI** — `testids/batch-promote-<date>` → **EliteaUI `main`**: ALL the batch's testids in one PR.
  Title `testids: batch promote <date> — ELITEA-N1, N2, …`; body = ticket links, testid list, companion
  test-PR link, and **"merge this first"** (after PR-Assistant, if any).
- **PR-Test** — `tests/batch-promote-<date>` → **elitea-testing-public `main`**: body = ticket links,
  test files, companion UI-PR link (**must merge + deploy first**), Stage-3 local-stabilize evidence,
  and a note that **the deployed gate (Stage 6) runs before this PR merges.**

All **draft**, mutually cross-linked. Merge order is strict: **Assistant → UI (+ lockfile bump) →
Test.** (One batched PR per repo is the whole point — it is what keeps PR volume down.)

## Stage 5 — Backport divergence to the long-lived branches  *(the robustness #703 lacked)*
Anything that changed on a batch branch but is **not** on the long-lived branch must flow back, or
`automation/base` / `automation/testids` diverge from `main` and the next sync breaks:
- **Trigger:** a cherry-pick conflict resolution, a **UI-team testid rename** during PR review, or a
  Stage-3 stabilization fix.
- **Destination:** EliteaUI testid edits → `EliteaUI automation/testids`; **Assistant testid edits →
  `elitea_assistant automation/testids`**; `LocatorDescriptor` / test fixes →
  `elitea-testing-public automation/base`. All three are shared org branches: **merge-only, never
  rebase, never force-push.**
- **Affected tests:** grep the changed testid across `automation/base` and **re-stabilize those** — a
  renamed testid may be used by tests *outside* this batch.

This is the existing **divergence rule** (`.agents/workflow.md` § Sync — "resolve in favour of `main`,
fix the `LocatorDescriptor`") applied **proactively as part of promotion** instead of surfacing at the
next `sync-base-branches`.
> **`[DISCUSS]`** how much of the backport is automatic vs human-confirmed. Renames are rare but
> high-impact and touch tests beyond the batch — I lean human-confirmed for renames, auto for pure
> conflict-resolution carry-back.

## Stage 6 — The deployed gate, sequenced BETWEEN the merges  *(keeps the real gate)*
At Stage 3 the testids live **only on the batch branch — not on `main`, not deployed** — so a deployed
run is impossible yet. The "does it work on the real env" proof therefore happens **between the
merges**, and is **human-owned**:

1. *(3-repo batch)* Human **merges PR-Assistant** → `elitea_assistant` `main`.
2. *(3-repo batch)* **Bump EliteaUI's lockfile to the new Assistant commit — the step that is easy to
   miss and silently breaks the batch.** `package.json` declares
   `"@eliteaai/elitea-assistant": "github:EliteaAI/elitea_assistant#main"` (a *branch*), but
   **`package-lock.json` pins a resolved SHA** and deploy builds run `npm ci`, which is lockfile-exact.
   So merging to Assistant `main` alone changes **nothing** on DEV:
   ```bash
   cd "$WORKSPACE/EliteaUI" && git checkout testids/batch-promote-<date>
   npm install @eliteaai/elitea-assistant     # rewrites package-lock.json to the new main SHA
   git add package-lock.json && git commit -m "chore: bump @eliteaai/elitea-assistant to <sha> (batch <date>)"
   git push                                   # lands on the UI batch branch, inside PR-UI
   # verify the pin actually moved:
   grep -o 'elitea_assistant.git#[0-9a-f]\{7,40\}' package-lock.json
   ```
   **Skip this and the Assistant testids never reach DEV** — the tests go green locally (alias serves
   source) and fail on every deployed env. This is the connected-repo "extra promotion hop"
   (`.agents/workflow.md` § Connected repos).
3. Human reviews + **merges PR-UI** (testids **+ the lockfile bump**) → EliteaUI `main` → deploys to DEV.
4. **Verify the batch's testids are LIVE on DEV** (string literals in the bundle) — **both** EliteaUI's
   own and any Assistant ones (the latter prove the bump worked) — **and run the batch tests against DEV**:
   ```bash
   curl -s https://dev.elitea.ai/assets/index-XXXX.js | grep -c '<a batch testid>'            # >0 = deployed
   curl -s https://dev.elitea.ai/assets/index-XXXX.js | grep -c '<an ASSISTANT batch testid>' # >0 = bump shipped
   gh workflow run "UI Tests DEV" -f ref=tests/batch-promote-<date> -f suite=<batch> -f publish_to_tms=false
   ```
   Green ⇒ gate passed. An Assistant testid missing here ⇒ the bump didn't ship; fix before continuing.
5. **Only then** merge **PR-Test** into `main`.

This preserves `promote-automation-batch`'s deployed gate — just sequenced later and human-gated. The
local stabilize (Stage 3) is the pre-check; **this** is the gate the test-PR merge waits on.
> **`[DISCUSS]`** who runs step 2 (human, or agent-on-request between the merges), and whether PR-Test
> is held **draft** until the DEV run is green (I recommend yes).

## Stage 7 — Board + cleanup
Per ticket in the batch: move **Ready → Promoted** + a work-log comment (all PR links, the gate
evidence, and — 3-repo batch — the Assistant lockfile-bump SHA). Then delete the collector issue, and
**delete every batch branch after its PR merges** (aliaksandr's note: *all merged branches must be
deleted*; the long-lived branches are **never** deleted). Restore the working clones to their
integration branches (Stage 3 checked them out):
```bash
git -C "$WORKSPACE/EliteaUI"          checkout automation/testids
git -C "$WORKSPACE/elitea_assistant"  checkout automation/testids   # 3-repo batch
```
Re-run **sync-base-branches** afterward (its Part 3 covers the Assistant) — `main` moved in 2–3 repos.

## Does NOT touch
- `automation/base` and **both** `automation/testids` branches (EliteaUI + elitea_assistant) are
  **read-only sources** here, except the Stage-5 backport (merge-only). **Never rebase or force-push them.**
- `EliteaUI/vite.config.js` — the local-Assistant alias is **operator-local** (`skip-worktree`'d,
  `VITE_ASSISTANT_LOCAL=1`). Never commit it to a batch branch.
- Merging any PR is **always a human action.**

---

## Open questions rolled up (for the #703 sync)
1. **`[DISCUSS]`** Deployed gate sequenced between the merges (Stage 6) vs local-only — I chose the
   former to keep the real gate; it costs a human step between merges.
2. **`[DISCUSS]`** Backport automation depth (Stage 5) — auto for conflict carry-back, human-confirmed
   for renames?
3. **`[DISCUSS]`** Selection method — cherry-pick (+ diff-verify) vs file-scoped checkout. Same
   shared-file risk either way; which is easier to make safe?
4. **`[DISCUSS]`** Skill vs Claude **workflow** — Stages 1 and 3 parallelize per ticket (aliaksandr's
   original reason for a workflow). Draft is written as a skill for reviewability.
5. **`[DISCUSS]`** Board columns + the **Promoted** terminal state (vs reusing `Ready`/`Done`).
6. **Confirm:** batched testid PR resolves the PR-volume reason the per-case flow was suspended
   (2026-07-16) — the premise this whole design rests on.
7. **`[DISCUSS]`** **Who owns the Assistant lockfile bump (Stage 6.2)?** It is a commit in *EliteaUI*
   that must land after the Assistant merge but before PR-UI merges — so it either (a) gets pushed onto
   the open PR-UI branch (agent-doable on request; keeps it inside the reviewed PR), or (b) becomes its
   own tiny EliteaUI PR (cleaner history, one more PR — mildly against the PR-volume goal), or (c) is a
   human step. I lean (a). Whoever owns it, the Stage-6.4 Assistant-testid `curl` check is what proves
   it actually happened.
8. **`[DISCUSS]`** Should a 3-repo batch be **split** instead — promote Assistant-dependent tickets as
   their own batch — so a lockfile-bump problem can't hold up EliteaUI-only tickets? Cost: two
   promotion runs.
