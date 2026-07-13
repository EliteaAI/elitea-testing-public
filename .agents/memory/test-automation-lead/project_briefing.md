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

## Elitea Project Specifics (seeded by scout 2026-07-10)

- **Base branch is `automation/base`** — never `main`. There is NO CI on it: the
  implementer's green local run against `http://localhost:5173` + reviewer approval
  IS your merge gate. You merge (squash) small PRs autonomously.
- **Merge-gate extra check:** before merging a test PR, confirm its testids are
  PUSHED to origin `automation/testids` (`cd ../EliteaUI && git fetch origin &&
  git status` / compare with `git log origin/automation/testids..automation/testids`
  → must be empty). A merged test whose testids live only on someone's laptop is
  red for everyone else.
- **Intake**: cases from `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/`
  (tag `automated:UI:regression`, status `draft`). Rules in
  `.agents/test-automation.yaml` § intake: dedup by `[Automate][ELITEA-<id>]` title
  search (all states), ≤10 new cards per run, already-automated exclusion (all three:
  `execution_type: automated` + `status: ready` + non-empty `automation_test_id`),
  contradictory metadata → report, never guess.
- **Back-write post-merge**: edit the case file in `onetest-ai-tm-Elitea` —
  `execution_type: automated`, `status: ready`, `automation_test_id: <dotted pytest path>`.
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
- **Batch operations only on explicit user request** (with clarifications): EliteaUI
  upstream PR, DEV restart, GHA runs, `automation/base → main` gate. Testids merge
  upstream + deploy BEFORE tests cross to `main` — paired and ordered.
- **onetest MCP write verbs** (`create_run`, `record_result`, `create_defect`, …)
  create REAL GitHub issues — never fire casually.

## My Role Focus

Run the pipeline and keep the user informed. Every routing turn must contain a
real dispatch (not a sentence about dispatching). Gate on AFS status —
`ready-for-automation` and `extend-existing` advance (see
`test-automation-workflow` § Implementer slot). Enforce No-Defect-Masking at dispatch time.
Read § Automation PR policy before every merge. After every meaningful turn,
emit a status update — the user is your only upstream channel.
