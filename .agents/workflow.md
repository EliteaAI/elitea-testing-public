# How This Team Works

_Seeded 2026-07-10 from operator way-of-work brief + PR sampling (merged PRs #10–15
on `main`). **Revised 2026-07-13: the EliteaUI fork was retired** — `automation/testids`
now lives on `EliteaAI/EliteaUI` directly. **Revised 2026-07-16 (current): agents no
longer open per-case draft PRs to EliteaUI `main`.** Testids terminate on
`automation/testids` (committed + pushed); a **human** cherry-picks them to `main`.
This is a suspended-not-deleted policy — restore notes in
`.agents/_reverted/RESTORE-testid-draft-pr-flow.md`. **Revised 2026-10 (current):
the factory and testid work are SPLIT.** The factory builds tests against the DEV env
as deployed with a locator ladder and never touches EliteaUI; a separate
`testid-migrator` swaps ladder locators for testids on already-green tests. Everything
below that mentions `automation/testids`, localhost:5173 or `add-data-testid` now
applies **only to the migrator**. Refresh when the process shifts._

## Git host

- **Host**: GitHub · **CLI**: `gh` · **Unit of change**: Pull Request
- **Remotes**: this repo `EliteaAI/elitea-testing-public` (admin);
  UI repo `EliteaAI/EliteaUI` (push, **no admin**) — worked on **directly, no fork**.
  A stale `fork` remote (`bermudas/EliteaUI`) may still exist locally as a safety
  net; it is **not** part of the workflow. Never push to it.

## The two processes (2026-10)

| | **Factory** (Tal → Sage → Axel) | **`testid-migrator`** (on request) |
|---|---|---|
| Input | TMS cases | the locator ledger (`.agents/locator-migration/ledger.json`) — non-testid declarations of already-merged, green tests |
| Target | DEV (`https://dev.elitea.ai`, `/app`) | phase B: localhost:5173 on `automation/testids` · phase A: DEV |
| Locators | ladder — existing testid → role+name → label → css → xpath, each non-testid with `suggested_testid=` | swaps a ledger row to `testid=` only once the testid is **on DEV** |
| Touches EliteaUI | **never** | yes — `add-data-testid` onto `automation/testids`, pushed; human cherry-picks to `main` |
| Output | one PR per case → `automation/base` | one PR per migration run → `automation/base` (phase A) + testid commits (phase B) |

**Why the split.** The old loop coupled every case to a second repo: a test needed a
testid → the testid lived in EliteaUI JSX → `main` review took days → the factory ran
against a local UI that served unmerged testids, and each case produced two PRs in two
repos. Building on DEV with the ladder removes the coupling: a factory test is green on
the env it targets the day it merges. Testid adoption is then a measured, batched
refactor (`automation/scripts/locator_inventory.py` — locator-debt metric + ledger),
and a test is migrated only after its testids are **deployed**, so a migrated test is
never red on DEV. The ledger states are `raw → testid-proposed → on-dev → migrated`
(`removed` when the declaration disappears).

## Branching

| Repo | Long-lived branch | Rule |
|---|---|---|
| elitea-testing-public | `automation/base` (cut from `main`) | small PRs into it, one per test/feature area; **never PR `main` directly** |
| EliteaAI/EliteaUI | `automation/testids` (integration) — **migrator only** | **never PR it into `main`, and (since 2026-07-16) never open per-case `main` PRs at all.** Testid commits are born ON it, committed + pushed, and stop there. A human cherry-picks them to `main`. |
| EliteaAI/elitea_assistant | `automation/testids` (integration) — **migrator only** | Connected repo (Support Assistant). Same rule as EliteaUI — testids born on it, committed + pushed, human promotes to its `main`. See § Connected repos. |

- There is **no CI on `automation/base`** — the green run from this machine against
  DEV before the PR is the only verification. You are the CI.
- There is **no `pending_testid` marker**. Do not invent one.
- Test work branches: `tests/<case-id>-<slug>`, cut from **`automation/base`**.
- Migrator batch branches: `locators/<yyyy-mm-dd>` (run date), cut from **`automation/base`**.
- Testid work (migrator only): committed **straight onto `automation/testids`** and pushed — no
  per-case branch, no PR (see § Testid flow below). *(Suspended 2026-07-16: the
  old `testids/<case-id>-<slug>` review branch + draft PR to `main` is on hold —
  `.agents/_reverted/`.)*
- Commit style (sampled from history): conventional-ish — `test: (5199) Add guardrails
  live-reload UI tests`, `refactor: use default gpt-5.2 model`, `docs(afs): amend selectors…`.

### No git worktrees for regular automation work (operator ruling 2026-07-24)

**Use plain branching and one straightforward flow at a time — one branch, one case,
no concurrent checkouts.** Do not create a `git worktree` as part of ordinary analysis,
implementation, review, or promotion work. **Only on an explicit human ask** (e.g. a
one-off recovery from a wedged clone) — never on your own initiative, and never as a
routine step in a skill or loop.

Why: worktrees bought parallelism this pipeline doesn't need (it is serial by design —
one case dispatched at a time, fresh-session review, lead-owned merge gate) and cost
real damage — a **confirmed-twice** hazard where `worktree add`/`remove` left the MAIN
checkout on the wrong branch (PRs #608, #693 —
`.agents/memory/qa-engineer/git_worktree_can_leave_main_checkout_on_wrong_branch.md`),
plus abandoned trees accumulating beside the sibling clones (6 stale, ~54 MB, cleaned
up 2026-07-24) which corrupt the load-bearing four-sibling topology.

**Reach for these instead — most "I need a worktree" moments need no checkout at all:**

| Goal | Do this |
|---|---|
| Read a file on another branch | `git show <branch>:<path>` |
| Compare against another branch | `git diff <branch>...HEAD` · `git log <branch>..HEAD` |
| Check a testid's presence on a ref | `git grep '<testid>' origin/main -- src/` (after `git fetch origin`) |
| Review a PR's code | Static review — **no execution, no checkout** (reviewer slot is static by contract) |
| Run a case's tests | The case's own branch, checked out normally, one at a time |
| Work another branch mid-task | Commit or park current work, `git checkout`, then return |
| Parallel work on shared files | Don't — serialize it. Two agents in one tree collide. |

If a checkout genuinely must move while another agent depends on the current one
(e.g. the EliteaUI dev server), that is a **coordination** problem: finish or park the
in-flight work first (the `sync-base-branches` guard pattern), don't fork the tree.

### Connected repos — testids in the Support Assistant (2026-07-23, #705) — migrator only

Some UI ships from **separate repos we own** but consume as packages — today the **Support
Assistant** (`@eliteaai/elitea-assistant`, source in the `../elitea_assistant` sibling). We add
testids there the SAME way as EliteaUI (§ Testid flow below), one repo outward:

- **Same dual-target model:** the assistant has its own permanent `automation/testids`
  integration branch (mirror of EliteaUI's; created 2026-07-23). Testids are born on it,
  committed + pushed; sync from its `main` by **merge only — never rebase/force**.
  *(Access: **push, no admin** on `EliteaAI/elitea_assistant`.)*
- **Local dev sees the source live** via a LOCAL-ONLY `EliteaUI/vite.config.js` alias +
  `VITE_ASSISTANT_LOCAL=1` (git-`skip-worktree`'d; full recipe in the parent `SETUP.md` § 6), so
  `add-data-testid` edits in `../elitea_assistant/src/**/*.tsx` HMR live on localhost:5173.
- **One extra promotion hop vs EliteaUI:** a testid on the assistant's `main` reaches a
  *deployed* env only after EliteaUI bumps the `@eliteaai/elitea-assistant` git-dependency to the
  new assistant commit. Local tests go green immediately (via the alias); the closure record must
  note the deployed-env promotion as pending that bump (owner = human).
- **Locator policy is unchanged:** the assistant's own JSX gets real testids
  (`.agents/testing.md` § Locator policy — connected-first-party-repo bullet). #579's
  scoped-raw-handle exception still applies to the assistant's OWN third-party internals
  (its mermaid / react-markdown output), exactly as it does inside EliteaUI.

### Testid flow — commit + push `automation/testids`, then stop — migrator only

**Current policy (2026-07-16): a testid is committed once, straight onto
`automation/testids`, and pushed. That is the agent's terminal step.** The dev
server runs that branch, so the testid is live under HMR the moment it exists and
every other agent sees it. Promotion to EliteaUI `main` is a **human** cherry-pick
from `automation/testids`, done out of band — **agents do not open EliteaUI `main`
PRs.**

```
    ══●══════●═══════════════════════════▶  automation/testids   (agent stops here)
      ▲   testid commits BORN + pushed        ← dev server :5173 runs THIS
      ╰── main merged in, often                  agents see EVERY testid
                                              ┄┄▶ human cherry-picks → main, later
```

```bash
cd ../EliteaUI                            # dev server is live on automation/testids
git fetch origin

# edit JSX under src/ ONLY, commit ON automation/testids (HMR shows it instantly),
# keep it in sync with main, then push the integration branch (plain FF — NEVER --force)
git add src/ && git commit -m "test: [EL-1737] add data-testid for …"
git merge origin/main && git push origin automation/testids
```
(Full procedure: `add-data-testid` skill.)

> **Suspended, not deleted.** The prior flow — cherry-pick each case onto a
> `testids/<case>-<slug>` branch cut from fresh `main` and open a **draft PR to
> `main`** — is on hold as of 2026-07-16 by operator request. To restore it see
> `.agents/_reverted/RESTORE-testid-draft-pr-flow.md`. Until then, **the human owns
> the `automation/testids` → `main` promotion**; agents never create that PR.

### Sync: `automation/testids` ← `main` — migrator only

**Merge. Never rebase, never force-push.** This branch is shared and lives on the org
repo — rewriting its history can clobber a colleague. `--force`/`--force-with-lease`
have **no legitimate use** on it.

```bash
cd ../EliteaUI
git checkout automation/testids
git fetch origin && git merge origin/main
git push origin automation/testids
```

Do this before a migrator phase-B run. Conflicts are rare — testid edits are additive
JSX attributes. If `package.json` / `package-lock.json` changed → re-run `npm install`
(a bare version bump doesn't require it).

> **Divergence rule — scope it precisely.** "Favour `main`" governs **code structure**
> and testid **renames**. It is NOT licence to drop our additive attributes:
>
> - Main **refactored the code around** our testid ⇒ take main's structure, then
>   **RE-ADD our testid on top**. Testids are additive and orthogonal to a refactor;
>   losing one here is a defect, not an acceptable merge outcome.
> - The UI team **renamed / moved** the testid ⇒ favour `main`, then fix the
>   `LocatorDescriptor` in this repo.
> - Main **deleted the element** ⇒ accept it; fix the page object + test, and do not
>   resurrect the testid.
>
> **Enforced, not trusted.** `sync-base-branches` § *Testid-loss guard* snapshots the
> testid set before and after every merge and blocks the push if it shrank. Three
> testids went missing before that gate existed: `artifacts-delete-files-button` and
> `artifacts-download-files-tooltip` were true merge losses (one-line restores), while
> `toolkit-detail-indexes-tab` was a legitimate element removal. Each surfaced days
> later, far from the cause. The guard greps **both** `data-testid="x"` and the
> prop-passed `testId="x"` form — `artifacts-delete-files-button` is wired via the
> prop, so a `data-testid`-only check reports "no loss" while the test breaks.

**Test repo ← main** (periodically): merge `main` into `automation/base`.

**Never shallow clones.** Check `test -f .git/shallow`; fix with `git fetch --unshallow origin`.

## The loop for one new test (factory)

1. **Refresh DEV auth** — `cd automation && ../.venv/bin/python scripts/dev_storage_state.py`
   (Playwright MCP runs `--isolated --storage-state .playwright-mcp/dev-storage-state.json`).
2. **Explore DEV** (Playwright MCP on `https://dev.elitea.ai/app`) — for each element
   the case touches, find the highest ladder rung that is unique: an existing testid
   first, then role+name, label, stable css, declared xpath.
3. **`page-object-generator` skill** — emit class-level declarations on that rung,
   every non-testid one with `suggested_testid=` (`.claude/rules/page-objects.md`).
4. **Write the test**, run it green against DEV, PR into `automation/base`.
5. **After merge**, `locator_inventory.py sync-ledger` registers the new non-testid
   declarations as `raw` rows — the migrator's queue.

Nothing in this loop touches EliteaUI or waits on its review. That is the point.

## The migration loop (`testid-migrator`)

Full procedure: `.claude/skills/migrate-locators-to-testids/SKILL.md`. In short:

1. `sync-ledger` + `queue` — split the ledger into **phase A** (testid already on
   DEV → swap) and **phase B** (needs a testid added).
2. **Phase A on DEV:** swap each `on-dev` row's declaration to `testid=`, run every
   test that uses it green on DEV, PR the batch to `automation/base`, mark `migrated`.
3. **Phase B on localhost:** `add-data-testid` for the next batch of `raw` rows
   (named by `suggested_testid`), commit + push `automation/testids`, mark
   `testid-proposed`. A human cherry-picks to `main`; when `check-ui-ref` sees the
   testid on the deployed ref, rows advance to `on-dev` and the next run's phase A
   picks them up.

A migrated test never depends on an undeployed testid — phase A only swaps what DEV
already serves.

## Promotion — HUMAN-TRIGGERED ONLY

What the lead performs — **only on explicit request**, never autonomously — is the
batch promotion (`batch-promote` skill): run the suite from GHA against the deployed
env, then open the `automation/base → main` gate PR (gate = green deployed run) and
merge.

**Simplified by the split:** factory tests are built on DEV and migrated tests only
reference testids that DEV already serves, so `automation/base` never depends on an
undeployed testid. The `batch-promote` testid-presence pre-check (Stage 6 sequencing)
is now a sanity check, not a blocker — if it ever finds a missing testid, a migrator
row skipped the `on-dev` gate; fix the ledger, don't sequence merges around it.

Testid promotion to EliteaUI `main` stays a **human** cherry-pick from
`automation/testids` (2026-07-16); agents don't open that PR.

## Review gates (pipeline-internal)

- Every automation PR into `automation/base`: adversarial review by `qa-engineer`
  (fresh session, `code-review` + triangulation vs TMS case and AFS) →
  `APPROVED` | `CHANGES_REQUESTED`; the lead merges.
- **Dispatch-prompt contract (lead):** every analyst, implementer and reviewer dispatch
  prompt carries the target + locator-policy line verbatim — see
  `.agents/role-overrides.md` § Orchestrator slot. The dispatch prompt is the gate.
- **Reviewer mechanical check:** the ladder grep in `.agents/role-overrides.md`
  § Reviewer slot — every added handle is a class-level declaration (testid, or a
  ladder rung with `suggested_testid=`); raw calls in methods/specs, `locator=` /
  `fallback=`, and positional picks are `CHANGES_REQUESTED`. Existing raw handles are
  tracked tech debt (#25/#42), not precedent.
- **Migrator batch review:** a fresh `qa-engineer` reviews the phase-A PR — every
  swapped testid verified on DEV (`check-ui-ref` output pasted), every affected test
  green on DEV — and the phase-B testid commits against the testid canon
  (`.agents/testing.md` § Testid-migrator rules).
- Commit authority: the implementer commits on the work branch the lead names
  (or creates one from `automation/base` when dispatched standalone). Factory roles
  never commit to EliteaUI; testid commits to `automation/testids` belong to the
  `testid-migrator` alone.

## Work tracking

Board #9 discipline lives in `.agents/profile.md` § Issue tracker — status machine,
human-only `Approved`, `question`/`bug` labels, work-log comments, and the
**identity rule**: every tracker/board write is prefixed `env -u GITHUB_TOKEN` so it
runs as the keyring account, never the shared `GITHUB_TOKEN`. Board mechanics:
`env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json`,
`… gh project field-list …`, `… gh project item-edit` — look up ids each time,
never hardcode.
Interactive session → the human in the room authorizes work; factory mode → work only
the one issue the dispatch names.

### Blocked on an app bug (cross-repo park)

When an automation case is blocked by a **confirmed application bug** filed in
`EliteaAI/elitea_issues` (via the `file-app-bug` skill), park the automation card the
same way as any blocker — with two cross-repo specifics:

- **Label** the parked card `blocked:app-bug` (distinct from a same-repo `Waiting on #N`).
- **Waiting-on line uses the full cross-repo form:** `Waiting on EliteaAI/elitea_issues#N`
  (plain text, never bare `#N` — bare resolves against THIS repo). This is what the
  tracking loop reads.
- **Unblock is not automatic and not human-only-gated by an agent.** The draft
  `track-app-issues` loop (`factory/loops/EXAMPLE-track-app-issues.*`, staged) polls
  `elitea_issues#N`; when it closes as `completed`, it strips `blocked:app-bug`, moves
  the card back to `Todo`, and comments "ready to resume" — a human re-approves.
  `Approved`/`Done` stay human-only.

### Closure record — factory cases (2026-10)

The lead posts this as the final comment on the automation issue. No testid row — the
factory added none, so the case is promotable as soon as it is merged:

```markdown
🔗 **Closure record — <CASE-ID>**

| Artifact | Where | State |
|---|---|---|
| Test | #<N> — `tests/<case>-<slug>` → `automation/base` | ✅ merged (`<sha>`) |
| AFS | `test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md` | on `automation/base` |
| Locators | declared <D> (testid <T> · ladder <L>) · unmanaged handles Δ <±U> | ledger: <L> new `raw` rows |
| Defects filed | #<X>, #<Y> — or "none" | |

**Status:** merged to `automation/base` · green on DEV · promotable.
**Still open:** <follow-ups, or "none">
```

The Locators row is the `locator_inventory.py scan` delta, **re-run by the lead on
`automation/base` after the merge and pasted** — never copied from the Run Report.
The issue moves to **`Ready`**; `Done` stays human-only.

### Closure record — testid-migrator batches (and pre-2026-10 cases)

The block below is the migrator's promotability check for the testids its phase B
pushed, and the historical record format for cases built under the localhost loop.

The work-log comments posted during a run (Started → AFS ready → PR opened → review →
merged) are a **narrative**. The closure record is the **artifact index**. Nobody
re-reads the narrative six months later; they read this one comment to find out where
the work lives and whether it's actually finished. **A bare "✅ merged" is not a closure
record** — that was the gap on #19.

The lead posts this as the final comment on the automation issue, **before** closing it.
**The promotability row is a verified fact, not a copy of the AFS/implementer claim**
(#35/#36/#37 shipped false rows by copying; the #19 rework shipped a false row from a
STALE clone — claimed 0/12 on main, truth was 5/12, added by the UI team's own
EL-5400). The verification block, verbatim — **the fetch is part of the check**, and
the output gets PASTED into the record:

```bash
cd ../EliteaUI && git fetch origin      # fresh ground truth — NON-OPTIONAL
FILTER='(data-testid|testid[[:space:]]*[:=])'          # -i is MANDATORY, see below
for t in <every testid the case's diff uses>; do
  printf "%-32s main:%-3s testids:%s\n" "$t" \
    "$(git grep -- "$t" origin/main -- src/ 2>/dev/null | grep -qiE "$FILTER" && echo YES || echo no)" \
    "$(git grep -- "$t" origin/automation/testids -- src/ 2>/dev/null | grep -qiE "$FILTER" && echo YES || echo no)"
done
```

**Note on the two-stage grep pattern (fixed 2026-08-10; supersedes the 2026-07-23
form that "resolved" #553 only halfway):**

Stage 1 (`git grep -- "$t"`) uses bare-substring matching to catch testids wired via:
- Direct attribute: `data-testid="agent-name-input"`
- Object literal: `'data-testid': 'agent-name-input'` and `testId: 'agent-name-input'`
- Prop indirection: `buttonTestId="agent-name-input"` → `data-testid={buttonTestId}`
- Runtime-composed: `` data-testid={`${PREFIX}-suffix`} `` — **stage 1 cannot see these
  at all.** If a component file differs from `origin/main`, diff the file itself
  (`git diff origin/main origin/automation/testids -- <file>`) instead of trusting a grep.

Stage 2 filters stage 1's hits down to real testid wiring, dropping comments
(`// TODO: add agent-name-input testid`) and prose mentions.

⚠️ **Both stage-2 flags are load-bearing — the pre-2026-08-10 filter
(`grep -qE "(data-testid|testid.*=.*$t)"`, no `-i`, `=` only) produced silent FALSE
NEGATIVES on two of the three wiring forms above:**
- `buttonTestId="agent-name-input"` — `testid` is **case-sensitive** and does not
  match `TestId`, and the line carries no literal `data-testid`, so it was dropped.
  Fixed by `-i`.
- `testId: 'agent-name-input'` — the **colon** form has no `=`, so it was dropped.
  Fixed by `[:=]`.

A false negative here writes "not on main" into a closure record that is wrong —
exactly the #19 failure the fetch rule was added to prevent. (Earlier still, the
literal `data-testid="$t"` form missed prop indirection and object literals
entirely: false rows on #73, #95, #166, #175, #262.)

**Caveat:** bare-substring stage 1 can still produce false *positives* (prefix
collisions — `agent-form` matching `agent-form-save-button` — or variable names).
When in doubt, read the hits instead of counting them:
```bash
git grep -- "$t" origin/main -- src/ | grep -iE '(data-testid|testid[[:space:]]*[:=])'
```

The UI team also adds testids in parallel (EL-5400, EL-5634, …). Only testids present
on **main** make a case promotable — and, since 2026-07-16, getting them there is a
**human** cherry-pick from `automation/testids`, not an agent PR. So the row reports
ground truth (on `automation/testids` ✓, on `main` yet?) and names the human as owner
of the gap:

```markdown
🔗 **Closure record — <CASE-ID>**

| Artifact | Where | State |
|---|---|---|
| Test | #<N> — `tests/<case>-<slug>` → `automation/base` | ✅ merged (`<sha>`) |
| Testids | EliteaAI/EliteaUI@<sha> (+ EliteaAI/EliteaUI@<sha> …) on `automation/testids` | ✅ pushed — dev server serves them; **human cherry-picks to `main`** |
| AFS | `test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md` | on `automation/base` |
| Defects filed | #<X>, #<Y> — or "none" | |

**Status:** merged to `automation/base` · testids on `automation/testids` · ⚠️ NOT yet on `main` (awaiting human cherry-pick) → not deployable-env-promotable yet.

**Testid commit SHAs — MANDATORY, regardless of promotability status.** The Testids
row must cite WHERE each testid was introduced (the originating commit SHA), whether
or not there's a pending cherry-pick action. This is the traceability anchor — six
months from now, "all pre-existing" tells you nothing; the SHA tells you where it
came from.

**Case A — testids NOT yet on `main` (awaiting human cherry-pick):**
List every testid commit's SHA this case added to `automation/testids`:

```bash
# the case's testid commits on the integration branch, newest first
git -C ../EliteaUI log origin/main..origin/automation/testids --oneline -- src/ | grep -i "<CASE-ID>"
```

**Case B — testids ALREADY fully on `main` (all pre-existing, nothing to cherry-pick):**
You still owe the SHA citations. Trace each testid to its originating commit on `main`:

```bash
# for each testid the merged test uses, find where it was introduced
cd ../EliteaUI
for t in <testid-1> <testid-2> ...; do
  sha=$(git log -1 --format=%h -S"data-testid=\"$t\"" origin/main -- src/)
  printf "%-32s EliteaAI/EliteaUI@%s\n" "$t" "$sha"
done
```

Paste the output into the Testids row. Format: `EliteaAI/EliteaUI@<sha>` for each
distinct originating commit (group testids by SHA if multiple came from the same commit).

**Worked examples:**

*Case A (3 new testids, not yet on main):*
```markdown
| Testids | EliteaAI/EliteaUI@a1b2c3d + EliteaAI/EliteaUI@e4f5g6h on `automation/testids` | ✅ pushed — dev server serves them; **human cherry-picks to `main`** |
```

*Case B (14 pre-existing testids, all already on main):*
```markdown
| Testids | All pre-existing — EliteaAI/EliteaUI@f9a1c8b7 (agent-name-input, model-selector-name, agents-page-header) + EliteaAI/EliteaUI@2d98830a (agents-import-button, agent-import-confirm-button) + EliteaAI/EliteaUI@9cb837f4 (entity-card-name) + EliteaAI/EliteaUI@76c60fed (agent-information-section) + 7 others | ✅ all on `main` — promotable |
```

> **Cross-repo links** (whenever you reference `EliteaAI/EliteaUI`): write the full
> `owner/repo` form as PLAIN TEXT — never inside backticks, never bare. **Commits:**
> `EliteaAI/EliteaUI@<sha>` renders as a clickable cross-repo commit link (this is the
> testid row's link now). **Issues/PRs:** `EliteaAI/EliteaUI#<M>`. Bare `#<M>` / bare
> `@<sha>` resolve against THIS repo (wrong), and GitHub never auto-links inside code
> spans. Both forms also leave a "mentioned in…" backlink on the EliteaUI side.
> Same-repo references (the test PR) stay bare `#<N>`.
**Unblocks when:** a human cherry-picks the testids `automation/testids` → `main`, and they deploy to DEV. **Owner:** human.
**Still open:** <follow-ups, or "none">
```

**Why the promotability row is load-bearing here.** A case's testids can sit on
`automation/testids` (pushed, serving the dev server) while `main` doesn't have them
yet — because promotion to `main` is now a **human** cherry-pick, done when they
choose. Such a test is **green on localhost and red on any deployed env** —
`automation/testids` has the testids, DEV does not. So *"merged" ≠ "done"*, and the
record must say which, naming the human as owner of the promotion. `batch-promote`
checks exactly this before a batch crosses to `main` — and when the batch *includes* the
testids, its Stage 6 sequences the deployed gate between the two merges instead.

**Do not close an issue whose testids aren't yet on `main`** — and do not
park it in `Blocked` either: nothing is stuck. Post the closure record, leave the
issue OPEN, and move the card to **`Ready`** — the agent-terminal state: delivered,
reviewable, awaiting the human's testid promotion / acceptance. **`Done` is human-only**
(the human closes + moves when the case is promotable/accepted), symmetric with
human-only `Approved` on the way in. `Blocked` means a REAL blocker only
(`Waiting on #N` — an open `question`/`bug` that stops work).

Worked example: [issue #19](https://github.com/EliteaAI/elitea-testing-public/issues/19)
(ELITEA-1737) — test merged, testids on `automation/testids` but not yet cherry-picked
to `main`, therefore NOT promotable. (Historical note: under the prior flow #19's
testids sat in draft PRs EliteaUI#525/#526; a human closed #19 while those were open.
The rule stands: agents leave such issues OPEN; only a human may close early.)

## Traps (cost someone an hour already)

- `requirements.txt` is **mkdocs-only**. Real deps: `pip install -e ".[reporting]"` —
  pytest won't even start without `allure-pytest` (`--alluredir` in addopts).
- venv must be Python 3.11+ (repo `.venv` is 3.13.13).
- `EliteaUI` has **no `.env.example`** (despite `start-ui-localhost` docs); its `.env`
  is a symlink to the master copy — don't recreate it.
- `npm install` looks hung during resolution — it isn't. Starting the dev server too
  early → `sh: vite: command not found`.
- OneDrive makes clones/fetches/installs slow — background long git/npm commands.
- `.env.test` beats shell exports (`config.py` orders dotenv first) — edit the file.
- Always run with cwd = `elitea-testing-public/` — that's what loads `.claude/skills`,
  `.claude/rules`, `.mcp.json`, `CLAUDE.md`, and lets the migrator's `add-data-testid` grep `../EliteaUI/src`.
- Playwright MCP lands on the Keycloak login page ⇒ the storage state expired —
  re-run `scripts/dev_storage_state.py` (it never types credentials into the browser).

## Unconfirmed

- `automation/base` PR review-approval count (branch is new — no PR history yet;
  pipeline-internal review applies regardless).
