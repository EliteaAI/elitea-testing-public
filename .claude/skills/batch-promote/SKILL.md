---
name: batch-promote
description: Promotes automation work from the long-lived integration branches to main — either the whole current state as-is (Mode A, proven) or a human-chosen subset of Ready tickets by cherry-pick (Mode B, draft pending #703). Cuts branches from main in 2 repos (3 when the batch touches the Support Assistant), then STABILIZES them in a loop — run the suite on localhost, triage every red to a class, fix upstream on the integration branch, rebuild, repeat — before opening BATCHED draft PRs and gating the deployed run between the merges. No defect masking to get a promotion out. Human-triggered only. Supersedes promote-automation-batch.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Batch Promote

Promotes automation work from the long-lived integration branches
(`elitea-testing-public automation/base`, `EliteaAI/EliteaUI automation/testids`, and
`elitea_assistant automation/testids`) into the respective `main` branches.

**HUMAN-TRIGGERED ONLY.** Never autonomous, never scheduled, never a follow-on from
finishing a test. It opens PRs into `main` in two repos — three when the batch touches
the Support Assistant. Wait to be asked; confirm scope first. **Merging is always human.**

> **Supersedes `promote-automation-batch`** (retired 2026-07-31). That skill was the
> single case "promote everything, testids already on `main`, gate on a DEV run" — which
> is Mode A with an empty testid PR. Its DEV-gate mechanics live on in Stage 6 here.

## Two modes — pick before anything else

| | **Mode A — as-is** | **Mode B — selective** |
|---|---|---|
| Unit | the whole current state of the integration branches | human-chosen Ready tickets |
| Method | scoped snapshot commit off `main` | cherry-pick each ticket's commits |
| Status | **proven** — executed 2026-07-31 | **DRAFT** — `[DISCUSS]` items open on #703 |
| Use when | first/bulk promotion, or catching `main` up wholesale | a subset is ready and the rest isn't |
| Risk | none from selection; all-or-nothing on scope | commit→ticket mapping is heuristic |

Mode B's `[DISCUSS]` markers are unresolved design questions — **do not run Mode B**
until #703 settles. Mode A is live.

## The gate is chosen by testid state, not by mode

This is the axis that actually matters, and it is independent of A/B:

| Testid state | Gate |
|---|---|
| Every testid the batch needs is **already on `main` and deployed** | Run the suite against DEV **before** opening the test PR. Stage 6 collapses to a single verification. |
| The batch **includes the testids** (the normal case) | A DEV run is *impossible* pre-merge — DEV doesn't have the testids yet. Verify on **localhost**, open draft PRs, and run the DEV gate **between** the merges (Stage 6). |

Getting this backwards is why a "just run it against DEV first" instinct fails: when the
promotion *is* the testids, that gate is circular by construction.

---

## Stage 0 — Scope and confirm

**Mode A:** confirm with the human what is being promoted and its boundary. Scope is a
set of **paths**, not tickets. The 2026-07-31 run used:

| Repo | Promoted paths | Deliberately excluded |
|---|---|---|
| `elitea-testing-public` | `automation/`, `test-specs/` | `.claude/`, `.agents/`, `docs/` — agent/tooling config is not the deliverable |
| `EliteaUI` | `src/` | everything else |
| `elitea_assistant` | `src/` | everything else |

**Mode B:** find the single collector issue in **To Promote** on Project #9, parse its
body for linked ticket numbers, present the resolved list, and wait for confirmation.

```bash
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json --limit 200 \
  | jq '[.items[] | select(.status == "To Promote")]'
```
> **`[DISCUSS]`** column names; whether **Promoted** is an agent-terminal state between
> `Ready` and human-only `Done`.

### Stage 0.5 — 2 repos or 3?

Testids can live in two UI repos (`.agents/workflow.md` § Connected repos). Most batches
touch only EliteaUI:

```bash
WORKSPACE="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
git -C "$WORKSPACE/elitea_assistant" fetch origin main --no-tags
git -C "$WORKSPACE/elitea_assistant" log --oneline origin/main..origin/automation/testids
```

Empty ⇒ **2-repo batch**; skip every "Assistant" step. Non-empty ⇒ **3-repo batch**: an
extra branch, PR, backport target, and — the part that bites — a **lockfile bump**
(Stage 6.2).

---

## Stage 1 — Sync the integration branches with `main` FIRST

Promoting a branch that is behind `main` produces a PR full of phantom reverts. Before
cutting anything, run **`sync-base-branches`**, including its **testid-loss guard** — a
merge can silently drop testid attributes, and that has happened more than once.

Confirm each source branch actually contains `main`:

```bash
git -C "$WORKSPACE/EliteaUI" fetch origin main --no-tags
git -C "$WORKSPACE/EliteaUI" merge-base --is-ancestor origin/main origin/automation/testids \
  && echo "EliteaUI: main contained" || echo "EliteaUI: NEEDS SYNC"

git fetch origin main --no-tags
git merge-base --is-ancestor origin/main origin/automation/base \
  && echo "tests: main contained" || echo "tests: NEEDS SYNC"
```

Also read what arrived from `main` — new commits touching areas the suite covers are a
heads-up for Stage 3, and any `data-testid` **removed** on main's side needs the
divergence rule applied now, not at the next sync.

---

## Stage 2 — Pre-flight: the suite must be honest before it is promoted

**Do not cut a promote branch over known-broken tests.** Every red must be triaged to a
class and either fixed or explained. Carrying a list of "known blockers" into a promotion
is how false confidence ships — a test red for a *fixable* reason is a defect, not a
baseline.

This stage is the **cheap first pass**: fix what is already known-red, on the integration
branches, before spending a branch cut and a multi-hour run on it. It does not replace
Stage 4's stabilization loop — it just keeps that loop from starting several iterations
in the hole.

Use **`adjust-automated-test`** for triage. Only two outcomes may reach a promote branch:

- **Fixed** — drift, missing/lost testid, data-hygiene defect.
- **Explained and legitimate** — a product bug with an OPEN linked issue and the
  assertion held at the *correct* expected value (sanctioned RED), or a documented
  environment gap (missing credential, unseeded precondition) filed as an issue.

### Pre-flight check — testids the suite references but that do not exist

A page object can reference a testid that was **never added to the UI**, or that a merge
silently ate. Both produce a red that looks like drift and is not. Catch them here:

```bash
cd "$WORKSPACE/elitea-testing-public"
# every testid the page objects bind to
grep -rhoE 'testid="[^"]+"' automation/pages/ | sed 's/testid="//;s/"//' | sort -u > /tmp/pobj-testids.txt
cd "$WORKSPACE/EliteaUI" && git fetch origin main --no-tags
while read -r t; do
  git grep -q -- "$t" origin/automation/testids -- src/ 2>/dev/null \
    || echo "  MISSING IN UI: $t"
done < /tmp/pobj-testids.txt
```

Anything listed is a testid the suite binds to that no UI element carries. For each, use
`git log --all -S"<testid>" -- src/` to tell the two cases apart:

- **0 commits ever** ⇒ it was never added. Add it (`add-data-testid`), scoped to elements
  the referencing test actually exercises.
- **Commits exist, gone now** ⇒ a merge dropped it. Restore it on top of `main`'s current
  structure per the divergence rule (`.agents/workflow.md` § Sync).

> Templated testids (e.g. `DotMenu` deriving `data-testid` from an item's `key`) will not
> match a literal grep of `src/`. Confirm by rendering, not only by grep, before
> declaring one missing.

---

## Stage 3 — Cut the promote branches from `main`

Branch names (both modes):

```
EliteaUI:              testids/promote-<date>   from origin/main
elitea-testing-public: tests/promote-<date>     from origin/main
elitea_assistant:      testids/promote-<date>   from origin/main   ← 3-repo batch ONLY
```

**Mode A** — build a scoped snapshot commit. Full recipe, verification steps, and the
zsh/plumbing traps: **`references/as-is-mechanics.md` §2**. In short: parent is
`origin/main`; the tree is `main`'s tree with the promoted subtrees swapped in; then
verify the diff touches *only* the promoted prefixes.

**Mode B** — cherry-pick each ticket's commits in chronological order; on conflict keep
the testid/test change and record the file for Stage 5.

**Verification, mandatory in both modes:**

```bash
git diff origin/main...<branch> --stat     # ONLY the intended scope may appear
```

Anything unexpected ⇒ **loud stop.** Nothing silently ships or drops.

> **`[DISCUSS]` (Mode B only) — cherry-pick fragility.** Commit→ticket mapping is
> heuristic: a testid commit can serve several tickets, and page objects / fixtures /
> `conftest` are shared, so a naive pick can drag in un-selected work or miss a
> dependency. Managed by this diff check plus Stage 4's run, where a bad pick surfaces as
> a failing test rather than a silent defect. Mode A does not have this problem at all.

---

## Stage 4 — Stabilize: run, triage, fix upstream, rebuild, repeat

**This is a loop, not a checkpoint.** Cutting the branches is the cheap part; making the
promoted state honest is the work. Expect several passes.

```
   ┌─────────────────────────────────────────────────────────┐
   │  run the suite on localhost against the promoted code    │
   │            ↓                                             │
   │  triage EVERY red to a class — no "known blocker" lists  │
   │            ↓                                             │
   │  fix UPSTREAM (integration branch), not the promote branch│
   │            ↓                                             │
   │  rebuild the snapshot (Stage 3) ── back to the top ──────┘
   └─ exit when every remaining red is explained (see below)
```

### Where the fix goes — decided by the cause, not by convenience

| Cause | Fix where | Rebuild needed? |
|---|---|---|
| **The cut itself** — wrong scope, a subtree missed, tree composed incorrectly | Fix the *recipe* and rebuild. Nothing is wrong upstream. | Yes |
| **A general defect** — drift, missing/lost testid, data hygiene, flaky wait | **Upstream**: `automation/base` for test/page-object code, `automation/testids` for testids. Then rebuild. | Yes |
| **A product bug** | Nowhere in this skill. File it, link it, hold the assertion at the correct value. | No |

**Mode A: never edit a promote branch directly.** It is *derived* — regenerating it from
the fixed integration branch is one command (`references/as-is-mechanics.md` §2, §4). If
you patch the promote branch instead, the defect stays upstream and returns at the next
promotion, and you have manufactured exactly the divergence Stage 7 exists to clean up.

**Mode B is the exception**: a cherry-picked branch legitimately diverges (conflict
resolution, a fix that only makes sense in the subset), so fix on the batch branch and
**backport per Stage 7**.

### Triage discipline

Classify before fixing — a red test is not evidence that the test is wrong. Use
**`adjust-automated-test`** (classes A–F) and the project's questioning ladders in
`.agents/role-overrides.md`: the interaction-discovery ladder before declaring any UI
"broken", and the OpenAPI cross-check before calling a 4xx/5xx a backend bug.

**No defect masking, ever** — not even to get a promotion out. Never lower a count, weaken
a comparison, delete a step, or skip a test to turn a promote branch green. A promotion
that ships a masked failure is worse than one that ships a documented red, because the
mask outlives the promotion. Verify each fix by re-running the affected test *before* the
next full pass, so a full run is never spent proving a one-line change.

### Exit criteria — what may still be red

Only two things:

1. **A product bug** with an OPEN linked issue, the assertion held at the *correct*
   expected value, and `# Known defect: #N` in the code (sanctioned RED — see
   `.agents/testing.md` § Merge gate).
2. **A documented environment gap** — a missing credential, an unseeded precondition —
   filed as an issue, with the cause named.

Everything else is fixed or the promotion waits. "Known blocker" is not a class; if the
only thing making a test red is that someone previously decided not to fix it, fix it now.

### Reaching the promoted code

The testids are not on `main` yet, so this is a **localhost** run. Two ways in:

**Preferred (Mode A) — prove equivalence, check out nothing.** If each promote branch's
tree equals its integration branch's tree within the promoted scope, the running dev
server and the working tree already *are* the promoted code. Recipe:
`references/as-is-mechanics.md` §3. This respects the no-worktrees policy
(`.agents/workflow.md`) and avoids the `skip-worktree` checkout trap.

**Otherwise (Mode B) — check the batch branches out**, since a cherry-picked subset is
genuinely different content:

```bash
pkill -f vite || true
git -C "$WORKSPACE/EliteaUI" checkout testids/promote-<date>
# 3-repo batch: the dev server serves the Assistant from the sibling clone's WORKING TREE
# (vite.config.js aliases the package → ../elitea_assistant/src when VITE_ASSISTANT_LOCAL=1),
# so the Assistant branch must be checked out too or you verify the wrong Assistant code:
git -C "$WORKSPACE/elitea_assistant" checkout testids/promote-<date>
(cd "$WORKSPACE/EliteaUI" && npm run dev &)   # :5173 — expect "[vite] Support Assistant → LOCAL source"
```

Then run — Mode A runs the **whole** suite, Mode B only the batch's tests:

```bash
cd "$WORKSPACE/elitea-testing-public/automation"
HEADLESS=true ../.venv/bin/pytest tests/ui -m 'not guardrails' -v -p no:cacheprovider \
  2>&1 | tee /tmp/promote-verify-run.log
```

**Never edit `EliteaUI/src` while this is running** — HMR pushes the change into the
browser mid-test and invalidates the run (`references/as-is-mechanics.md` Trap 3). A
partially-HMR'd run is not evidence, so **kill it rather than finish it**: a full pass
costs ~2h, and letting it run to completion only to redo it costs the same 2h twice. Kill,
fix, rebuild, re-run.

> ⚠️ A local run proves nothing about the **Assistant's deployed path**: the alias serves
> Assistant *source*, bypassing the package, so Assistant testids are green here even
> though a deployed env has never heard of them. Only Stage 6.2's lockfile bump closes it.

Loop until the exit criteria above are met. Then proceed — this is the **pre-check**;
Stage 6 is the gate.

---

## Stage 5 — Open the DRAFT PRs to `main` (batched, cross-linked)

- **PR-Assistant** *(3-repo only)* → `elitea_assistant main`: all the batch's Assistant
  testids. Body: **"merge FIRST — EliteaUI's lockfile bump depends on this landing."**
- **PR-UI** → `EliteaUI main`: **all** the batch's testids in one PR. Body: testid list,
  companion test-PR link, **"merge before the test PR."**
- **PR-Test** → `elitea-testing-public main`: test files, companion UI-PR link (must merge
  **and deploy** first), Stage-4 evidence, and a note that the **DEV gate runs before this
  merges.**

All **draft**, mutually cross-linked. Merge order is strict:
**Assistant → UI (+ lockfile bump) → Test.** One batched PR per repo is the point — it is
what keeps PR volume down, and it is the shape the per-case flow's 2026-07-16 suspension
was waiting for.

For Mode A, state the scope boundary explicitly in the PR body (what was promoted and
what was deliberately left behind), because a reviewer cannot infer it from a squashed
diff.

---

## Stage 6 — The deployed gate, sequenced BETWEEN the merges

At Stage 4 the testids live only on the promote branch, so this is where the "does it work
on the real environment" proof happens. **Human-owned.**

1. *(3-repo)* Human merges **PR-Assistant** → `elitea_assistant main`.
2. *(3-repo)* **Bump EliteaUI's lockfile** — easy to miss, silently breaks the batch.
   `package.json` declares a *branch* dep, but `package-lock.json` pins a resolved SHA and
   deploy builds run `npm ci` (lockfile-exact), so merging the Assistant alone changes
   nothing on DEV:
   ```bash
   cd "$WORKSPACE/EliteaUI" && git checkout testids/promote-<date>
   npm install @eliteaai/elitea-assistant
   git add package-lock.json && git commit -m "chore: bump @eliteaai/elitea-assistant to <sha>"
   git push
   grep -o 'elitea_assistant.git#[0-9a-f]\{7,40\}' package-lock.json   # verify the pin moved
   ```
3. Human reviews + merges **PR-UI** (testids **+ lockfile bump**) → deploys to DEV.
4. **Verify the testids are LIVE on DEV**, then run the suite against DEV:
   ```bash
   curl -s https://dev.elitea.ai | grep -oE '/assets/[^"]+\.js' | head -3
   curl -s https://dev.elitea.ai/assets/index-XXXX.js | grep -c '<a batch testid>'
   curl -s https://dev.elitea.ai/assets/index-XXXX.js | grep -c '<an ASSISTANT testid>'  # proves the bump
   gh workflow run "UI Tests DEV" -f ref=tests/promote-<date> -f suite=all -f publish_to_tms=false
   gh run list --workflow="UI Tests DEV" --limit 1 && gh run watch <run-id>
   ```
   A zero count = not deployed yet; wait, do not proceed. An Assistant testid missing =
   the bump didn't ship. **Green is the gate** — never rationalize a failure as flaky
   without re-running that single test and showing the output.
5. **Only then** merge **PR-Test**.

> **`[DISCUSS]`** who runs step 2 (human, or agent-on-request between merges), and whether
> PR-Test stays draft until the DEV run is green (recommend yes).

---

## Stage 7 — Backport divergence to the long-lived branches

Anything that changed on a promote branch but is **not** on the long-lived branch must
flow back, or the integration branches diverge from `main` and the next sync breaks.

**In Mode A this stage is mostly empty by construction** — Stage 4 fixes upstream and
regenerates, so the promote branch never holds anything the integration branch lacks. The
one case that still reaches here is a change made *after* the PRs open: a **UI-team testid
rename during review**. That is real divergence and must be backported.

**In Mode B it is load-bearing**, because cherry-picked branches diverge legitimately.

- **Triggers:** a conflict resolution (B), a **UI-team testid rename** during review
  (A and B), or a post-PR fix pushed onto a promote branch (A and B).
- **Destinations:** EliteaUI testid edits → `EliteaUI automation/testids`; Assistant edits
  → `elitea_assistant automation/testids`; `LocatorDescriptor`/test fixes →
  `elitea-testing-public automation/base`. All shared org branches: **merge-only, never
  rebase, never force-push.**
- **Renamed testid?** grep it across `automation/base` and re-verify those tests — a
  rename can affect tests outside this batch.

This is the divergence rule (`.agents/workflow.md` § Sync) applied proactively instead of
surfacing at the next `sync-base-branches`.

> **`[DISCUSS]`** how much is automatic vs human-confirmed — renames are rare, high-impact
> and reach beyond the batch; lean human-confirmed for renames, auto for conflict carry-back.

---

## Stage 8 — Board, cleanup, re-sync

- **Mode B:** per ticket, move **Ready → Promoted** with a work-log comment (PR links,
  gate evidence, and the Assistant lockfile SHA for a 3-repo batch). Delete the collector.
- **Both:** delete every promote branch **after its PR merges** (long-lived branches are
  never deleted). Restore any clone Stage 4 checked out:
  ```bash
  git -C "$WORKSPACE/EliteaUI"         checkout automation/testids
  git -C "$WORKSPACE/elitea_assistant" checkout automation/testids
  ```
- Re-run **`sync-base-branches`** — `main` moved in 2–3 repos, and `automation/base` is
  now behind by the merge commit. Merge, never rebase.
- Back-write the TMS per the seeded policy (`.agents/test-automation.yaml`
  § `backwrite_on_done`) — only if the seed establishes it; never invent it.

---

## Does NOT touch

- `automation/base` and both `automation/testids` branches are **read-only sources** here,
  except the Stage-7 backport (merge-only). **Never rebase or force-push them.**
- `EliteaUI/vite.config.js` — the local-Assistant alias is operator-local
  (`skip-worktree`'d). Never commit it to a promote branch.
- **Merging any PR is always a human action.**
- Force-pushing a promote branch is fine **only while no PR is open on it**
  (`references/as-is-mechanics.md` §4); once a PR exists, push normal commits.

---

## Open questions (Mode B / #703)

1. **`[DISCUSS]`** Backport automation depth (Stage 7) — auto for conflict carry-back,
   human-confirmed for renames?
2. **`[DISCUSS]`** Mode B selection: cherry-pick (+ diff-verify) vs file-scoped checkout.
   Same shared-file risk either way.
3. **`[DISCUSS]`** Skill vs Claude **workflow** — Mode B's per-ticket stages parallelize.
   Written as a skill for reviewability.
4. **`[DISCUSS]`** Board columns + the **Promoted** state (vs reusing `Ready`/`Done`).
5. **`[DISCUSS]`** Who owns the Assistant lockfile bump (Stage 6.2) — pushed onto the open
   PR-UI branch (lean this), its own tiny PR, or a human step?
6. **`[DISCUSS]`** Should a 3-repo batch be **split**, so a lockfile problem can't hold up
   EliteaUI-only tickets? Cost: two promotion runs.

**Answered 2026-07-31 by the first Mode A run:** the batched testid PR does resolve the
PR-volume objection behind the 2026-07-16 per-case suspension — one PR carried 88 testids
across 113 files, versus 88 per-case PRs under the old flow.
