# AGENTS — elitea-testing

Playwright/pytest test-automation suite for the Elitea AI platform. This team turns
onetest TMS cases into merged, honest automated tests on the **`automation/base`**
branch, run against a **local `EliteaAI/EliteaUI` checkout** on the `automation/testids`
integration branch (→ DEV backend). No fork — the branch lives on the org repo.

## Tech Stack

- **Language:** Python 3.13 (repo-local `.venv`; requires ≥3.11 — system python3 may be older)
- **Test framework:** Playwright 1.61.0 + pytest 9.1.1 + pytest-playwright, pytest-xdist
- **Config:** pydantic-settings via `automation/config.py` + `automation/.env.test`
- **Reporting:** allure-pytest (mandatory — `--alluredir` in `pytest.ini` addopts), pytest-html/json
- **Lint/type:** ruff (line 120, py311 target), mypy
- **System under test:** Elitea (React UI + REST API, Keycloak auth) — locally via
  EliteaUI (`automation/testids`) on `http://localhost:5173`

## Repository Structure

```
automation/
├── config.py            ← settings loader (.env.test beats shell env)
├── conftest.py          ← fixtures, auth_state, screenshots, report paths
├── pytest.ini           ← markers (p0–p3, smoke, regression, per-feature), allure addopts
├── api/                 ← REST API clients (Bearer + cookie-based)
├── pages/               ← page objects — testid-only LocatorDescriptor
├── components/          ← UI component helpers
├── fixtures/  utils/    ← shared fixtures & helpers
└── tests/
    ├── ui/<feature>/    ← agents, skills, pipelines, chat, toolkits, admin, voice, …
    ├── api/             ← API tests
    └── unit/            ← framework unit tests
.claude/rules/           ← auto-applied coding rules (page-objects, ui-tests, api-*, mui)
.claude/skills/          ← project skills incl. start-ui-localhost, add-data-testid,
                           page-object-generator, test-automation pipeline skills,
                           and Elitea domain knowledge: elitea-platform (REST API
                           reference — load first), elitea-pipeline, elitea-toolkit,
                           elitea-testing (agent/pipeline run & debug)
.agents/                 ← seeded team config (profile, workflow, testing, TMS yaml, memory)
docs/                    ← mkdocs site (requirements.txt is mkdocs-ONLY, not test deps)
```

## Build & Run

```bash
.venv/bin/pip install -e ".[reporting]"                 # install (reporting extra required)
cd automation
../.venv/bin/pytest tests/ui/smoke/test_ui_smoke.py -v  # one file
HEADLESS=true ../.venv/bin/pytest -m smoke -v           # smoke suite (<5 min)
../.venv/bin/ruff check .                               # lint
```

Local UI: `cd ../EliteaUI && npm run dev` → `http://localhost:5173`
(or the `start-ui-localhost` skill).

## Environment

`automation/.env.test` is a symlink to the master secrets file in the parent folder.
Key names (values never documented): `ELITEA_URL`, `APP_PREFIX`, `ELITEA_API_BASE`,
`ELITEA_PROJECT_ID`, `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`, `ELITEA_API_TOKEN`.
See `.agents/profile.md` § Roles & sample users.

## Testing & Conventions

Full detail in `.agents/testing.md` (framework, run commands, **locator policy —
testid-only, there is no ladder**, AFS conventions) and `.agents/conventions.md`
(pointers to `.claude/rules/*`). Hard per-role overrides: `.agents/role-overrides.md`
— it wins over any skill's defaults/examples. Team goal: `data-testid` on every
element new tests touch; UI-automation coverage is measured by testid presence.
Way of work — the two-branch dance, sync procedures, batch operations — in
`.agents/workflow.md`. Three-repo topology in `.agents/architecture.md`.

## CI/CD

GitHub Actions workflows run the suite against deployed envs (`test-ui-dev.yml`,
`test-ui-next.yml`, `test-ui-stage2.yml`, `test-api.yml`) — **that is not the local
loop's job**. There is NO CI on `automation/base`: the engineer running tests green
locally before PR is the only verification gate.

<!-- BUNDLE:test-automation START -->
# Test Automation Team — shared conventions

This is an **automation-focused team**: it turns TMS (test management system)
cases into merged, honest automated tests — **universal across any framework,
any test type (UI, API, mobile, performance, …), and any TMS.** The team matches
whatever the project already uses rather than imposing a tool. These are
team-wide defaults — scout refines them per project in `AGENTS.md`, which always
wins over this file.

## Team shape

- **`test-automation-lead` (Tal)** is the orchestrator. On this team he collapses
  the PM and tech-lead roles: he runs the batch pipeline, owns test-framework
  architecture decisions, and owns the automation merge gate. **The user launches
  Tal directly** (`claude --agent test-automation-lead`) for automation work —
  there is no PM above him. He is a top-level orchestrator, not a subagent.
- **`scout`** seeds the project first (`claude --agent scout`): framework, TMS
  adapter, base branch, merge policy, credential matrix. If the project isn't
  seeded, Tal **self-orients by running the same `seeding-a-project` skill
  himself** (asking only for blocking unknowns) — he never dead-stops; a
  deliberate `claude --agent scout` run stays the thorough path.
- **`qa-engineer` (Sage)** fills two slots — **analyst** (writes the AFS) and
  **reviewer** (adversarial, static test-honesty review — no execution, fresh
  session).
- **`test-automation-engineer` (Axel)** fills the **implementer** slot — writes
  the test code through the project's abstraction layer (page objects /
  API client / service object / scenario module), fixtures, and specs; returns
  a Run Report.

## The pipeline

```
User launches Tal directly (claude --agent test-automation-lead) → drops a batch
of TMS cases (a single case is a batch of one)
  Tal → Intake: one TMS sweep, dedup against existing AFS + tracker, case
        snapshots to `.agents/automation/<slug>/cases/<ID>.md`, cluster
        similar cases
      → THE RUN — on Claude Code one Workflow call; elsewhere the same phases
        as sequential dispatches:
          · ONE UNIT AT A TIME — nothing overlaps. A working tree has one
            state at a time, so ordering is what keeps slots coherent:
            always return the tree to the batch trunk, always branch from it
          · Analyse: qa-engineer + test-case-analysis, on the trunk
            → AFS + status per case, COMMITTED by the analyst itself;
              `ready-for-automation` and `extend-existing` advance,
              everything else ends there
          · Build, on a branch cut FROM the trunk:
            Implementer (test-automation-engineer + test-automation-workflow,
            green ONCE) → Reviewer (qa-engineer FRESH session + code-review,
            STATIC — no execution) → fix rounds until the reviewer APPROVES:
            a blocker nobody acted on (`unaddressed`) earns another round;
            stop only when every survivor is `persists` (attempted, still
            failing) or `external` (not fixable on this branch)
          · Merge back into `tests/batch-<slug>` as soon as review approves;
            semantic conflicts park the unit; the tree returns to the trunk
          · Gate — its own agent, never the implementer: the batch's specs
            together, N consecutive green (default 3)
          · Report — the run's single disk write:
            `.agents/automation/<slug>/report.{json,md}`, one row per case
      → Close: Tal reads the report — merges the `automated` cases, routes the
        findings, classifies a red gate, back-writes the TMS/tracker once,
        replans whatever isn't done
```

## Working agreements (team-wide)

- **AFS status is contract law.** `ready-for-automation` and `extend-existing`
  advance to the implementer (see `test-automation-workflow` § Implementer slot
  for the status table). Everything else gets handled per that status table,
  never forwarded.
- **No defect masking.** `test.fail()`, `xit()`, `@Ignore`, `pytest.skip()`, and
  weakened assertions for product defects are forbidden. A product bug means file
  a ticket and either `expect.soft()` (isolated, ticketed) or a natural fail
  (`blocked`) — never a hidden green.
- **A bundle install/update reaches NEW sessions only.** Skills and agent
  definitions load once at session start; `npx … init --update` changes the
  disk, not a running lead's context. After any update: finish or park the
  in-flight batch, then start a fresh session — never expect updated doctrine
  mid-session (field-verified failure mode).
- **Workflows are the default batch path on Claude Code — standing opt-in.**
  A batch of ANY size — one case included — runs via the shipped batch workflows
  (`batch-build` / `batch-campaign` under the `test-automation-workflow`
  skill; `batch-integrate` and `batch-stabilize` are repair tools, not stages). Installing this bundle and handing the
  lead a batch IS the explicit multi-agent orchestration opt-in the Workflow
  tool's gate requires — this instruction satisfies it; the lead does not ask
  again and does not re-litigate the gate. Fall back to sequential dispatches
  only for the cases listed under § When NOT to use it in the
  `test-automation-workflow` skill's `references/workflow-accelerant.md`:
  an unseeded project, no Workflow tool on this host, or an operator who wants
  to supervise step by step. A batch of one is NOT an exception — it costs ~8-10
  orchestrator turns conversationally against 2 through the workflow.
  The contracts are identical on both paths, so nothing forks.
- **Reuse to travel and to know — never to conclude.** Analysts and
  implementers aggressively reuse the suite to REACH areas fast (framework
  auth state, existing specs/page objects as transit) and to KNOW handles
  (digests, prior AFS) — but coverage judgments stand on your own execution.
  The two verdicts have different reach, because one of them CLOSES a case:
  `extend-existing` may target a spec merged to base **or already on this
  batch's trunk** (it produces work that shares the batch's fate);
  `already-covered` may target **only** a spec merged to base, because it is
  terminal and drops the case out of the remainder. Never target a same-batch
  AFS that has not merged (same-batch similarity is a cluster/family matter). Transit is not execution — the case's own steps are still run and
  observed live; a broken transit path is flagged as a possible regression.
- **Dispatch is the work.** A routing turn without an actual subagent dispatch in
  the same reply did nothing.
- **Done means green AND tracked.** A `completed` case is clean-green in CI, or
  red-for-a-real-product-bug with a filed, linked ticket. A `test.fail()`-masked
  green is `blocked`.
- **TMS-agnostic.** The project's TMS adapter skill loads only when the project
  declares its adapter (e.g. `tms.adapter: xray` → `xray-testing`); Zephyr /
  TestRail / Azure / markdown all work without any special skill. No single TMS
  is assumed to be present.
- **No unsolicited integrations.** Scaffolding or setup wires only what's needed
  to run tests. A TMS/result reporter, analytics, or any network-calling hook is
  added only when the task asks or the project declares it — and then gated so it
  never fires on a local run. Never silently wire one.
- **External writes follow the seeded way of work.** TMS execution updates,
  defect tickets, and status / progress posts to a tracker are real parts of the
  job — but **whether and how the project does them is decided during seeding and
  recorded in `.agents/*`**, not improvised per run. Perform each per the seeded
  policy: `.agents/test-automation.yaml` § `tms` (sync or not, which adapter),
  `.agents/profile.md` § Bug filing (file tickets? where? what style?) + §
  Automation PR policy + § Status reporting, `.agents/workflow.md`. Do the writes
  the seed establishes; **skip the ones it doesn't** (a markdown / no-TMS project
  does no execution back-write; a project with no tracker filing files no
  tickets). Don't invent a write the seed didn't set up, and don't drop one it
  did. Onboarding itself only *captures* this policy — it doesn't perform the
  writes.
<!-- BUNDLE:test-automation END -->
