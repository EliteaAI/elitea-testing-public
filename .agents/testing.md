# Testing

> Scout-generated 2026-07-10. Update when the framework, run commands, or
> conventions change. Analyst and implementer read this before touching tests.

## Framework

- **Name + version:** Playwright 1.61.0 + pytest 9.1.1 (pytest-playwright, pytest-xdist),
  Python 3.13.13 in repo-local `.venv`
- **Test type:** `mixed` — **ui is primary** (`tests/ui/<feature>/`), **api present**
  (`tests/api/`), framework unit tests (`tests/unit/`). Room reserved for more surfaces
  later (mobile / perf) — match the surface per case, don't assume UI.
- **Why this stack:** matches the Elitea React UI; API clients (Bearer + cookie auth)
  already exist in `automation/api/`.

## Run commands

All from `automation/` (cwd matters — `pytest.ini`, `conftest.py`, `.env.test` live there):

- **Single test, local:** `../.venv/bin/pytest tests/ui/skills/test_x.py::TestClass::test_case -v`
- **One file:** `../.venv/bin/pytest tests/ui/smoke/test_ui_smoke.py -v`
- **Smoke suite:** `HEADLESS=true ../.venv/bin/pytest -m smoke -v` (<5 min)
- **Headed vs headless:** headed is the **default** (`config.py: headless=False`);
  `HEADLESS=true` for quiet runs. CI-on-deployed-envs uses the GHA workflows
  (`.github/workflows/test-ui-*.yml`) — not the local loop's concern.
- **Local verification gate:** there is no CI on `automation/base`; a test must run
  green locally against `http://localhost:5173` before its PR. That run IS the merge gate.

## Structure

- **Tests live in:** `automation/tests/ui/<feature>/` (agents, skills, pipelines, chat,
  toolkits, artifacts, admin, voice, support_assistant, smoke), `tests/api/`, `tests/unit/`
- `automation/pages/` — page objects (one class per page; `base_page.py` common nav)
- `automation/components/` — reusable UI component helpers
- `automation/fixtures/` + `conftest.py` — fixtures, `auth_state` (skips login on
  localhost via `VITE_DEV_TOKEN`), screenshots on failure
- `automation/api/` — API clients: generic `APIClient` uses Bearer token;
  entity clients (`ConversationAPI`, `AgentAPI`) use cookie auth from browser state
- `automation/utils/` — helpers grouped by topic
- **AFS files (analyst output):** `test-specs/<feature>/l<pri>_<slug>_<TMS-ID>.md`
  (per `test-case-analysis` spec-format; `lcovered_`/`lextend_` prefixes apply)

## Markers & selection

`pytest.ini`: `p0`–`p3` priority, `smoke`, `regression`, per-feature (`agents`,
`skills`, `pipelines`, `chat`, `toolkits`, `credentials`, `guardrails`, `voice`,
`support_assistant`, `admin`, `datasources`, `prompts`, `api`, `ui`, `slow`).
New tests carry: priority marker + feature marker + `regression` (and `smoke` only
for critical-path fast tests).

## Coverage tagging (TMS traceability)

The `automation_test_id` back-written to the TMS case is the **dotted pytest path**,
e.g. `tests.ui.agents.test_agent_management.TestAgentConfiguration.test_agent_toolkits_section_visible`.
One case ↔ one test id; extensions append to the covering test's docstring/markers.

## Locator strategy

- **Testid-only via `LocatorDescriptor`** (`automation/pages/locator_descriptor.py`):
  `LocatorDescriptor(testid="agent-form-save-button")`. The `fallback` parameter is
  **dead code** — `__get__` never calls it when testid is set. **Strictly never
  populate it** (note: `.claude/rules/page-objects.md` was corrected on 2026-07-10 —
  the old "testid + fallback" example is obsolete).
- **Locators live ONLY as page-object class fields** — `LocatorDescriptor` attributes
  declared at class level. Never construct a locator inside a method body
  (`page.locator(…)`, `get_by_*` calls in methods) and never in spec files.
- **Missing testid on the target?** Do NOT fall back to CSS/text. Add the testid to
  EliteaUI via the `add-data-testid` skill (edits `../EliteaUI/src`, commits to
  `automation/testids`, Vite HMR picks it up live). Naming `{section}-{element}-{type}`,
  e.g. `agent-form-save-button` vs `pipeline-form-save-button` — verify uniqueness
  before adding.
- **Stop+flag rule:** if a testid genuinely can't be placed (element outside
  `EliteaUI/src`, third-party widget), surface to the lead — don't ship brittle CSS.
- Authoritative rules: `.claude/rules/page-objects.md`, `.claude/rules/ui-tests.md`,
  `.claude/rules/mui-patterns.md` (auto-applied).

## Test data strategy

- Config/env via `automation/config.py` (pydantic-settings): `.env.test` file BEATS
  shell env vars. Add new keys to config.py + the master env file — grep for an
  existing key first.
- `test-data/` at repo root; toolkit factories in `automation/toolkit_factories.py`.
- Prefer read-only assertions on stable existing data; seed minimally + clean up
  loudly only when the observable requires fresh state (workflow skill Hard Rule 10).
- Data-dependent tests: serial mode (pytest-xdist is installed — shared state must
  not run parallel).

## Hooks & fixtures

- `conftest.py` wires auth (`auth_state` — Keycloak on deployed envs via
  `input[name="username"]`; skipped entirely on localhost), screenshot-on-failure,
  report paths (JUnit XML + HTML paths set there, not pytest.ini).
- AI responses arrive over WebSocket ~2s after send — use condition waits
  (`wait_for_response()` style), never sleeps.

## Step reporting — allure.step (mandatory)

Every test's steps must be wrapped in `with allure.step("Step N — <what>"):` blocks
so they surface in the Allure report. Pattern (from `test_artifacts_multi_file.py`):

```python
with allure.step("Step 1 — Attach the artifact toolkit to the agent via UI and save"):
    ...
with allure.step("Step 2 — Send the combined multi-file prompt via embedded chat"):
    ...
```

One `allure.step` per AFS step (assertions live inside their step's block). A test
without step wrapping is `CHANGES_REQUESTED` at review.

## Reporters & evidence

- **Local artifacts:** `automation/reports/allure-results/` (always — addopts),
  `automation/screenshots/` on failure. Optional HTML:
  `--html=reports/report.html --self-contained-html`.
- **No TMS/result reporter is wired into pytest** — keep it that way unless a task
  explicitly asks (then CI-gated + graceful per workflow skill § Phase 5).
- Flaky retries disabled by default; per-test `@pytest.mark.flaky(reruns=N)` allowed.

## CI integration

- `.github/workflows/`: `test-ui-dev.yml`, `test-ui-next.yml`, `test-ui-stage2.yml`,
  `test-ui-custom.yml`, `test-api.yml`, `docs-build.yml`, `delete-stale-branches.yml`.
- These target **deployed** envs and are run by humans / the batch process — the local
  pipeline never gates on them. `automation/base` has no CI by design.

## Known issues

- `pytest` won't start without the `reporting` extra installed (allure addopts).
- Model-selector button text changes with the selected model (chat tests).
- OneDrive slowness affects anything spawning many file ops.

## Unconfirmed

- Known-flaky test list — none documented yet; record here as they surface.
- API-test conventions are thinner than UI (`.claude/rules/api-tests.md` exists —
  follow it; flag gaps to the lead).
