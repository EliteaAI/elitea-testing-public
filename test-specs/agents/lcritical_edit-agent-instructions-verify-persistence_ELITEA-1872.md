# Test Case: Edit agent instructions and verify persistence

## Metadata
- **TMS ID**: ELITEA-1872
- **Linked Story**: none
- **Priority**: critical (per case frontmatter; case body header says "high" —
  frontmatter is authoritative for TMS tag/status, noted here as a minor
  case-text inconsistency, not filed as a defect)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend `https://dev.elitea.ai`), project
  `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login
  via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the
  live system, all 5 steps verified, feature under test (Instructions field
  persistence) has **no defect**. All required testids already exist. One
  **pre-existing, already-open, unrelated** defect
  ([#524](https://github.com/EliteaAI/elitea-testing-public/issues/524))
  blocks the *test-data setup* step (creating a fresh agent) via the
  project's standard helpers — see Preconditions and Known Defects below —
  but does not affect the Instructions-field observable this case verifies.

## Preconditions

- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing agent is available in the current project.
- **Test-data setup gotcha (re-confirmed this run, broader than previously
  scoped) — do NOT use the plain `agent_id` fixture or
  `AgentAPI.create_agent()` as-is.** Both currently 400 against the DEV
  backend:
  ```json
  [{"type": "value_error", "loc": ["versions", 0, "llm_settings"],
    "msg": "Value error, temperature is not allowed together with a reasoning_effort (other than 'none') — reasoning models reject a custom temperature"}]
  ```
  This is the same root cause as open defect
  [#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
  ("Agent create fails 400: default LLM settings send temperature with
  reasoning_effort on a reasoning-capable model"), previously scoped to the
  UI's default `/agents/create` form. **This run re-confirmed it also hits
  `AgentAPI.create_agent()` directly** (`automation/api/client.py:366`, the
  same helper the shared `agent_id` fixture in
  `automation/fixtures/data_fixtures.py:76` calls) — i.e. the standard
  fixture most of `test_agent_management.py` depends on for a fresh agent is
  itself currently blocked against the DEV backend. Posted as an update on
  [#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
  (no new issue filed — same root cause/ticket).
  **Workaround used this run** (same one documented in
  `test-specs/agents/l3_remove-variable-verify-removal-persists_ELITEA-1884.md`):
  create the disposable agent via `AgentAPI.create_agent_full()` with a
  payload that sets `llm_settings.reasoning_effort: "none"` and **omits**
  `temperature` entirely:
  ```python
  payload = {
      "name": f"autotest_{request.node.name}"[:32],
      "description": f"Auto-created for test {request.node.name}",
      "type": "interface",
      "versions": [{
          "name": "base",
          "tags": [],
          "instructions": "You are a test agent.",
          "variables": [],
          "tools": [],
          "llm_settings": {
              "max_tokens": -1,
              "reasoning_effort": "none",
              "model_name": settings.default_model_name,
              "model_project_id": settings.default_model_project_id,
          },
          "conversation_starters": [],
          "agent_type": "openai",
          "welcome_message": "",
          "meta": {"step_limit": 25},
      }],
  }
  agent = agent_api.create_agent_full(payload)
  ```
  Confirmed live: this creates successfully (this run's agent id `4882`,
  deleted at teardown). **For the implementer:** either call
  `create_agent_full()` directly in this test (bypassing the broken
  convenience method, matching the ELITEA-1884 pattern), or — if triaged as
  higher-value — raise to the lead whether the shared `agent_id` fixture
  itself should be patched to use this payload shape, since it would unblock
  every other test currently relying on it against DEV. That fixture-level
  fix is out of scope for this single-case AFS; flagging it here so the
  implementer doesn't have to rediscover it.
- The 32-character API name limit applies (`autotest_{test_function_name}`
  can exceed it for long test names — truncate as the existing fixture
  already does).

## Test Data

### Literal values
| Field | Value |
|-------|-------|
| Initial instructions (seed) | `You are a test agent.` |
| New instructions (per case) | `You are an updated test assistant.` |

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner` (the
   `?viewMode=owner` query param is required — omitting it produces
   inconsistent tab context, matching prior AFS findings). Wait for the
   Instructions field to render.
   - **Verify — PASSES.** Agent detail page loads (`Page Title: Agent:
     <name> - <project>`); Instructions field (`agent-instructions-input`)
     shows the agent's current instructions (`You are a test agent.` for a
     freshly-seeded agent); Save/Discard buttons start `[disabled]`.
2. Click into `agent-instructions-input`, select-all (`ControlOrMeta+a`),
   then type (via `press_sequentially`, per the project's MUI
   React-onChange convention — `fill()` does NOT reliably trigger
   validation on this field) the new instructions: `You are an updated
   test assistant.`
   - **Verify — PASSES.** The field's value updates to the new text
     immediately; the Save and Discard buttons transition from
     `[disabled]` to enabled (`agent-save-button`, `agent-discard-button`
     — confirmed live via accessibility snapshot before/after).
3. Click `agent-save-button` (plain Save — this case operates on the
   `base` version, not Save As Version) and wait for network idle.
   - **Verify — PASSES.** `PUT
     /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}`
     returns **`201 Created`**. Zero console errors, zero console
     warnings (checked both `error` and `warning` levels). Save/Discard
     buttons return to `[disabled]` — matching the case's "confirmation is
     shown or save button returns to default state" acceptance criterion
     (this app's confirmation mechanism *is* the disabled-button
     transition; no separate toast was observed for this action).
4. Reload the page (full navigation via `page.goto` / browser reload —
   not an SPA route change) to
   `${BASE_URL}/agents/all/{agent_id}?viewMode=owner`.
   - **Verify — PASSES.** Full navigation completes; page re-renders with
     re-fetched agent data (`GET
     /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}`
     → `200 OK` observed in the network log).
5. Verify the Instructions field contains `You are an updated test
   assistant.`
   - **Verify — PASSES.** `agent-instructions-input.input_value() ==
     "You are an updated test assistant."` after reload. No
     reverse-masking: the live product behaves exactly as the case
     describes — this is a straightforward `ready-for-automation` case, not
     a clarification or defect.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (steps above) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | covered |
| Precondition: existing agent available | Agent detail page reachable | Test-data setup (see Preconditions workaround) | agent created via `create_agent_full()`, id returned | covered via workaround (see Known Defects) |
| Step 1: navigate to agent detail page | Page loads with current field values | Step 1 | page title, `agent-instructions-input` initial value | covered |
| Step 2: clear Instructions field, enter new text | Field displays new text | Step 2 | `agent-instructions-input` value post-type | covered |
| Step 3: click Save, wait for network idle | Save completes; confirmation/default-state shown | Step 3 | PUT response `201`, no console errors, Save/Discard `[disabled]` post-save | covered |
| Step 4: reload the page | Page reloads | Step 4 | full navigation (not SPA), GET re-fetch `200` | covered |
| Step 5: verify Instructions field shows new text | Field displays saved text post-reload | Step 5 | `agent-instructions-input.input_value()` post-reload | covered |
| Pass/Fail criteria: "all steps complete without errors" | No errors at any step | Steps 1–5 | console error/warning check at each step | covered |
| Pass/Fail criteria: "field reverts or shows different value = FAIL" | n/a (negative condition) | Step 5 | exact string equality assertion (not substring) | covered |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| Save/Discard button disabled-state transition (pre-save → enabled-after-edit → disabled-after-save) | The case's step 3 expected result ("confirmation is shown or save button returns to default state") is ambiguous about *which* signal to check; this app's actual mechanism is the disabled-state transition — confirmed live so the implementer doesn't guess at a toast/snackbar that doesn't exist for this action |
| Network-level PUT status code (`201`) and re-fetch GET status code (`200`) | Stronger signal than UI-only assertions; matches the project's existing pattern in `l3_remove-variable-verify-removal-persists_ELITEA-1884.md` for the same Save/reload flow |
| Zero console errors AND zero console warnings at both the initial edit+save and the post-reload check | Silent-error check per project convention (`test-case-analysis` § Anti-patterns); both checks clean this run |
| `press_sequentially` (not `fill()`) required to trigger the Save-button-enable state | Confirms the project's documented MUI React-onChange gotcha (`.claude/rules/mui-patterns.md`) applies to this exact field; the implementer should not attempt `fill()` and then wonder why Save stays disabled |
| Exact string equality (not substring) between the final field value and the case's literal expected text | The case's Pass criterion explicitly calls out "reverts... or shows a different value" as a FAIL condition — a substring check (as `test_agent_instructions_field` uses for its own, different assertion) would be too weak to catch a partial/garbled save |

## Stable handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| Instructions field | `agent-instructions-input` | pre-existing (`AgentFormPage.instructions_input`) |
| Save button | `agent-save-button` (via `AgentFormPage.click_save()` / `is_save_enabled()`) | pre-existing |
| Discard button | `agent-discard-button` (referenced by existing page object, not independently re-verified this run beyond enable/disable state) | pre-existing |

No new testids were needed — this case exercises only elements the suite
already touches and has testids for (`test_agent_instructions_field`,
`test_edit_agent_name`, `test_edit_agent_description` already cover
adjacent surfaces on this same page object).

## Implementation guidance for the implementer

This is **not** a Rule-6 dedup/extend case — `test_agent_instructions_field`
only asserts the Instructions field is visible and non-empty (no edit, no
save, no reload — see `automation/tests/ui/agents/test_agent_management.py`),
and `test_edit_agent_name` / `test_edit_agent_description` prove the
edit→save→reload→verify *pattern* but on different fields (name,
description). No existing spec asserts Instructions-field persistence
specifically, so this is genuinely new coverage — `ready-for-automation`,
not `extend-existing`.

That said, the **pattern to follow is a direct copy** of
`test_edit_agent_name` / `test_edit_agent_description` in
`TestAgentActions` (same file, same class,
`automation/tests/ui/agents/test_agent_management.py`), swapping in
`instructions_input` / `update_text_field("instructions", ...)` for
`name_input`/`update_name()`. Suggested test name:
`test_edit_agent_instructions`. The page object
(`AgentFormPage.update_text_field()`, `automation/pages/agent_form_page.py:419`)
already supports `"instructions"` as a `field_name` — no page-object changes
needed. Optionally add a thin `update_instructions()` wrapper mirroring
`update_name()`/`update_description()` (`agent_form_page.py:449-467`) for
call-site consistency, though it's not required (the generic
`update_text_field("instructions", ...)` call works as-is).

**Test-data setup**: do not use the `agent_id` fixture directly (see
Preconditions — currently broken against DEV by #524). Either fetch a fresh
agent via `AgentAPI.create_agent_full()` with the `reasoning_effort: "none"`
payload shown above (inline in the test, or as a small test-local fixture),
or coordinate with the lead about patching the shared fixture (out of scope
here).

## Known Defects Found

**None new.** The feature under test — Instructions field edit, save,
reload, persistence — behaves exactly as the case describes; no
reverse-masking, no defect. The only defect encountered was the
**already-open** [#524](https://github.com/EliteaAI/elitea-testing-public/issues/524),
which affects test-data setup (creating a fresh agent via the project's
default helpers), not the feature under test. This run **reconfirmed and
expanded the documented scope** of #524 (also hits `AgentAPI.create_agent()`
directly, not just the UI form) via a work-log comment on the existing
ticket — no new issue filed (dedup: same root cause).

## Cleanup steps

1. Created a disposable agent (`autotest_1872_instr`, id `4882`) via
   `AgentAPI.create_agent_full()` with the `reasoning_effort: "none"`
   workaround.
2. Executed all 5 case steps against it (see Test Steps above).
3. Deleted the agent via `AgentAPI.delete_agent(4882)` after verification —
   confirmed via script output (`deleted 4882`). No shared/fixture state was
   touched or left modified.

**For the implementer:** the automated test must follow the same
create-disposable-agent-then-delete-at-teardown pattern (via `pytest`
fixture teardown or `try/finally`), matching every other test in
`TestAgentActions`.
