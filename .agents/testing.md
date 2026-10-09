# Testing

> Scout-generated 2026-07-10. Update when the framework, run commands, or
> conventions change. Analyst and implementer read this before touching tests.
>
> **2026-10 cut-over — one target, the DEV env.** Analysis, implementation and
> every gate run against **`https://dev.elitea.ai` as deployed**, with **ladder
> locators** (§ Locator policy). Where a dated entry below (merge-gate corollaries,
> § Unconfirmed ledger) describes a run against a local dev server or a
> testid-only rule, it is **history** — keep it for the mechanism it records, do
> not follow it as procedure.

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
- **Local verification gate:** there is no CI on `automation/factory`; a test must run
  green from this machine against the **DEV env** (`ELITEA_URL=https://dev.elitea.ai`,
  `APP_PREFIX=/app` in `automation/.env.test`) before its PR — that is the
  *implementer's* gate. The *merge* gate is separate and stricter — see § Merge gate.
  **DEV is the only target** — never point a run at a local dev server.
- **Browser exploration (Playwright MCP) on DEV:** the analyst/implementer MCP starts
  with `--isolated --storage-state .playwright-mcp/dev-storage-state.json`. Refresh
  that file at the start of every session, before the first browser call —
  `cd automation && ../.venv/bin/python scripts/dev_storage_state.py` (Keycloak
  sessions expire; the script prints only path/cookie-count/origin, never values).

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
  - **Analysis-time entry (2026-07-23, #557/ELITEA-1965):** the exception
    applies whether the defect is discovered during **automation** or during
    **analysis itself** — the (a)/(b)/(c) criteria above don't restrict *when*
    the defect surfaces. When the analyst finds a defect that independently
    satisfies deterministic + single-cause + linked-to-open-defect, they SHOULD
    classify the AFS `ready-for-automation` (not `defect-found`) with a
    Classification-note declared improvisation citing this bullet, and direct
    the implementer to write the affected assertion(s) as the *correct*
    expected behavior with `expect.soft()` + `# Known defect: #N`. This
    preserves coverage of the passing steps and flips green when the product
    fix ships. `defect-found` remains the correct status only when the defect
    **blocks further exploration** (prevents reaching later steps) — i.e. when
    pausing is genuinely necessary, not merely one isolable step at the tail.
    Note: `spec-format.md`'s `defect-found` definition ("automation paused
    until fix") lives in `.claude/skills/test-case-analysis/references/` and
    is the project-agnostic default; this bullet is the project-specific
    override per `role-overrides.md` § Declared-improvisation protocol.
- Gate runs use a clean process each time: `cd automation && HEADLESS=true
  ../.venv/bin/pytest <node-id> -v -p no:cacheprovider` (×3).

## Structure

- **Tests live in:** `automation/tests/ui/<feature>/` (agents, skills, pipelines, chat,
  toolkits, artifacts, admin, voice, support_assistant, smoke), `tests/api/`, `tests/unit/`
- `automation/pages/` — page objects (one class per page; `base_page.py` common nav)
- `automation/components/` — reusable UI component helpers
- `automation/fixtures/` + `conftest.py` — fixtures, `auth_state` (Keycloak API login
  on DEV), screenshots on failure
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

## TMS case id in the test (mandatory on case-derived tests)

**A test built from a TMS case declares that case id in its own source, so the
case id reaches the report** — the run shows which TMS case each result belongs
to without anyone cross-referencing a spreadsheet. The implementer writes it
while building the test; it is not a back-write.

On this project the declaration is `@pytest.mark.tms("ELITEA-2003")`. Forms,
multi-case and per-parameter usage, and what it renders:
`.claude/rules/ui-tests.md` / `.claude/rules/api-tests.md` § Markers; mechanism:
`automation/utils/tms_case_ids.py` (its module docstring).

A test with no TMS case behind it (framework unit tests, helper tests written
outside any case) names no case id — there is none to name. That is the only
exemption, not a loophole for a case-derived test.

Distinct from the `automation_test_id` back-write below: that one is written by
the orchestrator post-merge and is a machine correlation key. Both name the same
case; neither substitutes for the other.

## Coverage tagging (TMS traceability)

The `automation_test_id` back-written to the TMS case is the **CI correlation key**.
It must be the **dotted, `tests.`-rooted "Form C"**:
`tests.ui.agents.test_agent_management.TestAgentConfiguration.test_agent_toolkits_section_visible`
— no `automation.` prefix, no `.py`, no `::`. **Both** other forms fail correlation
**silently** (🟥 gap in `automation_coverage`, never an error).

**→ `.agents/test-automation.yaml` § `backwrite_on_done` is the single source** —
why Form C is the only shape that correlates, the mechanical derivation from a
node-id, the self-check one-liner against `reports/junit.xml`, the list-of-1..N
semantics, the non-pytest (Xray) exception, and the "rebuild `index.json`" caveat.
Canon set by ELITEA-1794 / issue #598, 2026-07-23. **Back-writing is the
orchestrator's job** — implementers and analysts never write this field.

## Locator policy (AUTHORITATIVE — overrides any skill's example ladder)

_This section is the "locator strategy" the `test-automation-workflow` skill
defers to. **Rewritten 2026-10 for the dev-targeted factory.** It supersedes the
2026-07 "testid-only, one rung" policy (PR #23) and every ruling, memory or AFS
that assumes the factory adds testids. Mechanics live in
`.claude/rules/page-objects.md` § Locator Strategy (auto-applied) — this section
states the policy and who owns what. See also `.agents/role-overrides.md`._

### One target, one locator source

**Everything in this project's test loop targets the DEV env as deployed**
(`https://dev.elitea.ai`, `APP_PREFIX=/app`). The DEV DOM is the only ground truth
for a locator: if DEV serves a `data-testid`, use it; otherwise take the next
ladder rung that is unique and record a `suggested_testid=` hint. One PR per case,
into `automation/factory`, in this repo.

A missing testid is **not** work — it is a hint on a lower rung. Nothing in the
loop waits on a frontend change, and no test ever depends on a testid DEV does not
already serve.

> Converting those hints into real testids is a separate, on-request process with
> its own session, its own agent and its own procedure
> (`.claude/skills/migrate-locators-to-testids`). It is out of scope here and
> needs no space in your context: it never runs as part of a case, and its rules
> load only in its own session.

### The ladder

First rung that **uniquely and stably** identifies the element **on DEV** wins:

1. `testid=` — the element already carries a `data-testid` on DEV (the UI team and
   past migrations keep adding them — always check first)
2. `role=` + `name=` — ARIA role + stable accessible name
3. `label=` — form control with `<label>` / `aria-label`
4. `css=` — stable `id` / attribute selector (`#id`, `[name="x"]`); third-party
   library public classes (CodeMirror `.cm-content`, ReactFlow `.react-flow__node`)
   count; MUI generated/structural classes (`css-*`, `Mui*-root`) do **not**
5. `xpath=` — **declared last resort**, `description=` says why rungs 1–4 failed

Hard constraints (import-time enforced by `pages/locator_descriptor.py`, so a
violation fails collection):
- every locator is a **class-level** `LocatorDescriptor` / `OptionalLocatorDescriptor`
  / `ScopedLocator` field, or an UPPER_CASE `[data-testid="…"]` constant — never
  built in a method body, never chained raw off a field, never in a spec;
- exactly one kind per declaration; **every non-testid declaration carries
  `suggested_testid=`** (kebab-case `{section}-{element}-{type}`, call-site section,
  dynamic ones end `-{}`);
- **no positional handles** — `:nth-child`, `[2]`, `last()`, `position()`,
  absolute `/html/…`, `.nth(i)` sibling picks; scope to a declared parent instead;
- `locator=` / `fallback=` are legacy-only — never in new or modified declarations.

Scoped and dynamic handles use `ScopedLocator(..., suggested_testid=...)` and
`.within(scope, *args)` (any rung) or a `[data-testid=…{}]` template constant
(testid rung). Inline `get_by_*(f"…")` in a method is non-compliant on every rung.

### The metric — locator debt

`cd automation && ../.venv/bin/python scripts/locator_inventory.py scan` →
**locator debt = non-testid declared locators / all declared locators**, plus
**unmanaged handles** (raw calls in methods — pre-ladder legacy, never added to).
This replaced an earlier "coverage = testid presence" metric, which made every case
wait on a frontend change. Baseline at cut-over (2026-10): 1838 declared, 21
non-testid (1.14%), 389 unmanaged handles.

Writing tests on the ladder **raises** debt by design; the separate migration
process burns it down. Report the delta on any PR that touches `automation/pages/`;
unmanaged handles must never increase.

### Third-party internals — a permanent `css=` rung

Some elements can never carry a testid because a third-party library renders them:
ReactFlow nodes, CodeMirror/Monaco line nodes, mermaid and react-markdown output.
These are a legitimate **terminal** `css=` rung — a scoped selector under a
testid-bearing parent, with no `suggested_testid=` hint, because no hint could ever
be honoured. Say so in the declaration's `description=` (the #579 exception).

### Legacy

Pre-ladder raw handles in `automation/pages/` (issues #25/#42) stay tracked debt
(the "unmanaged handles" count) — never precedent. When a case touches a method
that builds a locator inline, declare it at class level on the ladder as part of
the change.

- Authoritative mechanics: `.claude/rules/page-objects.md`, `.claude/rules/ui-tests.md`,
  `.claude/rules/mui-patterns.md` (auto-applied, team-owned).

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

- `conftest.py` wires auth (`auth_state` — Keycloak on DEV via
  `input[name="username"]`), screenshot-on-failure,
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
without step wrapping is `CHANGES_REQUESTED` at review — same severity as a
case-derived test missing its TMS case id (§ TMS case id in the test above).

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
  pipeline never gates on them. `automation/factory` has no CI by design.

## Known issues

- `pytest` won't start without the `reporting` extra installed (allure addopts).
- Model-selector button text changes with the selected model (chat tests).
- OneDrive slowness affects anything spawning many file ops.

## Unconfirmed

> Historical ledger. Entries dated before 2026-10 were observed under the earlier
> run setup; their mechanisms (networkidle vs socket polling, dev-build React
> warnings, auth-identity gaps) are still useful when diagnosing — the procedures
> they prescribe are superseded by § Run commands / § Locator policy.

- Known-flaky test list — first entry (2026-07-20, ELITEA-1835/#260 merge-gate run):
  `ArtifactsPage`'s shared `click_bucket_row` action (`@action("Navigate to bucket")`,
  `artifacts_page.py:457`) timed out once in 5 consecutive live-gate invocations of
  `test_upload_via_three_options_and_verify_selection` (a raw `Locator.wait_for`
  `TimeoutError`, allure status `broken`, not an assertion failure — that run also
  took ~87s vs a ~70s baseline, consistent with a transient dev-backend/listing lag
  rather than a code defect). Not reproduced in the other 4 runs (1 before, 3 after,
  all showing the deterministic sanctioned-RED `#649` signature instead). Not yet
  confirmed as a recurring pattern — record further occurrences here if it repeats;
  escalate to a fix-only implementer dispatch only once a pattern is established.
- API-test conventions are thinner than UI (`.claude/rules/api-tests.md` exists —
  follow it; flag gaps to the lead).
- **`networkidle` setup flake, mechanism named and tracked as #1847 (2026-08-27, ELITEA-1790/#1811)**:
  gate run 2 of 3 on the ELITEA-1790 repair burned both of pytest-rerunfailures' reruns on a raw
  uncaught `playwright._impl._errors.TimeoutError: Timeout 10000ms exceeded` at **Step 1**, inside
  `SkillsListPage.navigate_to_create()` → `BasePage.wait_for_network()` →
  `page.wait_for_load_state("networkidle", timeout=10000)`. Two consecutive failures, then a pass;
  a full re-gate immediately after was **3/3 clean with `reruns.json == {}` each**.
  **This is not a new noise flavor — it is the first one in this ledger with a named, structural
  mechanism.** `networkidle` resolves only after 500 ms of zero network connections, and this app
  holds a **persistent Socket.IO polling transport open on every page** (the same
  `/socket.io/?EIO=4&transport=polling` already captured in the console-500 entry above). A
  continuous poll and a "500 ms of silence" wait are in direct tension, so every one of the
  **143 `wait_for_network` call sites** in `automation/pages/` is a race that degrades exactly where
  it hurts most — a loaded CI box against a deployed env. Playwright's own docs mark `networkidle`
  DISCOURAGED for precisely this reason.
  **Matched control was run before assigning blame** (the #1082 discipline): the ELITEA-1790 diff
  touches exactly ONE file (the spec), so swapping that file to its `origin/main` version runs the
  pristine spec against byte-identical shared page objects. Control: **2/2 clean**. That is too few
  runs to exonerate a low-rate flake, and the honest reading is that the mechanism is **pre-existing
  and shared**, while the repair adds a 6th `navigate_to_create()` per run (6 skills created instead
  of 5) and therefore **+20% exposure** to it. Recorded rather than smoothed over.
  **Response when this fires: re-gate.** It is a raw uncaught error at a *precondition*, upstream of
  every assertion the spec makes, so it can never be a member of a sanctioned-RED set and 2-of-3 is
  never acceptable. The durable fix is #1847 (wait on the element the caller actually needs, not on
  network silence) — not a longer timeout, which only widens the window the race has to win in.
  ⚠️ **The reruns make junit record PASS**, so this class is invisible in the junit trail — evidence
  lives only in `reports/allure-results/*-result.json` (allure status `broken`). Grep by `fullName`.
