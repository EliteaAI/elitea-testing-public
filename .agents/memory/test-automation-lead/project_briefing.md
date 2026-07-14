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

- **Base branch is `automation/base`** — never `main`. There is NO CI on it. The merge
  gate is **yours and independent**: reviewer `APPROVED` + **your own 3 consecutive
  green runs of the spec (3 separate pytest invocations, BEFORE `gh pr merge`)** —
  semantics in `.agents/testing.md` § Merge gate, incl. the sanctioned-RED
  isolated-defect exception. The implementer's green run is NOT the gate. You merge
  (squash) small PRs autonomously.
- **Merge-gate extra check:** before merging a test PR, confirm its testids are
  PUSHED to origin `automation/testids` (`cd ../EliteaUI && git fetch origin &&
  git log origin/automation/testids..automation/testids` → must be empty). A merged
  test whose testids live only on someone's laptop is red for everyone else. Note this
  gates on the **integration branch**, not on EliteaUI `main` — a testid still in an
  open draft PR is fine for `automation/base`; it only blocks the `main` promotion.
- **Intake**: cases from `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/`
  (tag `automated:UI:regression`, status `draft`). Rules in
  `.agents/test-automation.yaml` § intake: dedup by `[Automate][ELITEA-<id>]` title
  search (all states), ≤10 new cards per run, already-automated exclusion (all three:
  `execution_type: automated` + `status: ready` + non-empty `automation_test_id`),
  contradictory metadata → report, never guess.
- **Back-write post-merge**: edit the case file in `onetest-ai-tm-Elitea` —
  `execution_type: automated`, `status: ready`, `automation_test_id: <dotted pytest path>`.
- **HARD OVERRIDES: `.agents/role-overrides.md` § Orchestrator slot** — dispatch-prompt
  contract (every implementer/reviewer dispatch carries the testid-only policy line
  verbatim; the workflow skill's example ladder does NOT apply on this project),
  run `sync-base-branches` BEFORE the first case of a session (2026-07-14 audit:
  0/11 sessions did), and closure-record promotability is a fact you VERIFY against
  EliteaUI branches, never copy from the AFS (#35/#36/#37 shipped false rows).
- **Closure record — the LAST comment on every automation issue, before you close it.**
  Template + rules: `.agents/workflow.md` § Work tracking → Closure record. A bare
  "✅ merged" is NOT a closure record — post the artifact index: test PR + sha, the
  **testid draft PR on `EliteaAI/EliteaUI`**, the integration-branch state, AFS path,
  defects filed. Then the row people forget: **is it promotable?** Since the fork
  retirement a test can be merged to `automation/base` while its testids sit in an open
  draft PR — green on localhost, red on any deployed env. That case is `blocked`, not
  `completed`: **post the record and leave the issue OPEN** for the human to close once
  the testid PR lands. Worked example: issue #19 / EliteaUI#525.
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
- **Batch promotion only on explicit user request** (with clarifications): DEV restart,
  GHA runs, `automation/base → main` gate. Testids merge to EliteaUI `main` + deploy
  BEFORE the tests that use them cross to `main` — ordered, and still the invariant.
  **Testids are no longer batched** (changed 2026-07-13, fork retired): they promote
  per-case as **draft PRs** to `EliteaAI/EliteaUI` opened by `add-data-testid`. Never
  mark one ready or merge it — that's the human's call. `promote-automation-batch` is
  now tests-only; its Stage 1 just *verifies* the needed testids merged and deployed.
- **onetest MCP write verbs** (`create_run`, `record_result`, `create_defect`, …)
  create REAL GitHub issues — never fire casually.

## My Role Focus

Run the pipeline and keep the user informed. Every routing turn must contain a
real dispatch (not a sentence about dispatching). Gate on AFS status —
`ready-for-automation` and `extend-existing` advance (see
`test-automation-workflow` § Implementer slot). Enforce No-Defect-Masking at dispatch time.
Read § Automation PR policy before every merge. After every meaningful turn,
emit a status update — the user is your only upstream channel.
