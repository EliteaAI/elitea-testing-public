---
name: Project briefing
description: Stack overlay (test-automation) — onboard a test-automation engagement; detect framework, TMS, base branch, merge policy
type: project
---

## Ownership map (WHO owns WHAT — decide before editing anything)

- **Upstream bundle** (arozumenko/sdlc-skills → bundles/test-automation): the four
  role agents, workflow/analysis skills (`test-automation-workflow`,
  `test-case-analysis`, `seeding-a-project`, `memory`, …), the sdlc-skills hooks.
  **NEVER edit.** The bundle is designed to be overridden, not patched: generic
  workflow in skills; project way-of-work in `.agents/` (`testing.md` owns locator
  strategy per the skill's own contract; `role-overrides.md` is the hook-injected
  per-slot override channel — occupy those seams instead).
- **Team-owned** (test-automation team updates them, scout only FLAGS):
  `.claude/rules/*`, project skills (`add-data-testid`, `page-object-generator`,
  `test-quality-checker`, `start-ui-localhost`, `sync-base-branches`,
  `batch-promote`, …), framework code (`automation/`), EliteaUI.
- **Scout-owned levers**: `.agents/*` (incl. role memories), `CLAUDE.md`, `AGENTS.md`.
- Precedence lesson (2026-07-14 audit, hook-verified 43/43): ambient briefings LOSE
  to the actively-executing skill text; overrides must land in the skill's declared
  deference points (`.agents/testing.md`, `.agents/role-overrides.md`) and in the
  lead's dispatch prompts — not in more memory prose.

## Project Knowledge

- **Engagement type:** Test-automation. The product under test can be **any
  stack** — your job is not to map the application architecture in depth, but to
  map the **test framework + the path from TMS case to merged automated test**.
- **Detect the test framework (any surface, no preferred order):** scan for
  whatever the project actually uses — UI runners (`playwright.config.*`,
  `cypress.config.*`, `wdio.conf.*`, Selenium), API/test frameworks
  (`pytest.ini`/`conftest.py`, JUnit/TestNG via `pom.xml`, NUnit/xUnit via
  `*.csproj`, Jest/Vitest, RestAssured, Postman/Newman), mobile (Appium,
  Espresso, XCUITest), and performance (k6, JMeter, Gatling, Locust). Record the
  framework, its version, the abstraction-layer convention (page object / API
  client / service or screen object / scenario module), the handle strategy, the
  **run command** + **CI command**, and a free-text **test-type** descriptor
  (e.g. `ui` / `api` / `mobile` / `perf` / `mixed`) as a hint for the engineer —
  not an enforced enum. Write these into `.agents/testing.md`.
- **Detect the TMS (test management system):** Xray (Jira app), Zephyr, TestRail,
  Azure Test Plans, or a markdown/`test-specs/` fallback. The TMS adapter is the
  single highest-risk unknown — if you can't confirm it, say so loudly. Record it
  in `.agents/test-automation.yaml` (`tms.adapter: …`) so Tal loads the right
  adapter skill conditionally.
- **Detect the issue tracker + automation PR policy:** base branch, merge policy
  (`auto-merge` / `human-approved` / `manual`), merge strategy
  (`squash`/`rebase`/`merge`). Record under `.agents/profile.md` § Automation PR
  policy — Tal reads it before every merge.
- **Roles & sample users:** capture the credential matrix / user sets the suite
  runs against (env-var keys, not secrets) in `.agents/profile.md`.

## Elitea Project Specifics (seeded 2026-07-10)

- **Seed complete** — CLAUDE.md rewritten, AGENTS.md project sections added (bundle
  block preserved), full `.agents/*` set written, 4 memory briefings adjusted.
- **Topology:** three siblings under the parent folder (NOT a git repo, don't init):
  this repo (`automation/base`), `../EliteaUI` (**`EliteaAI/EliteaUI` directly — no fork**;
  `automation/testids` integration branch, push but no admin),
  `../onetest-ai-tm-Elitea` (TMS, `.onetest/` cwd-relative).
- **TMS = onetest** (custom adapter, MCP server `onetest-tms` in `.mcp.json`);
  intake/back-write policy in `.agents/test-automation.yaml`.
- **Exploration shortcuts:** framework truth = `pyproject.toml` + `automation/pytest.ini`
  + `.venv/bin/pip list`; rules in `.claude/rules/`; upstream-main skills already all
  present on `automation/base` (verified — don't re-copy); case sample =
  any `.md` under `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/`.
- **Operator decisions on record:** no `env.sh` (killed — repo-relative paths instead);
  no onboarding GitHub issue (local `.agents/onboarding.md` only); memory briefings
  adjusted not replaced; leave room for non-UI surfaces (api present, mobile/perf later).
- **Identity rule:** shared `GITHUB_TOKEN` env var = shared token, no `project`
  scope; ALL tracker/board writes use `env -u GITHUB_TOKEN gh …` so they run as
  the operator's OWN keyring account (portable — whoever runs the agents, on any
  machine). Dedup via list API, never `--search` (index lag → dup #17/#18).
- **Open gaps:** no flaky-test list yet.

## My Role Focus

Onboard a test-automation engagement: produce `.agents/profile.md`,
`.agents/testing.md`, `.agents/workflow.md`, and `.agents/team-comms.md` so Tal
can dispatch the pipeline without flying blind. The framework + TMS adapter +
automation PR policy are the fields Tal depends on most — fill them or flag them
explicitly as gaps. There is no separate PM or tech-lead on this team; Tal owns
both, so your profile is his single source of project truth.
