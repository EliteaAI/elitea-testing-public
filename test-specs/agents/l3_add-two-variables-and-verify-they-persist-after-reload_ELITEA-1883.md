# Test Case: Add two variables and verify they persist after reload

## Metadata
- **TMS ID**: ELITEA-1883
- **Linked Story**: none
- **Priority**: low (per case frontmatter) — mapped to `p3`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch →
  DEV backend `https://dev.elitea.ai`), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live system, all 8
  steps verified, no product defect in the feature under test. One **test-infra** defect was found
  and filed separately (see below) — it does not block this case because a proven workaround
  already exists from prior cases.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing agent is available. **Do not use the shared `agent_id` pytest fixture** — it is
  currently broken (see Known Defects below); use `AgentAPI.create_agent_full()` with the
  established `reasoning_effort: "none"` / no-`temperature` workaround instead, exactly as
  `test_agent_remove_variable.py` (ELITEA-1884) does. Create a dedicated, uniquely-named agent per
  run with **no `{{variable}}` references** in its seed Instructions (so the Variables section
  starts absent, matching case step 1's implicit "before" state), and delete it at teardown via
  `delete_agent_via_menu()`.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Dedicated disposable agent name: `elitea-1883-av-{uuid4[:8]}` (mirrors the ELITEA-1884 pattern)

### Literal values (from the case)
| Field | Value |
|-------|-------|
| Instructions text | `{{MY_VAR}} and {{API_URL}}` |
| MY_VAR value | `hello_world` |
| API_URL value | `https://example.com` |

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner` (the `?viewMode=owner` query
   param is required — omitting it 404s, per prior-case precedent). Wait for the Instructions
   field to render.
   - **Verify — PASSES.** Agent detail page loads; Instructions field (`agent-instructions-input`)
     is empty (seed agent has no instructions); no Variables section rendered — confirmed absent
     from the DOM entirely (not just empty/collapsed), per the `ApplicationVariables.jsx` /
     `VariableList.jsx` shared-component behavior already documented in the ELITEA-1884 AFS.
2. Click into `agent-instructions-input` and type `{{MY_VAR}} and {{API_URL}}`.
   - **Verify — PASSES.** Instructions field shows the typed text exactly.
3. Verify the Variables section appears automatically, with a row for each of `MY_VAR` and
   `API_URL`.
   - **Verify — PASSES.** A "Variables" accordion (`agent-variables-section`) appears below
     Instructions with two rows. **Correction to a claim in the ELITEA-1884 AFS**: rows do
     **NOT** render in first-appearance order in the Instructions text. Live DOM order for
     `{{MY_VAR}} and {{API_URL}}` (MY_VAR appears first in the text) is
     `agent-variable-row-API_URL` then `agent-variable-row-MY_VAR` — i.e. **alphabetical by
     variable name**, not appearance order. (ELITEA-1884's `department`/`tone` pair happened to
     be alphabetically ordered too, which is why that AFS's claim went unchallenged — it was a
     coincidence, not a verified mechanism. See Concrete Handles below; the implementer should
     assert set-membership + per-row content, not textual appearance order, unless order itself
     is asserted as alphabetical.)
4. Enter `hello_world` into the `MY_VAR` value input.
   - **Verify — PASSES.** `agent-variable-input-MY_VAR`'s DOM `value` shows `hello_world`
     immediately. Confirmed both `.fill()` (direct DOM value set) and `press_sequentially()` work
     for this field — unlike the Instructions field (which the project's `mui-patterns.md`
     documents as requiring keyboard events for React `onChange`), this variable-value `Input`
     round-tripped correctly through Save with a plain `.fill()`-style set. Still, per the
     project's MUI convention, the implementer should default to `click()` +
     `press_sequentially()` for consistency with other form fields in this codebase, since that
     path is proven to work for both.
5. Enter `https://example.com` into the `API_URL` value input.
   - **Verify — PASSES.** `agent-variable-input-API_URL` shows the typed URL exactly (entered via
     `press_sequentially`).
6. Click `agent-save-button` (plain Save, not Save As Version — this case operates on the `base`
   version).
   - **Verify — PASSES.** `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}`
     returns `201 Created`. No console errors. Response body's `version_details.variables`
     contains both entries with correct values:
     `[{"name": "API_URL", "value": "https://example.com", "id": ...}, {"name": "MY_VAR", "value": "hello_world", "id": ...}]`
     (server-side order matches the DOM row order — alphabetical — confirming this isn't a
     client-rendering artifact).
7. Reload the page (full navigation, not SPA route change) to
   `${BASE_URL}/agents/all/{agent_id}?viewMode=owner`.
   - **Verify — PASSES.** Page reloads cleanly, no console errors.
8. Verify both `MY_VAR` and `API_URL` appear in the Variables section with their correct values
   after reload.
   - **Verify — PASSES.** Post-reload DOM read confirms: Instructions field still shows
     `{{MY_VAR}} and {{API_URL}}`; both `agent-variable-row-API_URL` and
     `agent-variable-row-MY_VAR` present; `agent-variable-input-MY_VAR` value = `hello_world`;
     `agent-variable-input-API_URL` value = `https://example.com`. Exact match to pre-reload
     state — no reverse-masking, the case's expected behavior matches the live product exactly.

## Expected Results
- Variables section appears automatically once `{{name}}` tokens exist in Instructions, with one
  row per distinct variable name (alphabetically ordered, not appearance order — see step 3).
- Entered values are reflected live in each variable's input.
- `PUT .../application/prompt_lib/{project_id}/{agent_id}` returns `201 Created` on Save, with
  both variables and their values present in the response body.
- No console errors at any step.
- After a full-navigation reload, both variables and their values persist exactly as saved.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (steps above) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, existing agent available | n/a (setup) | see § Preconditions | — | asserted *(via disposable-agent workaround — see Known Defects)* |
| Step 1: navigate to agent detail page | page loads | Step 1 | page load, `agent-instructions-input` empty | asserted |
| Step 2: type `{{MY_VAR}} and {{API_URL}}` into Instructions | text entered | Step 2 | `agent-instructions-input` value | asserted |
| Step 3: verify Variables section appears with MY_VAR and API_URL rows | section displayed, both names as rows | Step 3 | `agent-variables-section` visible, `agent-variable-row-MY_VAR` / `-API_URL` present | asserted |
| Step 4: enter `hello_world` for MY_VAR | field shows `hello_world` | Step 4 | `agent-variable-input-MY_VAR` value | asserted |
| Step 5: enter `https://example.com` for API_URL | field shows the URL | Step 5 | `agent-variable-input-API_URL` value | asserted |
| Step 6: click Save | Save completes | Step 6 | network PUT response `201`, response body variables array, no console errors | asserted |
| Step 7: reload the page | page reloads | Step 7 | full navigation, no console errors | asserted |
| Step 8: verify both variables + values persist after reload | both listed with correct values | Step 8 | post-reload DOM read on both row + input testids | asserted |

### Axis 2 — observables asserted beyond the case text

- Variables section is entirely absent from the DOM (not just empty) before any `{{name}}` token
  exists — *carried over from the ELITEA-1884 AFS's finding about the same shared component;
  re-verified live this run on a fresh agent.*
- Variable row DOM order is alphabetical by variable name, not first-appearance order in the
  Instructions text — *added: this run's two-variable case (`MY_VAR` before `API_URL` in text,
  but `API_URL` renders first) directly contradicts the order claim in the ELITEA-1884 AFS, which
  was based on an alphabetically-coincidental pair (`department`/`tone`). Corrected here and
  flagged in memory so the ELITEA-1884 AFS/implementation isn't propagated with a false
  assumption.*
- Server response body's `variables` array order matches DOM row order (both alphabetical) —
  *added: confirms the ordering is not a client-only rendering quirk, useful for the implementer
  choosing between DOM-read and API-read assertions.*
- No console errors after Save and after reload — *silent-error check per project convention.*
- Both `.fill()`-style and `press_sequentially()`-style entry succeed for the variable value
  inputs and both persist correctly through Save — *added: this is the first case to actually
  enter values into these inputs (ELITEA-1884 only ever left them at their empty default), so it's
  the first live confirmation of which interaction method the implementer can safely use.*

## Cleanup
1. Delete the dedicated disposable agent via `delete_agent_via_menu()` (or `agent_api.delete_agent()`
   as a fallback if the UI session was lost) — confirmed this run via `DELETE
   .../application/prompt_lib/399/{agent_id}` → `204 No Content`.

## Concrete Handles (discovered during exploration)

| Element | Handle | Status |
|---|---|---|
| Instructions field | `agent-instructions-input` | pre-existing |
| Save button | `agent-save-button` | pre-existing |
| Variables section heading (accordion summary) | `agent-variables-section` | pre-existing (added in ELITEA-1884) |
| Variable row (dynamic, one per variable name) | `agent-variable-row-{name}` (e.g. `agent-variable-row-MY_VAR`, `agent-variable-row-API_URL`) | pre-existing (added in ELITEA-1884) |
| Variable value input (dynamic) | `agent-variable-input-{name}` | pre-existing (added in ELITEA-1884) |
| Agent actions menu (three-dot) | `agent-actions-menu-button` → `agent-actions-menu` | pre-existing |
| Delete agent menuitem | `delete-agent-menuitem` | pre-existing |
| Delete-confirm name input | `delete-confirm-name-input` (contains a plain `#name` input) | pre-existing |

No new testids were needed — the ELITEA-1884 run already added everything this case's UI surface
requires. `automation/pages/agent_detail_page.py` already exposes `VARIABLE_ROW` /
`VARIABLE_INPUT` templates, `is_variable_row_visible()`, `get_variable_row_names()`, and
`is_variables_section_visible()`. **Gap**: there is no existing page-object method to read or set
a variable's *value* (only its row visibility/name) — the implementer will need to add e.g.
`fill_variable_value(name, value)` and `get_variable_value(name)` using the existing
`VARIABLE_INPUT` template, following the `click()` + `press_sequentially()` MUI convention.

## Network Behavior
- `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` — fires on Save;
  response body's `version_details.variables` is a list of `{name, value, id}` — assert on this
  directly for the strongest persistence signal (not just DOM state), same pattern as
  `test_agent_remove_variable.py`'s `_wait_for_resolved_save_count` + captured-request approach.

## Known Defects Found During Exploration

**None in the feature under test.** The case executed exactly as written; live behavior matches
expected behavior at every step (with one documentation correction — variable row order, see Axis
2 above, which is a correction to a prior AFS's claim, not a product defect).

**Test-infra defect found and filed** (not blocking this case, but affects any future case relying
on the shared `agent_id` fixture):

- **[MAJOR] `AgentAPI.create_agent()` hardcodes an invalid `temperature`+`reasoning_effort` combo,
  fails 400** — filed as
  [EliteaAI/elitea-testing-public#563](https://github.com/EliteaAI/elitea-testing-public/issues/563).
  This run was explicitly tasked with re-verifying, live, the orchestrator's claim that
  [#524](https://github.com/EliteaAI/elitea-testing-public/issues/524) ("Agent create fails 400:
  temperature+reasoning_effort conflict") was fixed on dev. Re-confirmed **two separate things**:
  1. The **product/UI fix is real and holds**: `/agents/create` with Name+Description only now
     sends `temperature: null` (not a non-null default) and gets `201 Created`.
  2. **But** the `agent_id` **pytest fixture** (`automation/fixtures/data_fixtures.py:77` →
     `AgentAPI.create_agent()`, `automation/api/client.py:366`) still 400s with the byte-identical
     validator message, because it independently hardcodes `"temperature": 0.6,
     "reasoning_effort": "medium"` — an invalid combination the backend correctly rejects. This
     was never actually the same bug as #524's root cause once traced fully; it's our own
     fixture's payload that's invalid, not a backend regression. Filed as a separate test-infra
     bug (`#563`) rather than reopening #524, and posted a clarifying comment on #524 itself.
  **Impact on this AFS**: none — the established `create_agent_full()` +
  `reasoning_effort: "none"` + no-`temperature` workaround (proven across ELITEA-1884/1888/1872)
  is used in this case's Preconditions/Test Data, same as those three prior cases.

## Blocked Steps
None — case completed end-to-end.

## Automation Hints
- Framework: pytest + Playwright, per `.agents/testing.md` (confirmed).
- Page object: extend `automation/pages/agent_detail_page.py` — do not duplicate the
  `VARIABLE_ROW`/`VARIABLE_INPUT` templates or the existing variable-row methods from ELITEA-1884.
- Follow `test_agent_remove_variable.py`'s structure closely (dedicated disposable agent via
  `create_agent_full()`, `capture_requests_matching` + `_wait_for_resolved_save_count` pattern for
  asserting the Save PUT, `delete_agent_via_menu()` teardown in a `finally` block). This case is
  effectively that test's sibling — "add + persist values" instead of "remove + persist absence".
- When asserting variable row order, assert **alphabetical by name** or (safer, order-independent)
  assert set membership + per-row value — do not assume first-appearance-in-text order.
