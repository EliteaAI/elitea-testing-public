---
project: elitea-testing
team: elitea-test-automation
issue-tracker: https://github.com/EliteaAI/elitea-testing-public/issues
default-branch: automation/base
languages: [python]
---

# Elitea Test Automation — project card

Playwright/pytest suite automating onetest TMS cases against the Elitea platform,
run locally against `EliteaAI/EliteaUI` on its `automation/testids` integration
branch. **Team goal: `data-testid` on every element new tests touch — UI-automation
coverage is measured by testid presence** (locator policy: `.agents/testing.md`).
Currently UI-focused; API tests exist and
other surfaces (mobile, perf) may be added later — nothing in this seed assumes
UI-only.

## Tech Stack
- Playwright 1.61.0 + pytest 9.1.1 (Python 3.13, repo-local `.venv`)
- Page objects with testid-only `LocatorDescriptor`
- allure-pytest reporting (mandatory install extra)

## Build & Test
- Install: `.venv/bin/pip install -e ".[reporting]"`
- Test (from `automation/`): `../.venv/bin/pytest tests/ui/smoke/test_ui_smoke.py -v`
- Lint: `../.venv/bin/ruff check .`

## Environment & access

- **Primary base URL:** `http://localhost:5173` — `EliteaAI/EliteaUI` on `automation/testids`,
  pointing at the DEV backend. `ELITEA_URL` in `.env.test` controls it; `APP_PREFIX`
  empty on localhost, `/app` on deployed envs.
- **API base:** `ELITEA_API_BASE` (DEV backend).
- Deployed envs `dev.elitea.ai` / `next.elitea.ai` exist but are **CI's job** — the
  local pipeline never targets them for verification.

### Repo access map

| Repo | Access | Role |
|---|---|---|
| `EliteaAI/elitea-testing-public` | admin | this repo — tests, tracker, board |
| `EliteaAI/onetest-ai-tm-Elitea` | admin | TMS — cases, runs, defects |
| `EliteaAI/EliteaUI` | **push, no admin** | UI — testid work directly on `automation/testids`; `main` owned by the UI team |
| `EliteaAI/elitea_assistant` | **push, no admin** | Support Assistant (connected repo, `@eliteaai/elitea-assistant`) — testids in ITS source on its own `automation/testids` integration branch; consumed by EliteaUI as a git-dep. See `.agents/workflow.md` § Connected repos. |
| ~~`bermudas/EliteaUI`~~ (fork) | RETIRED 2026-07-13 | no longer part of the workflow — never push to it |

### Roles & sample users

Env-var names only — **never secrets**. All resolve from `automation/.env.test`
(symlink to the master file in the parent folder).

| Role key | Purpose | Credential env vars |
|----------|---------|--------------------|
| `${TEST_USER}` | Standard authenticated user (Keycloak) | `TEST_USER_EMAIL`, `TEST_USER_PASSWORD` |
| API token | Direct API calls | `ELITEA_API_TOKEN` |
| localhost dev auth | `auth_state` skips login on localhost | `VITE_DEV_TOKEN` (in `EliteaUI/.env`) |
| GitHub toolkit test data | Fed INTO the Elitea UI/API to create GitHub toolkits & credentials (toolkit tests, `github_credential` fixture, guardrails tests — they SKIP without it) | `GIT_HUB_TOKEN` (in `.env.test`) |
| Jira toolkit test data | Same pattern for Jira toolkits | `JIRA_USERNAME`, `JIRA_API_KEY` |

**Do not confuse the GitHub tokens.** `GIT_HUB_TOKEN` (`.env.test`) is *test data for
the system under test* — it configures toolkits inside Elitea and must stay. The
shell's `GITHUB_TOKEN` is infra (github MCP server) and is exactly the token the
Identity rule below excludes from `gh` tracker writes. Neither is a tracker identity.

## Project systems

### Issue tracker
- **System**: github-issues
- **Project / board key**: `EliteaAI/elitea-testing-public` + GitHub Projects board **#9** (owner `EliteaAI`)
- **URL**: https://github.com/EliteaAI/elitea-testing-public/issues · https://github.com/orgs/EliteaAI/projects/9
- **Board status machine**: `Todo` → `Approved` (HUMAN-ONLY) → `In Progress` →
  **`Ready`** (agent-terminal: test merged + closure record with *verified*
  promotability posted, issue OPEN, awaiting external merges / human acceptance)
  → `Done` (HUMAN-ONLY: promotable/accepted, human closes the issue). `Blocked`
  is a side state for REAL blockers only (`Waiting on #N`). Agents never set
  `Approved` or `Done` — humans own both ends. New issues auto-add
  to the entry column — file them unassigned, set no status.
- **Load-bearing labels**: `question` (parked decision) and `bug` (product defect) mark
  issues the factory must NEVER work as tasks; body must name origin ("Found while working #N").
- **Identity rule — NEVER write to the tracker as the shared token.** The shell /
  `.env` exports `GITHUB_TOKEN` (a shared token, wrong attribution, no `project`
  scope) which overrides the keyring login. **Every `gh` command that writes issues,
  comments, or board items MUST be prefixed with `env -u GITHUB_TOKEN`** so it runs
  as **the operator's own keyring account** — whoever is running the agents on this
  machine, not any specific person and not the shared token:
  `env -u GITHUB_TOKEN gh issue create …`, `env -u GITHUB_TOKEN gh project item-edit …`.
  Per-machine setup (once): `gh auth login` with your own account (scopes: `repo`,
  `project`, `read:org`), then `env -u GITHUB_TOKEN gh auth status` must show YOUR
  account as active. The shared `GITHUB_TOKEN` stays exported only for `.mcp.json`'s
  github MCP server.
- **Board #9 holds ONLY `EliteaAI/elitea-testing-public` issues.** Never
  `gh project item-add` an issue from another repo (`elitea_issues`,
  `elitea_support`, EliteaUI, …) — it duplicates a defect the originating card
  already tracks, in a repo this board has no workflow states for, and lands in
  `Todo` (the reproduce loop's trigger column). Cross-repo visibility comes from a
  **back-link comment**, never a second card. (Two real incidents: elitea_support#1231
  via a stale support-agent config; elitea_issues#6039 via `file-app-bug` Step 4 —
  both removed.)
- **Dedup rule (intake cards)**: never `--search` — the index lags minutes and
  causes duplicate filings (#17/#18). Exact command:
  `.agents/test-automation.yaml` § `intake.dedup` (single source).
  *Bug* dedup is a different, wider check — see § Bug filing below.

### Test Management System (TMS)
- **System**: onetest (custom — markdown cases + GitHub-issue executions, MCP server `onetest-tms`)
- **Cases repo**: `EliteaAI/onetest-ai-tm-Elitea` (clone must sit as sibling `../onetest-ai-tm-Elitea`,
  aka `$OT_REPO_ROOT` — several scripts read `.onetest/` relative to cwd)
- **Configured in**: `.agents/test-automation.yaml` (adapter + transport + intake/back-write policy)

### Task source (where work to automate comes from)
- **Intake**: tms-folder — cases as `.md` files in
  `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/` (other folders may come later)
- **Selector**: tag `automated:UI:regression`, status `draft`
- **Intake rules**: see `.agents/test-automation.yaml` § intake (dedup key
  `[Automate][ELITEA-<id>]` in title, ≤10 new cards per run, already-automated
  exclusion, contradictory-metadata → report not guess)

### Knowledge base
- **System**: readme-only + `docs/` (mkdocs) + `onetest-ai-tm-Elitea/docs/` for TMS docs
- **Elitea domain knowledge — installed skills** (from `bermudas/EliteaSkills`):
  `elitea-platform` (REST API reference, auth, endpoints — **load first** for any
  Elitea API question), `elitea-pipeline` (pipeline YAML/node types),
  `elitea-toolkit` (toolkit creation/linking), `elitea-testing` (predict endpoint,
  agent/pipeline run & debug). Use them to find exact endpoint paths, payload
  shapes, and platform semantics instead of reverse-engineering.

### Bug filing (defects discovered during analysis/runs)
- **Style**: github-issue, labelled **`bug`**, in `EliteaAI/elitea-testing-public`
- **Bundling policy**: strict-per-bug
- **Link originating case**: yes — body names the TMS case ID and "Found while working #<task>"
- **Dedup before filing (light — one command, not a research project).** Before
  filing a bug, check whether it is already tracked. Use the real-time list API,
  never `--search` (index lags → the #17/#18 dup filings):
  `env -u GITHUB_TOKEN gh issue list --repo EliteaAI/elitea-testing-public --label bug
  --state all --limit 300 --json number,title,state` then keyword-match the
  component + symptom locally. One pass; if nothing obvious matches, file and move on.
  - **Duplicate = same object + same trigger + same expected/actual.** Anything less
    is NOT a duplicate:
    - *Same pattern, different object/case/surface* ⇒ **sibling**, not duplicate.
      File it, and cross-link both ways (`sibling of #N — same pattern, different
      <object>`). Bucket-delete-toast vs files-delete-toast are siblings, not dupes —
      collapsing siblings destroys coverage.
    - *Match is CLOSED and it reproduces again* ⇒ **regression**, not duplicate. New
      issue, body says "regression of #M". Never re-mark a closed issue as a dupe.
    - *Unsure* ⇒ **file it**, with "possible duplicate of #N" in the body. A lost bug
      costs far more than a linked maybe-dupe a human merges in seconds. Dedup is
      never a filter that silently drops a finding.
  - **A real duplicate found BEFORE filing ⇒ do not file.** Instead comment the new
    occurrence on the existing issue (which case/step hit it + embedded evidence) so
    evidence consolidates instead of splitting, and say "not filed — already tracked
    as #N" in your Run Report / AFS.
  - **Two issues already exist ⇒ mark, never close.** Survivor is the **lower issue
    number** (oldest wins; migrate the newer's better evidence onto it first if any).
    On the newer: add the `duplicate` label + a comment "Duplicate of #M — <why>",
    and leave it **OPEN**. Agents never close issues (`Done` is human-only) — the
    `duplicate` label IS the human's sweep queue (`gh issue close <n> --reason duplicate`).
- **Never mask**: no `test.fail()`/skip/weakened asserts; isolated defect →
  `expect.soft()` with ticket linked; blocking defect → natural fail + `blocked`
- **Two trackers, two purposes** — do not conflate:
  - *This repo's `bug` issues* (`EliteaAI/elitea-testing-public`) — the lightweight,
    localhost, filed-during-analysis defect notes above. **Unchanged — stays light;
    analysis is not distracted by DEV verification.**
  - *Application-bug tracker* `EliteaAI/elitea_issues` — the externally-visible tracker
    the dev team reads. A defect reaches it only after DEV verification + an explicit ask.
- **Escalation path (know it exists; act only on an explicit ask).** A confirmed bug
  (DEV-verified via the `reproduce-elitea-bug` skill, verdict `repro:confirmed`) is
  escalated to `elitea_issues` via the `file-app-bug` skill — **ONLY on an explicit
  user request.** Agents NEVER file to `elitea_issues` on their own initiative: surface
  the confirmed bug and the escalation option, and wait. The *procedure* lives in those
  two on-demand skills (not here) so automation-analysis sessions never load it.

### Test case storage
- **Source of truth**: tms (onetest markdown files in `onetest-ai-tm-Elitea`)
- **AFS location**: `test-specs/<feature>/` in this repo (analyst output, git-tracked)

### Status reporting
- **TMS execution back-write**: yes — post-merge, orchestrator edits the case file in
  `onetest-ai-tm-Elitea`: `execution_type: automated`, `status: ready`,
  `automation_test_id: <dotted tests.-rooted path>` — NOT the `.py::` node-id form and NOT
  `automation.`-prefixed; both fail CI correlation (see `.agents/test-automation.yaml`
  § backwrite_on_done)
- **Comment PR link on the originating issue**: yes — work-log comments
  (🔧 started / 📝 update / 🚫 blocked / ✅ done) + PR link on the tracking card
- **Board tracking**: assign self, move to `In Progress` when starting; `Blocked` +
  "Waiting on #N" when parked; `Done` only after merge + closure record (verified
  promotability — see workflow.md; never copy the implementer's claim)
- **Gating**: no automated result reporters wired into pytest; back-writes are
  explicit orchestrator actions, never per-local-run

### Automation PR policy
- **Base branch for automation PRs**: `automation/base` (long-lived, cut from `main`).
  **Never** open a PR against `main`. Feature branches cut from `automation/base`,
  one PR per test / feature area, small.
- **Merge policy**: auto-merge into `automation/base` — the orchestrator merges once the
  test ran green locally + review passed. There is NO CI on `automation/base`; the
  green local run IS the gate.
- **Testids to `EliteaAI/EliteaUI` `main`**: **agents do NOT open `main` PRs (suspended
  2026-07-16 — `.agents/_reverted/`).** Testids are committed + **pushed** to
  `automation/testids` and stop there; a **human** cherry-picks them to `main` out of band.
- **Batch promotion is human-triggered only** (never autonomous): DEV restart, GHA runs,
  `automation/base → main` gate PR. Testids are NOT batched any more — they promote
  per-case. See `.agents/workflow.md` § Promotion.
- **Squash / rebase / merge**: squash (default) for small PRs into `automation/base`.

### Additional notes
- Parent folder of this clone = the workspace (plain directory, NOT a git
  repo — never `git init` it; the three-sibling layout is load-bearing).
- No `env.sh` — paths are repo-relative (`../EliteaUI`, `../onetest-ai-tm-Elitea`);
  `GITHUB_TOKEN` comes from the master `.env` when needed by `.mcp.json`.
- Repos sit on OneDrive — git/npm operations are slow, background them, don't assume hangs.
- Never shallow-clone any of the three repos (`test -f .git/shallow` to check;
  `git fetch --unshallow origin` to fix) — shallow clones break history-walking merges.
- **`automation/testids` is a shared org branch: never rebase it, never force-push it.**
  Sync with `git merge origin/main`.
