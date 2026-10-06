# How This Team Works

_Seeded 2026-07-10 from operator way-of-work brief + PR sampling (merged PRs #10–15
on `main`). **Revised 2026-10 (current): one target, one repo.** Tests are built,
run and gated against the **DEV env as deployed**, with ladder locators
(`.agents/testing.md` § Locator policy), and every artifact a case produces lands in
**this** repo. Refresh when the process shifts._

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
| Output | **one** PR per case → `automation/factory`, in this repo |

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
| elitea-testing-public | `automation/factory` (`main` merged in periodically) | small PRs into it, one per test/feature area; **never PR `main` directly** |

- There is **no CI on `automation/factory`** — the green run from this machine against
  DEV before the PR is the only verification. You are the CI.
- There is **no `pending_testid` marker**. Do not invent one.
- Test work branches: `tests/<case-id>-<slug>`, cut from **`automation/factory`**.
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

### Sync: `automation/factory` ← `main`

Periodically (and before the first case of a session): merge `main` into
`automation/factory` — `sync-base-branches` Part 1. Never rebase a shared branch.

**Never shallow clones.** Check `test -f .git/shallow`; fix with `git fetch --unshallow origin`.

## The loop for one new test

1. **Refresh DEV auth** — `cd automation && ../.venv/bin/python scripts/dev_storage_state.py`
   (Playwright MCP runs `--isolated --storage-state .playwright-mcp/dev-storage-state.json`).
2. **Explore DEV** (Playwright MCP on `https://dev.elitea.ai/app`) — for each element
   the case touches, find the highest ladder rung that is unique: an existing testid
   first, then role+name, label, stable css, declared xpath.
3. **`page-object-generator` skill** — emit class-level declarations on that rung,
   every non-testid one with `suggested_testid=` (`.claude/rules/page-objects.md`).
4. **Write the test**, run it green against DEV, PR into `automation/factory`.
5. **After merge**, `locator_inventory.py sync-ledger` registers the new non-testid
   declarations as `raw` rows — the locator-debt ledger.

The loop is self-contained: one repo, one env, nothing to wait for.

## Promotion — HUMAN-TRIGGERED ONLY

What the lead performs — **only on explicit request**, never autonomously — is the
batch promotion (`batch-promote` skill): run the suite from GHA against the deployed
env, then open the `automation/factory → main` gate PR (gate = green deployed run) and
merge.

Because every test on `automation/factory` was built and gated against DEV as
deployed, the branch never depends on something that isn't live yet — the promotion
gate is the green deployed run, full stop.

## Review gates (pipeline-internal)

- Every automation PR into `automation/factory`: adversarial review by `qa-engineer`
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
- Commit authority: the implementer commits on the work branch the lead names
  (or creates one from `automation/factory` when dispatched standalone).

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

The lead posts this as the final comment on the automation issue. A case is promotable
as soon as it is merged — it was built and gated on the env it targets:

```markdown
🔗 **Closure record — <CASE-ID>**

| Artifact | Where | State |
|---|---|---|
| Test | #<N> — `tests/<case>-<slug>` → `automation/factory` | ✅ merged (`<sha>`) |
| AFS | `test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md` | on `automation/factory` |
| Locators | declared <D> (testid <T> · ladder <L>) · unmanaged handles Δ <±U> | ledger: <L> new `raw` rows |
| Defects filed | #<X>, #<Y> — or "none" | |

**Status:** merged to `automation/factory` · green on DEV · promotable.
**Still open:** <follow-ups, or "none">
```

The Locators row is the `locator_inventory.py scan` delta, **re-run by the lead on
`automation/factory` after the merge and pasted** — never copied from the Run Report.
The issue moves to **`Ready`**; `Done` stays human-only.

The work-log comments posted during a run (started → AFS ready → PR opened → review →
merged) are a **narrative**. The closure record is the **artifact index**. Nobody
re-reads the narrative six months later; they read this one comment to find out where
the work lives and whether it's actually finished — so **a bare "✅ merged" is not a
closure record**, and every row states a fact the lead verified itself, never one
copied from the AFS or the Run Report.

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

- `automation/factory` PR review-approval count (branch is new — no PR history yet;
  pipeline-internal review applies regardless).
