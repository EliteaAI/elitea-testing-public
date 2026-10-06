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

## Elitea Project Specifics (seeded by scout 2026-07-10, revised 2026-10)

> **2026-10 precedence:** work targets the **DEV env as deployed** with the locator
> ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`), in this
> repo alone. Any pre-2026-10 memory — here or in `.agents/memory/` — that says
> testid-only, a locally served UI, or testid-presence-as-coverage is **superseded**:
> a missing testid is a lower rung plus a `suggested_testid=` hint, never work.

- **Framework:** Playwright 1.61 + pytest 9.1, Python 3.13 repo-local `.venv`.
  Run from `automation/`: `../.venv/bin/pytest tests/ui/<feature>/test_x.py -v`.
  Headed is default; `HEADLESS=true` for quiet runs. `pip install -e ".[reporting]"`
  or pytest won't start (allure in addopts).
- **Target DEV — `https://dev.elitea.ai/app`, as deployed** (`ELITEA_URL`/`APP_PREFIX`
  in `.env.test`). Green there is the implementer's gate — no CI on `automation/factory`.
  Refresh `scripts/dev_storage_state.py` before browser exploration.
- **Locators follow the ladder — HARD OVERRIDE (`.agents/role-overrides.md`,
  `.claude/rules/page-objects.md`).** Use the AFS rung (climb higher if DEV allows):
  existing testid → role+name → label → stable css → declared xpath. Never positional,
  never MUI generated classes. Every non-testid declaration carries
  `suggested_testid="{section}-{element}-{type}"` (import-time validated). Class-level
  `LocatorDescriptor` / `OptionalLocatorDescriptor` / `ScopedLocator` / UPPER_CASE
  `[data-testid=` constants only — never built in methods or specs; `fallback=` /
  `locator=` are legacy, never in new code. Existing raw handles are tech debt
  (#25/#42), never precedent.
- **Your PR in this repo is the only artifact.** Nothing outside it is changed to make
  a locator work: if DEV does not serve a testid, drop a rung and write the hint.
- **The per-test loop:** explore DEV → `page-object-generator` (ladder declarations) →
  write test → green on DEV → `locator_inventory.py scan` delta → PR to `automation/factory`.
- **Wrap every test step in `with allure.step("Step N — …"):`** — one per AFS step,
  assertions inside their step's block (pattern: `test_artifacts_multi_file.py`).
  Auto-applied rules: `.claude/rules/{page-objects,ui-tests,mui-patterns,api-*}.md`.
- **Config:** `from config import settings`; `.env.test` BEATS shell exports — edit
  the file. Page objects navigate with bare paths (`/skills/all`); `APP_PREFIX=/app`
  on DEV is injected by `settings.app_base_url`.
- **WebSocket ~2s delay** on AI responses — condition waits, never sleeps.
- **Traps:** OneDrive is slow (background git commands, don't assume a hang);
  `.env.test` is a symlink, don't recreate; never shallow-clone.
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
