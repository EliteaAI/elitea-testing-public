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
  green locally against `http://localhost:5173` before its PR — that is the
  *implementer's* gate. The *merge* gate is separate and stricter — see § Merge gate.

## Merge gate (the section the workflow skill defers to — N and semantics)

- **N = 3, and it means three SEPARATE consecutive pytest invocations of the SAME
  spec** — not one invocation in which 3 different tests pass (the 30e159d9
  anti-pattern). Three processes, same test node id(s), zero failures between them.
- **Run by the LEAD, independently, strictly BEFORE `gh pr merge`.** Reviewer
  `APPROVED` is necessary but not sufficient; the implementer's green run is not
  the gate; running the gate after the merge is a violation even if it passes
  (the baf8f3cf anti-pattern — self-caught, now codified).
- **Sanctioned-RED exception (isolated known defect):** a spec whose failure is
  (a) deterministic — identical failure 3/3, (b) single-cause, tied to an OPEN
  defect issue linked in the test (soft-assert or `# Known defect: #N` comment
  per the no-masking decision tree), may merge RED: 3/3 *identical* failures IS
  its deterministic gate, and staying red in CI is the correct signal until the
  product fix ships. Anything else red — flaky, multi-cause, no linked defect —
  blocks. Record the exception explicitly in the closure record.
  - **Closed-set variant (2026-07-18, ELITEA-1892/#615):** "single-cause" does
    not require literally one defect ID to fire every run. A gate run may
    legitimately show any subset of a **closed, enumerable set** of known
    defects touching the same flow — e.g. run A shows only `#611`, run B shows
    `#611`+`#614` — and still count as one sanctioned signature, PROVIDED
    every member of the set independently satisfies (a)+(b) on its own (open,
    filed, soft-asserted) AND every occurrence is verified against an
    independent ground truth (API response, not just a second DOM read)
    *before* being classified as the known defect rather than a raw failure —
    so a genuinely new/unknown cause can never silently fall into the
    "known" bucket. All terminal failures must route through the identical
    mechanism (one `soft_failures`/`pytest.fail()` aggregation, not separate
    ad-hoc catches). What still blocks: any failure that reaches the gate as
    a raw/uncaught exception, or that the API tie-breaker itself contradicts
    (real bug, not staleness), or a defect not in the enumerated, linked set.
    Record which set-members actually fired across the 3 gate runs in the
    closure record — don't just write "sanctioned RED".
- Gate runs use a clean process each time: `cd automation && HEADLESS=true
  ../.venv/bin/pytest <node-id> -v -p no:cacheprovider` (×3).

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

## Locator policy (AUTHORITATIVE — overrides any skill's example ladder)

_This section is the "locator strategy" the `test-automation-workflow` skill
defers to. **This project has no locator ladder — the ladder is one rung:
`data-testid`.** The skill's `getByRole → testid → …` sequence is a generic
example and does not apply here. See also `.agents/role-overrides.md`._

**Why (team goal):** the team wants `data-testid` on every element new tests
touch, and **measures UI-automation coverage via testid presence**. A
role/label/CSS handle isn't just brittle — it is invisible to the coverage
metric. Every raw handle silently shrinks measured coverage. (Ruled by the team
in PR #23, "Enforce testid-only locators"; confirmed by the operator 2026-07-14.)

**The inverse also holds — scope is load-bearing (team ruling 2026-07-14):**
testids go ONLY on elements tests actually touch. Blanket-adding to untested
elements is front-end noise and makes untested UI light up as "covered" in the
presence-based visualization — it corrupts the metric from the other side.
Coverage density (N testids / M components) is NOT a target; honest
presence ≈ tested is.

- **Testid-only via `LocatorDescriptor`** (`automation/pages/locator_descriptor.py`):
  `LocatorDescriptor(testid="agent-form-save-button")`. Never populate `fallback=`
  (dead code) or `locator=` (kept in the API for legacy only — forbidden in new
  code per `.claude/rules/page-objects.md`).
- **Locators live ONLY as page-object class fields** — `LocatorDescriptor` attributes
  declared at class level. Never construct a locator inside a method body
  (`page.locator(…)`, `get_by_*` calls in methods), never chain a raw selector off
  an existing field (`self.x.locator(".css")`), and never in spec files. Scoped
  sub-selectors: UPPER_CASE class constants containing `[data-testid="…"]` only.
- **Dynamic (runtime-parameterized) testids — the canonical pattern.** A testid whose
  value depends on data (`skill-tag-option-<name>`) cannot be a static field. The
  compliant shape is the SAME class-constant mechanism, templated:
  ```python
  # class level — the testid pattern is part of the locator inventory
  SKILL_TAG_OPTION = '[data-testid="skill-tag-option-{}"]'
  # call site — format with test-generated data only
  option = self.page.locator(self.SKILL_TAG_OPTION.format(tag_name))
  ```
  Inline `get_by_test_id(f"…{var}")` in a method body is NOT compliant — the pattern
  must live at class level so the testid inventory stays greppable (coverage
  tooling reads class-level `[data-testid=` strings). Dynamic testid naming:
  `{section}-{element}-{param}` with the parameter as the suffix.
  (Origin: #19 rework FAIL-1 — the canon was silent, the agent improvised; this
  section closes that gap.)
- **Testid = stable identity; state via `data-*` attributes (UI-team ruling,
  EliteaUI PR #581 review, 2026-07-16).** Never add a testid whose presence or VALUE
  changes with component state (`data-testid={!isExpanded ? id : undefined}` and
  state-switched ternaries are both outlawed). The element keeps ONE testid; state is
  a separate attribute (`data-expanded`, `data-state`). Automation asserts state by
  filtering on that attribute — a testid-keyed selector with a `data-*` state filter
  (`'[data-testid="x"][data-expanded="false"]'` as a class constant) IS compliant
  testid-only locating, and is the required replacement for "click until the testid
  disappears" loops. *Grandfathered:* the two-state import dialog
  (`agent-import-preview-dialog`/`agent-import-complete-dialog`) predates this ruling
  and stays until the UI team asks; do not add new testids in that shape.
- **Shared components never hardcode feature-scoped testids (same ruling).** A
  component under `src/components/` or `src/[fsd]/shared/` gets either a GENERIC
  testid (`search-send-button`) or a caller-supplied `testId` prop wired at the
  feature's call site. `{section}-{element}-{type}` naming refers to the CALL SITE's
  section, never the shared component's first consumer (the `agent-search-clear-button`
  -on-shared-SearchBar mistake — it leaked into skills and credentials pages).
- **Testid prop naming: `testId` / `<part>TestId`** (`closeButtonTestId`), never a
  `data` prefix (`dataTestId`, `closeButtonDataTestId`) — the prop always lands as
  `data-testid`, the prefix is noise.
- **Missing testid on the target? That is work to do, not a reason to rung down.**
  The escalation test is OR, not AND: missing testid *alone* ⇒ add it to EliteaUI
  via the `add-data-testid` skill (commit **and push `automation/testids`** — Vite HMR
  picks it up live; a human promotes to `main`, no agent PR). Naming `{section}-{element}-{type}`,
  e.g. `agent-form-save-button` vs `pipeline-form-save-button` — verify uniqueness
  before adding.
- **Stop+flag rule:** ONLY if a testid genuinely can't be placed (element outside
  `EliteaUI/src`, third-party widget like ReactFlow's `rf__wrapper`), surface to
  the lead — don't ship brittle CSS.
- **Existing raw handles in `automation/pages/` are tracked tech debt**
  (issues #25/#42, ~350 call sites), not precedent. Never cite neighbors to
  justify a new raw handle.
- Authoritative rules: `.claude/rules/page-objects.md`, `.claude/rules/ui-tests.md`,
  `.claude/rules/mui-patterns.md` (auto-applied; team-owned — where mui-patterns
  shows non-testid workarounds, prefer adding the testid; the workaround is only
  for elements that fail the stop+flag test).

## Test data strategy

- Config/env via `automation/config.py` (pydantic-settings): `.env.test` file BEATS
  shell env vars. Add new keys to config.py + the master env file — grep for an
  existing key first.
- `test-data/` at repo root; toolkit factories in `automation/toolkit_factories.py`.
- **Toolkit credentials are test data**: `GIT_HUB_TOKEN`, `JIRA_USERNAME`/`JIRA_API_KEY`
  in `.env.test` get typed into the Elitea UI to create toolkits (`toolkit_configs.py`);
  affected tests `pytest.skip` when unset. These are NOT tracker identities — see
  `profile.md` § Roles & sample users.
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
