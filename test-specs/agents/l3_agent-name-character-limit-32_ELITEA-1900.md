# Test Case: Agent name character limit enforced at 32 characters

## Metadata
- **TMS ID**: ELITEA-1900
- **Source case**: `.agents/automation/agents-batch1-1277/cases/ELITEA-1900.md`
  (snapshot; TMS module `agents`)
- **Linked Story**: none
- **Priority**: l3 (low, per case frontmatter) — matches the l3(low)→p3
  mapping confirmed against the immediately-adjacent sibling case
  ELITEA-1899 (`test-specs/agents/l3_agent-icon-change-persists-on-list-card_ELITEA-1899.md`,
  same "low"→`l3` label, compiles to `@pytest.mark.p3` in
  `test_agent_icon_management.py`).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` / id `399`)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- The Create Agent page (`${BASE_URL}/agents/create`) is reachable directly
  by bare-path navigation — no dependency on any pre-existing agent/data.

## Test Data
### reuse-existing
None.

### generate-per-test
- An 80-character filler string (`"A" * 80`) typed into the Name field —
  never persisted (test never clicks Save), so nothing to clean up.
- A short filler description string typed into the Description field, used
  only to satisfy the Save-button's `required` condition for Step 5's
  assertion — also never persisted.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create` (bare path — matches the
   project's page-object navigation convention).
   - **Verify**: the Create Agent form is displayed — Name
     (`agent-name-input`) and Description (`agent-description-input`)
     fields are visible and empty; Save (`agent-save-button`) is
     **disabled** (control condition — proves Step 5's later "enabled" is a
     real state change, not an always-on button; same pattern as
     `test_agent_create_button_navigation.py`/ELITEA-1870, already merged).

2. Type an 80-character string (`"A" * 80`) into the Name field
   (`agent-name-input`) via real keystrokes (`press_sequentially` /
   Playwright `type`, not `fill()` — confirmed both paths produce the same
   result live, but keystroke-level typing is the closer analog to a real
   user and is what actually exercises the native `maxlength` HTML
   attribute end-to-end).
   - **Verify**: no assertion here — this step is the input action; the
     result is checked in Step 3.

3. Read the Name field's value.
   - **Verify** (confirmed live via `el.value` / `el.value.length` in
     browser context): the field contains **exactly 32 characters**
     (`"A" * 32`), never 80. Confirmed both via Playwright `fill()` (whole
     string in one call, truncated to 32 by the native `maxlength`
     attribute before it ever reaches React state) and via true
     keystroke-by-keystroke typing continued past the 32-char boundary
     (typed 32 filler chars, then attempted 5 more `"B"` keystrokes at the
     end of the field) — the extra keystrokes are silently rejected, value
     stays at exactly 32 chars, length never changes. This is the
     "no more can be entered" half of the case's Step 3.

4. With the Name field still at exactly 32 characters, check for an error
   state.
   - **Verify** (confirmed live): `agent-name-input`'s `aria-invalid`
     attribute is `"false"` (MUI TextField's error-state indicator); no
     error-styled helper text is rendered under the field. A "0 characters
     left" character counter appears (a normal, non-error UI affordance,
     not an error indicator) — this is expected UI feedback, not the case's
     "error state" concern.

5. Fill the Description field (`agent-description-input`) with a short
   non-empty string (Description is `required`, independently of the Name
   field's state).
   - **Verify** (confirmed live): Save (`agent-save-button`) becomes
     **enabled** once both Name (32 chars, at the limit) and Description
     are non-empty — matches the case's Step 5 and its "Expected Final
     State".

6. Side-channel check — no console errors across the whole flow (navigate →
   type 80 chars → verify truncation/no-error → fill description → verify
   Save enabled).
   - **Verify** (confirmed live): zero console errors.

## Expected Results
- Typing 80 characters into the Name field results in exactly 32 characters
  being accepted — both via a single `fill()` call and via continued
  keystroke-level typing past the boundary (extra input is silently
  rejected, not appended, no error thrown).
- No error state (`aria-invalid`, error-styled helper text) is shown when
  the Name field is exactly at the 32-character limit — a plain, non-error
  character counter ("0 characters left") is the only feedback shown.
- The Save button is enabled once Name (at the 32-char limit) and
  Description are both filled.
- No console errors at any step.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to the Create Agent page | The Create Agent form is displayed | AFS step 1 | `step 1`: Name/Description fields visible+empty, Save disabled | asserted |
| 2 Type 80 characters into the Name field | Input is entered in the Name field | AFS step 2 | `step 2`: keystroke-level typing action | asserted (action step, result checked in step 3) |
| 3 Verify the input is truncated to a maximum of 32 characters (no more can be entered) | The Name field contains exactly 32 characters; no additional input is accepted | AFS step 3 | `step 3`: `el.value.length == 32` after both `fill()` and continued keystrokes past the boundary | asserted |
| 4 Verify no error state is shown when the name is exactly at the 32-char limit | No error message or visual error state is displayed | AFS step 4 | `step 4`: `aria-invalid == "false"`, no error helper text | asserted |
| 5 Verify the Save button is enabled (Description also filled) | Save button is enabled when both Name (32 chars) and Description are filled | AFS step 5 | `step 5`: `is_save_enabled() == True` | asserted |
| Expected Final State: Name field contains exactly 32 chars, no error, Save enabled with Description filled | (restates steps 3-5) | AFS steps 3-5 | steps 3-5 | asserted *(no separate row needed)* |

## Axis 2 — Analyst additions
- `step 1` asserts Save starts **disabled** on the fresh form — *added: the
  control condition proving step 5's "enabled" is a real state change
  caused by filling both required fields, not an always-enabled button.
  Mirrors the already-merged ELITEA-1870 pattern
  (`test_agent_create_button_navigation.py`).*
- `step 3`'s continued-keystroke sub-check (typing 5 more `"B"` characters
  after reaching the 32-char boundary) — *added: the case's own Step 3 text
  says "no more can be entered", which a single `fill()` truncation alone
  doesn't fully prove (a `fill()` call bypasses the DOM's native input
  event pipeline in some edge cases). Continued real keystrokes confirm the
  native `maxlength="32"` HTML attribute (not just a post-hoc React
  truncation) is what enforces the limit — confirmed live, source-code
  cross-checked (see Automation Hints).*
- `step 6` (no console errors across the whole flow) — *added: a
  boundary-truncation feature is exactly the kind of interaction that can
  throw an uncaught exception in the input's event pipeline without
  visibly breaking the UI; confirmed live there is none on this build.*

## Cleanup
None. The test never clicks Save — no agent is created, nothing to delete.

## Concrete Handles (discovered during exploration)

All three handles below are **pre-existing** — confirmed present on both
`origin/main` and `origin/automation/testids` in `EliteaAI/EliteaUI`
(git-grep verified this run, 2026-08-07). **No new testid work needed for
this case.**

| Element | File | Testid | Provenance |
|---|---|---|---|
| Name input | `CreateAgentForm.jsx` (`src/[fsd]/features/agent/ui/agent-details/configurations/form/`) | `agent-name-input` | on-main ✓ / on-automation/testids ✓ |
| Description input | `CreateAgentForm.jsx` (same file) | `agent-description-input` | on-main ✓ / on-automation/testids ✓ |
| Save button | (agent form header, existing page object field) | `agent-save-button` | on-main ✓ / on-automation/testids ✓ |

Not touched by this case (no testid requested — scope discipline, `.agents/role-overrides.md`
"touches" = actually invoked on this test's executed path):
- The Name field's character counter (`Text.CharacterCounter` at
  `CreateAgentForm.jsx:139-146`) — renders "0 characters left" at the
  32-char boundary but has **no `data-testid` wired at this call site**
  (the shared `CharacterCounter.jsx` component DOES support a `dataTestId`
  prop, per `EliteaUI/src/[fsd]/shared/ui/text/CharacterCounter.jsx:12,20`
  — it's a threading gap, not a missing-capability gap). This case's own
  "no error state" assertion is satisfied via the Name input's own
  `aria-invalid` attribute instead (see step 4), so the counter is not on
  this test's executed path — do not add a testid for it here.
- Instructions field, Tags field, Welcome message, icon picker, Cancel
  button — none exercised by this case's steps.

## Network Behavior
- No network requests fire from typing into Name/Description or from the
  32-char truncation itself — confirmed live, purely client-side Formik/
  React state (`CreateAgentForm.jsx`'s local `name` state +
  `formik.handleChange`). The test never clicks Save, so no
  `POST .../applications/...` (agent-creation) call is expected or should
  be asserted.

## Known Defects Found During Exploration
None. The case passes exactly as authored on this build:
- `MAX_NAME_LENGTH = 32` (`EliteaUI/src/common/constants.js:66`), wired as
  the native `maxLength` HTML attribute on `agent-name-input`
  (`CreateAgentForm.jsx:135`) — this is a synchronous, client-side-only
  constraint; no server round-trip is involved in the truncation.
- No length-based validation error exists for Name at all (only the
  `required`-empty case sets `formik.errors.name`) — so "no error state at
  the limit" is not a near-miss of some length-validation rule, it's simply
  that no such rule exists; the 32-char ceiling is enforced purely by the
  input's `maxlength` attribute preventing the value from ever exceeding
  it.

Evidence:
`test-results/screenshots/ELITEA-1900-step-03-name-truncated-32-chars.png`
(Name field showing 32 `"A"` characters, "0 characters left" counter, no
error styling, Save still disabled pending Description) — captured via
Playwright MCP snapshot this run (`.playwright-mcp/create-agent-name-filled.yml`).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: `automation/pages/agent_form_page.py` already has everything
  this case needs — `name_input`, `description_input`, `save_button`
  (`LocatorDescriptor`s), plus `get_name()`, `is_save_enabled()`. No new
  page-object methods are strictly required; a small `fill_name()` /
  `fill_description()` convenience wrapper is optional (neither currently
  exists — call `.name_input.fill(...)`/`.press_sequentially(...)` and
  `.description_input.fill(...)` directly, or add thin wrappers if the
  implementer prefers matching other page objects' style).
- Navigation: `self.navigate("/agents/create")` (bare path via
  `BasePage.navigate()`, `automation/pages/base_page.py:97`) — matches the
  project's page-object navigation convention (`APP_PREFIX` injected
  automatically). Do **not** reuse `AgentsListPage.navigate_to_create()` /
  click-through unless deliberately also covering that path — this case
  only needs to reach the form, ELITEA-1870 already covers the click
  navigation itself.
- Truncation check, two complementary techniques (both belong in the same
  test, not either/or — see Axis 2 above):
  1. `page.get_by_test_id("agent-name-input").fill("A" * 80)` then read
     `.input_value()` — confirms the value never exceeds 32 chars via a
     single bulk fill.
  2. `page.get_by_test_id("agent-name-input").press_sequentially("A" * 32)`
     then `press_sequentially("BBBBB")` (5 more chars) — confirms the
     value is *still* exactly 32 chars after keystrokes attempted past the
     boundary. `press_sequentially` (not `type`, which is the sync-API
     legacy alias) is the current Playwright Python API name for
     char-by-char typing.
- Error-state check: read `aria-invalid` directly —
  `page.get_by_test_id("agent-name-input").get_attribute("aria-invalid")`
  should be `"false"` (or falsy) at the 32-char boundary. No new
  page-object method needed; a one-line inline check or a thin
  `has_name_error()` helper both work.
- No `page.wait_for_timeout` calls — per `.agents/conventions.md`; typing
  and reading `input_value()`/`get_attribute()` are synchronous enough not
  to need any wait beyond Playwright's built-in actionability checks.
- Console-error capture: mirror `test_agent_create_button_navigation.py`'s
  pattern — `page.on("console", ...)` collecting `msg.type == "error"`
  entries across the whole flow, asserted empty at the end.
