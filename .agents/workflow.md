# How This Team Works

_Seeded 2026-07-10 from operator way-of-work brief + PR sampling (merged PRs #10–15
on `main`). **Revised 2026-10: one target, one repo.** Tests are built,
run and gated against the **DEV env as deployed**, with ladder locators
(`.agents/testing.md` § Locator policy), and every artifact a case produces lands in
**this** repo. **Revised 2026-10-16 (current): base is `main`, agents open PRs, humans
merge** — `automation/factory` is frozen history. Refresh when the process shifts._

## Git host

- **Host**: GitHub · **CLI**: `gh` · **Unit of change**: Pull Request
- **Remote**: this repo, `EliteaAI/elitea-testing-public` (admin). It is the only
  repo a case commits to.

## One loop, one repo (2026-10)

| | |
|---|---|
| Input | TMS cases |
| Target | DEV — `https://dev.elitea.ai`, `APP_PREFIX=/app` |
| Locators | the ladder — existing testid → role+name → label → css → xpath, each non-testid declaration carrying `suggested_testid=` |
| Output | **one** PR per batch → `main`, in this repo (a batch of one = one case) — opened by the factory, **squash-merged by a human** |

**Why it looks like this.** An earlier loop coupled every case to the frontend repo: a
test needed a testid, the testid needed a frontend change, that change needed days of
review, and each case produced two PRs in two repos. Building on DEV with the ladder
removes the coupling — a test is green on the env it targets the day it merges, and a
missing testid is a `suggested_testid=` hint rather than a blocker. Converting those
hints into real testids is a separate, on-request process with its own session and its
own procedure (`.claude/skills/migrate-locators-to-testids`); it never runs as part of
a case and needs no space in your context.

## Branching

| Repo | Long-lived branch | Rule |
|---|---|---|
| elitea-testing-public | `main` | one PR per batch into it (the gated `tests/batch-<slug>` trunk; a batch of one is one case branch); **agents open them, a human squash-merges them** — agents never `gh pr merge` into `main`, never push to it |

- There is **no CI on PRs into `main`** — the green run from this machine against
  DEV (implementer) and the lead's 3× gate before hand-off are the verification. You
  are the CI; the human merge is the acceptance step.
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
| Review a PR's code | Static review — **no execution, no checkout** (reviewer slot is static by contract) |
| Run a case's tests | The case's own branch, checked out normally, one at a time |
| Work another branch mid-task | Commit or park current work, `git checkout`, then return |
| Parallel work on shared files | Don't — serialize it. Two agents in one tree collide. |

If a checkout genuinely must move while another agent depends on the current one, that
is a **coordination** problem: finish or park the in-flight work first, don't fork the
tree.

### Keeping an open PR current

There is no base-branch sync any more — branches are cut from `origin/main` directly.
What drifts now is an **open PR waiting for a human**: when `main` moves under it in a
way that touches its files, or GitHub reports it conflicting, merge `origin/main` into
the PR branch (never rebase, never force-push), re-run the gate, and post the fresh
result on the PR. Cases that depend on each other belong in the same batch (one PR);
a case that needs another batch's still-open PR is parked `Blocked` — "Waiting on
#N" — never stacked on the unmerged branch.

**Never shallow clones.** Check `test -f .git/shallow`; fix with `git fetch --unshallow origin`.

## The loop for one new test

1. **Refresh DEV auth** — `cd automation && ../.venv/bin/python scripts/dev_storage_state.py`
   (Playwright MCP runs `--isolated --storage-state .playwright-mcp/dev-storage-state.json`).
2. **Explore DEV** (Playwright MCP on `https://dev.elitea.ai/app`) — for each element
   the case touches, find the highest ladder rung that is unique: an existing testid
   first, then role+name, label, stable css, declared xpath.
3. **`page-object-generator` skill** — emit class-level declarations on that rung,
   every non-testid one with `suggested_testid=` (`.claude/rules/page-objects.md`).
4. **Write the test**, run it green against DEV, PR into `main` (a human merges it).
5. **After a human merges**, `locator_inventory.py sync-ledger` registers the new
   non-testid declarations as `raw` rows — the locator-debt ledger (part of
   § After a human merges).

The loop is self-contained: one repo, one env — the only wait is the human merge.

## Promotion — none for this repo

Every batch PR targets `main` and a human merges it, so there is nothing to promote in
`elitea-testing-public`. `batch-promote` survives only for the testid integration
branches (`automation/testids` in `EliteaUI` / `elitea_assistant`) — human-triggered
only, as before.

## After a human merges

Nothing in the pipeline runs the moment a human clicks merge, so the post-merge work is
picked up afterwards — by the `postmerge` loop (`factory/loops/EXAMPLE-postmerge.md`),
or by the lead at the start of a session: list `Ready` cards whose linked PR is
`MERGED` into `main` (one batch PR covers several cards — every one of them), and for
each card:

1. TMS back-write (`.agents/test-automation.yaml` § `backwrite_on_done`) + rebuild
   `index.json`.
2. Once per tick, after all back-writes: `locator_inventory.py scan` on a fresh
   `origin/main` + `sync-ledger`. The ledger
   change reaches `main` like everything else — one `chore/ledger-sync-<date>` PR
   (refreshed, never duplicated) that a human merges.
3. Post the **merge record** (below) on the issue. The card stays `Ready` until the
   human closes it (`Done` stays human-only).

A `Ready` card whose PR was **closed unmerged** is not done — comment, move it to
`Blocked`, and let a human decide.

## Review gates (pipeline-internal)

- Every unit of an automation batch: adversarial review by `qa-engineer`
  (fresh session, `code-review` + triangulation vs TMS case and AFS) →
  `APPROVED` | `CHANGES_REQUESTED`, before it merges into the batch trunk; then the
  lead's 3× DEV gate on the trunk; then the lead opens the ONE batch PR into `main`,
  ready for review, and **hands it to a human, who squash-merges it**.
- **PR bodies link the card with `Refs #<card>` — never `Closes` / `Fixes` /
  `Resolves`.** A closing keyword would auto-close the card the moment the human
  merges, skipping the post-merge back-write and the merge record; the card stays
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

### Closure record — two parts

**Hand-off record** — the lead posts it on **every card the batch PR covers** when the
PR is gated and handed to a human; each issue moves to **`Ready`**:

```markdown
🔗 **Hand-off record — <CASE-ID>**

| Artifact | Where | State |
|---|---|---|
| Test | #<N> — `tests/batch-<slug>` → `main` (batch of <K>: <IDs>) · this case: `<node-id>` | 🟡 open, ready for human squash-merge (head `<sha>`) |
| Gate | 3 separate DEV runs of the batch's specs on the trunk | ✅ 3/3 green — or sanctioned RED (`#<defect>`) |
| Review | qa-engineer fresh session | ✅ APPROVED |
| AFS | `test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md` | on the PR branch |
| Locators | declared <D> (testid <T> · ladder <L>) · unmanaged handles Δ <±U> | vs `origin/main` |
| Defects filed | #<X>, #<Y> — or "none" | |

**Status:** gated on DEV · awaiting human merge.
**Still open:** <follow-ups, or "none">
```

**Merge record** — posted after a human merges (§ After a human merges):

```markdown
✅ **Merge record — <CASE-ID>**: batch PR #<N> squash-merged to `main` (`<sha>`) by @<human>.
TMS back-write: <case file> → `automation_test_id: <Form C ref>` (<TMS commit/PR>).
Locators on `main`: <scan delta pasted> · ledger: <L> new `raw` rows.
```

Every number in either record is **re-run by the lead and pasted** — never copied from
the Run Report. The issue stays `Ready` until a human closes it; `Done` stays
human-only.

The work-log comments posted during a run (started → AFS ready → PR opened → review →
handed off → merged) are a **narrative**. The two records are the **artifact index**.
Nobody re-reads the narrative six months later; they read these two comments to find
out where the work lives and whether it's actually finished — so a bare "✅ PR opened"
is not a hand-off record, and every row states a fact the lead verified itself, never
one copied from the AFS or the Run Report.

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

- Human merge cadence for factory batch PRs into `main` (flow is new as of 2026-10-16
  — how long `Ready` cards wait, and how large a batch PR a human can comfortably
  review, is unmeasured).
