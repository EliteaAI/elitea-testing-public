# How This Team Works

_Seeded 2026-07-10 from operator way-of-work brief + PR sampling (merged PRs #10–15
on `main`). **Revised 2026-10: one target, one repo.** Tests are built,
run and gated against the **DEV env as deployed**, with ladder locators
(`.agents/testing.md` § Locator policy), and every artifact a case produces lands in
**this** repo. **Revised 2026-10-16 (current): base is `main`; the lead squash-pushes
each gated batch straight to it** — no PR, no human merge; `automation/factory` is
frozen history. Refresh when the process shifts._

## Git host

- **Host**: GitHub · **CLI**: `gh` · **Unit of change**: one squash commit per batch on `main`, pushed directly
- **Remote**: this repo, `EliteaAI/elitea-testing-public` (admin). It is the only
  repo a case commits to.

## One loop, one repo (2026-10)

| | |
|---|---|
| Input | TMS cases |
| Target | DEV — `https://dev.elitea.ai`, `APP_PREFIX=/app` |
| Locators | the ladder — existing testid → role+name → label → css → xpath, each non-testid declaration carrying `suggested_testid=` |
| Output | **one** squash commit per batch on `main`, in this repo (a batch of one = one case) — **pushed by the lead** after review + the 3× DEV gate |

**Why it looks like this.** An earlier loop coupled every case to the frontend repo: a
test needed a testid, the testid needed a frontend change, that change needed days of
review, and each case produced two PRs in two repos. Building on DEV with the ladder
removes the coupling — a test is green on the env it targets the day it lands, and a
missing testid is a `suggested_testid=` hint rather than a blocker. Converting those
hints into real testids is a separate, on-request process with its own session and its
own procedure (`.claude/skills/migrate-locators-to-testids`); it never runs as part of
a case and needs no space in your context.

## Branching

| Repo | Long-lived branch | Rule |
|---|---|---|
| elitea-testing-public | `main` | one squash commit per batch (the gated `tests/batch-<slug>` trunk; a batch of one is one case branch), **pushed directly by the lead** — only after every unit is reviewer-`APPROVED` and the trunk passed the lead's 3× DEV gate. No other role pushes `main`; nobody rebases or force-pushes it |

- There is **no CI before `main`** — the green run from this machine against DEV
  (implementer), the fresh-session review and the lead's 3× gate before landing are
  the verification. You are the CI. The human acceptance step is `Ready` → `Done` on
  the card, after the work is already on `main`.
- **`main` also moves on its own**: `build-test-index.yml` commits
  `automation/index.json` (as `github-actions[bot]`) after every push touching
  `automation/tests/ui/**` — including your own landing. Always `git fetch origin`
  before a push to `main`; a rejected push is normal, never a reason to `--force`.
- `automation/factory` and `automation/base` are **frozen history** (cut-over
  2026-10-16, both identical to `main` at that point). Never branch from, PR into or
  sync them.
- There is **no `pending_testid` marker**. Do not invent one.
- Branches: a batch trunk `tests/batch-<slug>` (or, for a batch of one,
  `tests/<case-id>-<slug>`) cut from a freshly fetched **`origin/main`**; a batch's
  unit branches `tests/<case-id>-<slug>` are cut from the trunk and merge back into it.
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
| Review a unit's code | Static review — **no execution, no checkout** (reviewer slot is static by contract) |
| Run a case's tests | The case's own branch, checked out normally, one at a time |
| Work another branch mid-task | Commit or park current work, `git checkout`, then return |
| Parallel work on shared files | Don't — serialize it. Two agents in one tree collide. |

If a checkout genuinely must move while another agent depends on the current one, that
is a **coordination** problem: finish or park the in-flight work first, don't fork the
tree.

### Keeping a trunk current

There is no base-branch sync — branches are cut from `origin/main` directly. What
drifts is a **trunk between its gate and its landing**: when `origin/main` moved in a
way that touches the batch's files, merge `origin/main` into the trunk (never rebase,
never force-push) and re-run the gate before landing. Cases that depend on each other
belong in the same batch (one commit); a case that needs another batch that has not
landed yet is parked `Blocked` — "Waiting on #N" — never stacked on the unlanded
trunk.

**Never shallow clones.** Check `test -f .git/shallow`; fix with `git fetch --unshallow origin`.

## The loop for one new test

1. **Refresh DEV auth** — `cd automation && ../.venv/bin/python scripts/dev_storage_state.py`
   (Playwright MCP runs `--isolated --storage-state .playwright-mcp/dev-storage-state.json`).
2. **Explore DEV** (Playwright MCP on `https://dev.elitea.ai/app`) — for each element
   the case touches, find the highest ladder rung that is unique: an existing testid
   first, then role+name, label, stable css, declared xpath.
3. **`page-object-generator` skill** — emit class-level declarations on that rung,
   every non-testid one with `suggested_testid=` (`.claude/rules/page-objects.md`).
4. **Write the test**, run it green against DEV, review, gate, land on `main`.
5. **Before landing, on the trunk**, `locator_inventory.py sync-ledger` registers the
   new non-testid declarations as `raw` rows — the locator-debt ledger rides in the
   batch's one commit (§ Closing a batch).

The loop is self-contained: one repo, one env, one session — nothing waits.

## Promotion — none for this repo

Every batch lands on `main` directly, so there is nothing to promote in
`elitea-testing-public`. `batch-promote` survives only for the testid integration
branches (`automation/testids` in `EliteaUI` / `elitea_assistant`) — human-triggered
only, as before.

## Closing a batch — everything in ONE commit

**A batch reaches `main` as exactly one commit, and that commit is complete.** Every
change the batch makes to this repo — tests, page objects, AFS, the locator-debt
ledger, the batch's records, the team's memory — rides in the one squash commit.
There are no follow-up `chore(ledger)` / memory / daily-log commits on `main`.

So after the gate is green, and **before** the squash, the lead commits the batch's
bookkeeping **on the trunk** (`tests/batch-<slug>`):

1. **Locator ledger** — `git fetch origin`, then on the trunk run
   `locator_inventory.py scan` (paste it; the delta vs the pre-landing `origin/main`
   goes in the commit message) + `sync-ledger`; commit
   `.agents/locator-migration/ledger.json` if it changed.
2. **Batch records** — `.agents/automation/<slug>/report.json` with the gate verdict
   written back (orchestration playbook § Close), plus `gate-runs.jsonl`. Then close
   the session's work scope (`work-scope.mjs close --session <id>`): it writes
   `cost.json` + `batch-report.*` / `batch-tokenomics.*` into the same dir. Those
   are the files `.gitignore` lets through from `.agents/automation/**`; the rest of
   the batch dir stays local.
3. **Memory** — the lead's (and any role's) `.agents/memory/**` entries and the
   daily log for this batch.

These touch only `.agents/**`, so they do not re-open the gate. Anything committed to
the trunk after the gate under `automation/` **does** — re-gate before landing.

Then land the trunk (`.agents/role-overrides.md` § Orchestrator slot — *Landing a
batch*): one `git merge --squash`, one commit, one push.

## After landing

The lead does this **in the same session** that pushed the batch, right after the
push succeeds — there is no separate post-merge loop, and **nothing further is
committed to `main`** for the batch. For every case of the batch:

1. TMS back-write (`.agents/test-automation.yaml` § `backwrite_on_done`). **UI cases
   are written by CI**: the push triggers `build-test-index.yml`, whose
   `tms-backwrite` job derives the fields from the tests' `@pytest.mark.tms` +
   `@allure.issue` pair and commits them to TMS `main`. Your job is to **verify** it:
   `env -u GITHUB_TOKEN gh run list --repo EliteaAI/elitea-testing-public --workflow
   build-test-index.yml --commit <landed sha> --json databaseId,status,conclusion`,
   wait for `completed`, then confirm each case file on TMS `main` reads `automated` /
   `ready` with this case's Form C ref and `automation_pr` = the landed commit. A
   **red run** (`check` rejected a marker/link) means the cases were NOT written:
   the fix is a test-code change, so it is the next batch's work — park the card
   `Blocked` with the run URL, never hand-write around it. Non-UI cases (API), or a
   run that could not push: back-write by hand per `backwrite_on_done` + rebuild
   `index.json`.
2. Post the **closure record** (below) on every card and move each to `Ready`. The
   card stays open until a human closes it (`Done` stays human-only).

Anything found missing after the push (a ledger row, a memory entry) is **not** a
follow-up commit: `sync-ledger` is idempotent and the next batch's run registers
the row, and a memory entry rides in the next batch's commit — say so in this
batch's closure record. The cost record is a recompute at close, so spend after it
(the back-write, the closure records) shows in `team-report.mjs`, never by amending
`main`.

A session that pushed a batch but died before steps 1–2 left the card `In Progress`
with work on `main`: the next session (or the control loop's flag) finishes 1–2 from
the landed commit — never re-land it.

## Review gates (pipeline-internal)

- Every unit of an automation batch: adversarial review by `qa-engineer`
  (fresh session, `code-review` + triangulation vs TMS case and AFS) →
  `APPROVED` | `CHANGES_REQUESTED`, before it merges into the batch trunk; then the
  lead's 3× DEV gate on the trunk; then **the lead squash-lands the trunk on `main`
  and pushes it** (`.agents/role-overrides.md` § Orchestrator slot — *Landing a
  batch*). The review and the gate are the only acceptance before `main`.
- **Landing commits link the card with `Refs #<card>` — never `Closes` / `Fixes` /
  `Resolves`.** A closing keyword in a commit pushed to `main` auto-closes the card
  on push, before the back-write and the closure record; the card stays open in
  `Ready` until a human closes it. This overrides any skill example that says
  `Closes #N` (e.g. `completing-a-task`).
- **Dispatch-prompt contract (lead):** every analyst, implementer and reviewer dispatch
  prompt carries the target + locator-policy line verbatim — see
  `.agents/role-overrides.md` § Orchestrator slot. The dispatch prompt is the gate.
- **Reviewer mechanical check:** the ladder grep in `.agents/role-overrides.md`
  § Reviewer slot — every added handle is a class-level declaration (testid, or a
  ladder rung with `suggested_testid=`); raw calls in methods/specs, `locator=` /
  `fallback=`, and positional picks are `CHANGES_REQUESTED`. Existing raw handles are
  tracked tech debt (#25/#42), not precedent.
- Commit authority: the implementer commits on the work branch the lead names
  (or creates one from `origin/main` when dispatched standalone).

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

### Closure record

The lead posts it on **every card the batch covers** once the batch is on `main` and
§ After landing step 1 (the TMS back-write) is done; each issue then moves to
**`Ready`**:

```markdown
✅ **Closure record — <CASE-ID>**

| Artifact | Where | State |
|---|---|---|
| Test | `main` @ `<sha>` — batch `<slug>` (<K> cases: <IDs>) · this case: `<node-id>` | ✅ landed (trunk `tests/batch-<slug>` kept for history) |
| Gate | 3 separate DEV runs of the batch's specs on the trunk | ✅ 3/3 green — or sanctioned RED (`#<defect>`) |
| Review | qa-engineer fresh session | ✅ APPROVED |
| AFS | `test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md` | on `main` |
| Locators | declared <D> (testid <T> · ladder <L>) · unmanaged handles Δ <±U> · ledger: <L> new `raw` rows (in `<sha>`) | pre-landing `origin/main` vs `<sha>` |
| TMS back-write | <case file> → `automation_test_id: <Form C ref>` | `build-test-index` run <URL> ✅ · TMS commit <sha> (or the manual commit for non-UI) |
| Defects filed | #<X>, #<Y> — or "none" | |

**Status:** on `main` · awaiting human acceptance (`Done`).
**Still open:** <follow-ups, or "none">
```

Every number in the record is **re-run by the lead and pasted** — never copied from
the Run Report. The issue stays `Ready` until a human closes it; `Done` stays
human-only.

The work-log comments posted during a run (started → AFS ready → review → gated →
landed) are a **narrative**. The closure record is the **artifact index**. Nobody
re-reads the narrative six months later; they read this comment to find out where the
work lives and whether it's actually finished — so a bare "✅ landed" is not a closure
record, and every row states a fact the lead verified itself, never one copied from
the AFS or the Run Report.

## Traps (cost someone an hour already)

- `requirements.txt` is **mkdocs-only**. Real deps: `pip install -e ".[reporting]"` —
  pytest won't even start without `allure-pytest` (`--alluredir` in addopts).
- venv must be Python 3.11+ (repo `.venv` is 3.13.13).
- OneDrive makes clones/fetches/installs slow — background long git commands.
- `.env.test` beats shell exports (`config.py` orders dotenv first) — edit the file.
- Always run with cwd = `elitea-testing-public/` — that's what loads `.claude/skills`,
  `.claude/rules`, `.mcp.json` and `CLAUDE.md`.
- Playwright MCP lands on the Keycloak login page ⇒ the storage state expired —
  re-run `scripts/dev_storage_state.py` (it never types credentials into the browser).

## Unconfirmed

- How often the `build-test-index.yml` bot commit races a landing push (direct push
  is new as of 2026-10-16 — the rejected-push → merge → re-land path is unmeasured).
