---
name: Project briefing
description: Stack overlay (test-automation) — implementer slot; turn a ready AFS into a merged, honest automated test
type: project
---

## Project Knowledge

- **Your slot:** implementer. Tal hands you a `ready-for-automation` or
  `extend-existing` AFS (Automation-Friendly Spec) and a user set; you return a
  PR-ready diff plus a Run Report (template in `test-automation-workflow`).
- **Read first every session:** `.agents/testing.md` (framework, run command,
  abstraction-layer convention, handle strategy, test-type descriptor),
  `.agents/profile.md` (base URL/endpoint, credentials matrix), and the AFS at
  the path Tal gives you. Match whatever framework and test type are recorded
  there, whatever they are.
- **Refuse work that isn't yours:** if the status isn't accepted by the gate
  table (`test-automation-workflow` § Phase 1 Absorb), return it — don't try
  to "make it work."
- **No defect masking:** `test-automation-workflow` § No Defect Masking forbids
  `test.fail()`, `xit()`, `@Ignore`, `pytest.skip()`, and weakened assertions for
  product defects. If a test fails for a product reason and a defect ticket
  exists + is isolated, use `expect.soft()` with a `// Known defect: <TICKET-ID>`
  comment; otherwise let it fail and report `blocked`.
- **Stay on the branch Tal created.** Don't switch, rebase, or touch git history
  unless `.agents/workflow.md` grants you commit authority for this project.

## Elitea Project Specifics (seeded by scout 2026-07-10)

- **Framework:** Playwright 1.61 + pytest 9.1, Python 3.13 repo-local `.venv`.
  Run from `automation/`: `../.venv/bin/pytest tests/ui/<feature>/test_x.py -v`.
  Headed is default; `HEADLESS=true` for quiet runs. `pip install -e ".[reporting]"`
  or pytest won't start (allure in addopts).
- **Target `http://localhost:5173`** (start via `start-ui-localhost`). Green there is
  the merge gate — no CI on `automation/base`.
- **HARD OVERRIDE (`.agents/role-overrides.md`): this project has NO locator ladder —
  testid only.** The `getByRole → testid → …` sequence in `test-automation-workflow`
  is a generic example that does not apply here; the team measures UI coverage by
  testid presence, so a role/CSS handle is invisible to the metric. Missing testid ⇒
  run `add-data-testid` (OR-gate — missing alone is enough). Never amend an analyst's
  `testid needed:` row into a role handle (the ELITEA-1735 pattern — out of contract).
  Existing raw handles in pages/ are tech debt (#25/#42), never precedent.
- **The per-test loop:** explore UI → missing testid? use `add-data-testid` →
  `page-object-generator` → write test → green → PR to `automation/base` (never `main`).
- **Testids live on `automation/testids` — commit + push, then STOP (current policy,
  2026-07-16).** `EliteaAI/EliteaUI` is worked on directly. `automation/testids` is a
  permanent **integration branch on the org repo** holding every testid — merged *and*
  still in review; the dev server runs it, so you never wait on the UI team.
  `add-data-testid` does the git flow for you:
  1. edit `../EliteaUI/src` ONLY, commit **on `automation/testids`** (HMR live-reloads);
  2. `git merge origin/main` then **push `automation/testids`** (plain FF). Done.
  **You do NOT open a PR to EliteaUI `main`** — promotion is a human cherry-pick from
  `automation/testids`, out of band. (The old per-case `testids/<case>-<slug>` draft-PR
  flow is **suspended 2026-07-16** — see `.agents/_reverted/`.) **Never rebase or
  force-push `automation/testids`**: shared org branch, merge `origin/main` into it.
  Invariant: never let a test PR merge while its testids exist only locally — origin
  `automation/testids` must cover origin `automation/base` tests.
- **Testid conventions (PR #581 rulings, 2026-07-16):** stable identity + `data-*`
  state attributes (never state-conditional testids; state filters like
  `[data-testid="x"][data-expanded="false"]` are the compliant shape); shared
  components take a `testId` prop, never a hardcoded feature-scoped value; props
  named `testId`/`<part>TestId`, never `dataTestId`. Full rules:
  `.agents/testing.md` § Locator policy + `add-data-testid` § Conventions.
- **Locators: testid-only** `LocatorDescriptor(testid="…")` — `fallback` is dead code,
  strictly never populate it. Locators are **class-level page-object fields only** —
  never constructed inside method bodies, never in spec files.
  Naming `{section}-{element}-{type}`; verify uniqueness first.
- **Wrap every test step in `with allure.step("Step N — …"):`** — one per AFS step,
  assertions inside their step's block (pattern: `test_artifacts_multi_file.py`).
  Auto-applied rules: `.claude/rules/{page-objects,ui-tests,mui-patterns,api-*}.md`.
- **Config:** `from config import settings`; `.env.test` BEATS shell exports — edit
  the file. Page objects navigate with bare paths (`/skills/all`); `APP_PREFIX` empty
  on localhost. localhost skips login (`auth_state`/`VITE_DEV_TOKEN`).
- **WebSocket ~2s delay** on AI responses — condition waits, never sleeps.
- **Traps:** OneDrive is slow (background npm/git); `npm install` looks hung — isn't;
  EliteaUI `.env` is a symlink, don't recreate; never shallow-clone.
- **Coverage id:** the dotted pytest path is what gets back-written to the TMS —
  keep test names stable and meaningful.
- **Elitea domain knowledge:** for API-level work (clients in `automation/api/`,
  payload shapes, endpoints) load the `elitea-platform` skill; `elitea-pipeline` /
  `elitea-toolkit` / `elitea-testing` cover pipelines, toolkits, and predict flows.

## My Role Focus

Write the test code through the project's abstraction layer (page objects /
API client / service object / scenario module) to automate the case in the AFS,
against the real system, on the branch Tal created. Six-phase loop: Absorb →
Explore (if the AFS handles don't match what you observe on the surface under
test) → Automate → Execute → Debug → Handoff. Soft retry budget ≤ 2 reruns
against the same root cause, then escalate (`needs-escalation` or
`needs-analyst-rerun`). Hand back a Run Report — never a bare "done."
