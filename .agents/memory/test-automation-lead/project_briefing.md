---
name: Project briefing
description: Stack overlay (test-automation) — orchestration starting context for Tal
type: project
---

## Project Knowledge

- **Your role on this team:** top-level orchestrator. There is no PM or tech-lead
  above you — you collapse both. The user launches you directly with a TMS case or
  batch; you route the analyst → implementer → reviewer pipeline, own
  test-framework architecture, and own the automation merge.
- **Read before your first dispatch:** `.agents/team-comms.md` (host + exact
  dispatch syntax — wrong syntax means your dispatch prints as plain text and
  nothing runs), `.agents/profile.md` (systems map, base URL, credentials,
  **§ Automation PR policy** — base branch / merge policy / merge strategy),
  `.agents/testing.md` (framework conventions), `.agents/test-automation.yaml`
  (TMS adapter).
- **If none of scout's files exist:** the project was never seeded — **self-orient
  by running the `seeding-a-project` skill yourself** (scout's own onboarding
  procedure, loaded on demand): seed the `.agents/*` set, ask only for blocking
  unknowns, proceed. Don't dead-stop. A deliberate `claude --agent scout` run
  stays the thorough path. See playbook § Self-orientation.
- **Match your skills to the project's systems.** Engage whichever *installed*
  skill corresponds to a system the project actually uses — the TMS adapter named
  in `.agents/test-automation.yaml`, the tracker / knowledge base in
  `.agents/profile.md`, the framework in `.agents/testing.md`. *Examples:* an Xray
  project → `xray-testing` (if installed); a Jira tracker → `atlassian-content` for
  issue writes (plain `create_issue` produces wall-of-text bodies — the skill
  formats them); a Playwright stack → `playwright-best-practices` as a worked
  reference, not a default lens. **If the matching skill isn't installed, work from
  the system's own API / the adapter verbs directly — a missing optional skill is
  never a blocker, and no single TMS (Xray included) is assumed to be present.**

## Elitea Project Specifics (seeded by scout 2026-07-10, revised 2026-10)

> **2026-10 precedence:** work targets the **DEV env as deployed** with the locator
> ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`), in this
> repo alone. Any pre-2026-10 memory — here or in `.agents/memory/` — that says
> testid-only, a locally served UI, or testid-presence-as-coverage is **superseded**:
> a missing testid is a lower rung plus a `suggested_testid=` hint, never work.

- **Base branch is `automation/factory`** — never `main`. There is NO CI on it. The merge
  gate is **yours and independent**: reviewer `APPROVED` + **your own 3 consecutive
  green runs of the spec (3 separate pytest invocations, BEFORE `gh pr merge`)** —
  semantics in `.agents/testing.md` § Merge gate, incl. the sanctioned-RED
  isolated-defect exception. The implementer's green run is NOT the gate. You merge
  (squash) small PRs autonomously.
- **Merge gate runs against DEV** (`ELITEA_URL=https://dev.elitea.ai`, `APP_PREFIX=/app`).
  Extra check: the PR diff touches this repo only, and its locator delta is declared
  (`locator_inventory.py scan` before/after; no new unmanaged handles).
- **Intake**: cases from `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/`
  (tag `automated:UI:regression`, status `draft`). Rules in
  `.agents/test-automation.yaml` § intake: dedup by `[Automate][ELITEA-<id>]` title
  search (all states), already-automated exclusion (all three: `execution_type:
  automated` + `status: ready` + non-empty `automation_test_id`), contradictory
  metadata → report, never guess. **No per-run card cap** (retired 2026-08-10,
  operator ruling) — file the whole qualifying set in one sweep; never self-split
  into small batches. Wave sizing happens *after* intake, on the campaign card.
- **Back-write post-merge**: edit the case file in `onetest-ai-tm-Elitea` — ALL FOUR:
  `execution_type: automated`, `status: ready`, `automation_test_id: <dotted pytest
  path>`, **`automation_pr: <merged PR URL>`** (#19 rework FAIL-4 = the fourth field
  forgotten).
- **HARD OVERRIDES: `.agents/role-overrides.md` § Orchestrator slot** — dispatch-prompt
  contract (every analyst/implementer/reviewer dispatch carries the DEV-target +
  ladder policy line verbatim — role-overrides.md § Orchestrator slot), sync
  `automation/factory` BEFORE the first case of a session, and the closure-record
  locator delta is a fact you VERIFY (re-run `locator_inventory.py scan`), never copy
  from the implementer (#35/#36/#37 shipped false rows by copying).
- **Closure record — the LAST comment on every automation issue.** Template:
  `.agents/workflow.md` § Closure record — factory cases (2026-10). A bare "✅ merged"
  is NOT a closure record — post the artifact index: test PR + sha, AFS path, defects
  filed, and the **Locators** row (`declared <D> (testid <T> · ladder <L>) · unmanaged
  handles Δ <±U>`, verified). Post the record, leave the issue OPEN, card → **`Ready`**
  (agent-terminal); `Done` is human-only like `Approved`. `Blocked` only for real
  blockers (`Waiting on #N`). Ladder locators are NOT a blocker — a case with no
  testid at all is complete and promotable the moment it merges.
- **Board #9 (owner EliteaAI)** is the state machine — `Approved` is human-only;
  file new issues with NO status, unassigned.
- **Identity rule (hard):** prefix EVERY tracker/board write with
  `env -u GITHUB_TOKEN` — the shared `GITHUB_TOKEN` in the env is a shared token
  and lacks `project` scope; the correct identity is **the operator's own keyring
  account** (whoever runs you on this machine — set up once via `gh auth login`).
  Plain `gh issue create` attributes your writes to the WRONG identity. If
  `env -u GITHUB_TOKEN gh auth status` shows no keyring account, stop and ask the
  operator to log in — don't fall back to the shared token for writes.
- **Dedup with the list API, never `--search`** (search index lags → duplicates like
  #17/#18): `env -u GITHUB_TOKEN gh issue list --state all --limit 200 --json title | grep "ELITEA-<id>"`.
- **Batch promotion only on explicit user request** (with clarifications): GHA runs,
  `automation/factory → main` gate (`batch-promote` skill, § Mode A whole state / § Mode B
  subset). Every test on `automation/factory` is built against DEV as deployed, so
  nothing in it can be waiting on an undeployed handle — that skill's testid
  pre-check is a sanity check, not a blocker.
- **onetest MCP write verbs** (`create_run`, `record_result`, `create_defect`, …)
  create REAL GitHub issues — never fire casually.

## My Role Focus

Run the pipeline and keep the user informed. Every routing turn must contain a
real dispatch (not a sentence about dispatching). Gate on AFS status —
`ready-for-automation` and `extend-existing` advance (see
`test-automation-workflow` § Implementer slot). Enforce No-Defect-Masking at dispatch time.
Read § Automation PR policy before every merge. After every meaningful turn,
emit a status update — the user is your only upstream channel.
