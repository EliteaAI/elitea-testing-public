# Test Case: Remove a variable and verify removal persists

## Metadata
- **TMS ID**: ELITEA-1884
- **Linked Story**: none
- **Priority**: low (per case frontmatter) — mapped to `p3`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch →
  DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live system, all 6
  steps verified, no product defect. Three missing testids (`agent-variables-section`,
  `agent-variable-row-{name}`, `agent-variable-input-{name}`) were discovered absent live and
  added this run — see EliteaUI changes below.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- An agent with at least one saved variable exists — **do not create a fresh disposable agent
  via the default UI create flow**: that flow is currently blocked by an **open, unrelated**
  defect, [EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
  ("`temperature` is not allowed together with a `reasoning_effort`" 400 on the project's default
  reasoning-capable model), confirmed hit again in this run when attempting agent creation via
  `POST /api/v2/elitea_core/applications/prompt_lib/399` from the `/agents/create` form. This run
  worked around it by reusing the existing shared fixture agent **`Test Agent`** (agent id `3`,
  version id `3`, `base` version) instead — its Instructions field starts with no variables, so a
  variable can be added and removed without any pre-existing variable being lost. The
  implementer's automated test should follow the same pattern used in
  `test-specs/agents/lcritical_save-as-version-creates-named-version-visible-in-dropdown_ELITEA-1888.md`
  instead: **create a dedicated, uniquely-named agent per run via `AgentAPI.create_agent_full()`**
  with `llm_settings` setting `reasoning_effort: "none"` and omitting `temperature` (avoids
  #524), then delete it at teardown via `delete_agent_via_menu()`. **Do not reuse the shared
  `Test Agent` (id 3) as automated-test fixture data** — this analyst run reused and then
  restored it manually (see Cleanup below) only because analysis happens outside the automated
  suite; a real automated test must not depend on manually restoring shared state.

## Test Data

### Literal values
| Field | Value |
|-------|-------|
| Instructions (initial, two variables) | `This is a test agent for UI testing. Focus on {{department}} using a {{tone}} tone.` |
| Instructions (after removing one variable) | `This is a test agent for UI testing. Focus on using a {{tone}} tone.` |
| Variable removed | `department` |
| Variable that must persist | `tone` |

Two variables (not one) are used deliberately so the case's "remaining variables are intact"
requirement (step 6) has something concrete to assert on — a single-variable agent can't
distinguish "the removed variable is gone" from "the whole Variables section collapsed because
it's now empty."

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner` (the `?viewMode=owner` query
   param is required, per prior AFS findings — omitting it 404s). Wait for the Instructions
   accordion to render.
   - **Verify — PASSES.** Agent detail page loads; Instructions field (`agent-instructions-input`)
     shows the agent's current instructions; no Variables section rendered if instructions
     contain no `{{name}}` references (confirmed: the section is entirely absent from the DOM,
     not just empty/collapsed, when there are zero variables — `ApplicationVariables.jsx`
     returns `null` when `version_details.variables.length === 0`).
2. Click into `agent-instructions-input`, and type (via `fill`/`press_sequentially`) instructions
   containing two `{{variable}}` references: `{{department}}` and `{{tone}}`.
   - **Verify — PASSES.** A "Variables" accordion section appears below Instructions, with one
     row per distinct variable name, in the order they first appear in the instructions text.
     Each row shows the variable name as its label plus a value input (empty by default).
3. Click `agent-save-button` (plain Save, not Save As Version — this case operates on the `base`
   version).
   - **Verify — PASSES.** PUT `/api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}`
     returns `201 Created`. No console errors. Save/Discard buttons return to `[disabled]`.
4. Edit `agent-instructions-input` again, removing the `{{department}}` token from the text
   (keep `{{tone}}`).
   - **Verify — PASSES.** The `department` variable row (and its value input) disappears from
     the Variables section **immediately, client-side, no save needed** — the Variables list is
     derived live from the Instructions text via regex parsing, not from the last-saved state.
     The `tone` row remains untouched.
5. Click `agent-save-button` again.
   - **Verify — PASSES.** PUT returns `201 Created` again, no console errors.
6. Reload the page (full navigation, not SPA route change) to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner`.
   - **Verify — PASSES.** After the agent data re-fetches: Instructions field shows the
     post-removal text (`{{department}}` gone, `{{tone}}` retained). The Variables section shows
     **only** the `tone` row — `department`'s row is absent, matching the case's expected final
     state exactly. No reverse-masking: the live product behaves exactly as the case describes;
     this is a straightforward `ready-for-automation` case, not a clarification.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (steps above) | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: navigate to agent with saved variable(s) | Detail page loads, variable(s) visible | Step 1 | DOM presence of Variables accordion + row testids | covered |
| Step 2: remove `{{variable}}` from instructions | Reference removed from Instructions field | Step 4 | `agent-instructions-input` value | covered |
| Step 3: verify variable row disappears | Row no longer shown | Step 4 | absence of `agent-variable-row-department` (and presence of `agent-variable-row-tone`) | covered |
| Step 4: click Save | Save completes | Steps 3 & 5 (two saves: seed + removal) | network PUT response `201`, no console errors | covered |
| Step 5: reload the page | Page reloads | Step 6 | full navigation (not SPA) | covered |
| Step 6: verify removed variable gone, others intact | Removed variable absent, remaining variables present | Step 6 | `agent-variable-row-department` absent, `agent-variable-row-tone` present, post-reload | covered |
| Preconditions: "agent with at least one saved variable exists" | n/a (setup) | see § Preconditions | — | covered via workaround (existing agent, see note on #524) |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| Variables section is entirely absent from the DOM (not just empty) when there are zero variables | `ApplicationVariables.jsx` returns `null` in that state — worth confirming so the implementer doesn't write a "section visible but empty" assertion that can never pass |
| Variable row disappearance is instant/client-side on text edit, before Save | The case's step 3 wording ("remove ... verify the variable row disappears") could be misread as requiring a save first; confirmed live it's a pure derived-state re-render off the Instructions textarea, no round-trip |
| No console errors on either Save | Silent-error check per project convention; both saves clean |
| Order of variable rows matches first-appearance order in the instructions text | Relevant for the implementer's `tone` vs `department` row assertions — not explicit in the case, but needed to write a stable name-anchored assertion |

## Stable handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| Instructions field | `agent-instructions-input` | pre-existing |
| Save button | `agent-save-button` | pre-existing |
| Variables section heading (accordion summary) | `agent-variables-section` | **added this run** |
| Variable row (dynamic, one per variable name) | `agent-variable-row-{name}` (e.g. `agent-variable-row-tone`, `agent-variable-row-department`) | **added this run** |
| Variable value input (dynamic) | `agent-variable-input-{name}` | **added this run** |

Dynamic testid naming follows the project's canonical class-constant + `.format()` pattern
(`.agents/testing.md`):
```python
VARIABLE_ROW = '[data-testid="agent-variable-row-{}"]'
VARIABLE_INPUT = '[data-testid="agent-variable-input-{}"]'
```

## EliteaUI changes made this run (testid gaps closed)

All three were confirmed absent live (`document.querySelectorAll('[data-testid*="variable"]')`
returned `[]` before the change) and added via the `add-data-testid` skill, dual-target flow:
commit `50594fa` on `automation/testids`, cherry-picked cleanly (no conflicts) onto
`testids/ELITEA-1884-variables-removal` cut from fresh `origin/main`, draft PR
[EliteaAI/EliteaUI#568](https://github.com/EliteaAI/EliteaUI/pull/568).

| testid | Element | File |
|---|---|---|
| `agent-variables-section` (static) | "Variables" accordion header | `src/components/ApplicationVariables.jsx` (new optional `sectionTestId` prop → `BasicAccordion`'s existing per-item `testId` field) |
| `agent-variable-row-{name}` (dynamic) | Wrapper `Box` around each variable's row | `src/components/VariableList.jsx` (new optional `rowTestId` template prop, `{}`-substituted per variable label) |
| `agent-variable-input-{name}` (dynamic) | Variable value input | `src/components/VariableList.jsx` (new optional `inputTestId` template prop, wired via `inputProps={{ 'data-testid': ... }}`) |

**Scope note for the reviewer:** `ApplicationVariables` / `VariableList` are shared components
also used elsewhere (e.g. the agent-create flow's `CreateAgentForm.jsx`, FSD). Per the project's
testid-scope rule (`.agents/testing.md`: "testids go ONLY on elements tests actually touch"),
the new props were wired **only** at `ApplicationConfigurationForm.jsx` — the actual call site
exercised live in this run (agent edit route, `/agents/all/:id`). The agent-create call site was
**not** wired, because agent creation via the default UI flow is currently blocked by open defect
#524 and was not exercised here. If a future case automates the create-flow's Variables section,
wire `sectionTestId`/`rowTestId`/`inputTestId` at `CreateAgentForm.jsx`'s existing
`<ApplicationVariables ... />` call the same way — the shared components already support it.

## Known Defects Found

None. The case executed exactly as written; live behavior matches expected behavior at every
step. The only defect encountered was the **already-open, unrelated** agent-creation defect
[#524](https://github.com/EliteaAI/elitea-testing-public/issues/524), which affects test-data
setup (see Preconditions) but is not a defect in the feature under test (variable
removal/persistence) and was not re-filed.

## Cleanup steps

This analyst run reused the shared fixture agent **`Test Agent`** (id `3`) rather than a
disposable one (blocked by #524 — see Preconditions). After verifying all 6 steps:
1. Edited `agent-instructions-input` back to the agent's original text:
   `This is a test agent for UI testing.` (no variable references).
2. Clicked `agent-save-button`; confirmed `201 Created`, no console errors.
3. Reloaded and confirmed the Variables section is fully absent again (matching the agent's
   pre-run state) — `Test Agent` is left exactly as other tests in the suite expect it.

**For the implementer:** this manual restore is not a substitute for proper test isolation. The
automated test must create its own disposable agent (`AgentAPI.create_agent_full()`, per the
ELITEA-1888 pattern) and delete it at teardown (`delete_agent_via_menu()`) — never touch the
shared `Test Agent` (id 3) fixture.
