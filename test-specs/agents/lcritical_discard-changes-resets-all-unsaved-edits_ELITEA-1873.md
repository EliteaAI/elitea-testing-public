# Test Case: Discard changes resets all unsaved edits

## Metadata
- **TMS ID**: ELITEA-1873
- **Linked Story**: none
- **Priority**: critical
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}`
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst / Implementer**: test-automation-engineer (Axel), combined
  analyst+implementer slot (batch `agents-batch1-1277`, surface already
  mapped — `test-specs/agents/_surface.md`)
- **Status**: `ready-for-automation` — case executed end-to-end live against
  `http://localhost:5173` (agent id `3`, "Test Agent" — edits made and
  discarded, never saved, so no shared data was mutated), all 4 steps
  verified, feature under test (Discard reverting Name/Description/
  Instructions) has **no functional defect**. One **testid gap** existed on
  the Discard confirmation modal/button (see Concrete Handles) and was
  closed via `add-data-testid` before implementation — see Amendment below.

## Preconditions

- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing agent with saved Name, Description, and Instructions is
  available. Implemented via a **dedicated, disposable agent** created
  through `AgentAPI.create_agent_full()` (not the shared `agent_id` fixture)
  — the fixture's plain `create_agent()` call currently 400s against the DEV
  backend ([#524](https://github.com/EliteaAI/elitea-testing-public/issues/524),
  `temperature` + a non-`"none"` `reasoning_effort` on the project's
  default reasoning-capable model). Workaround (same as ELITEA-1872/1884):
  `reasoning_effort: "none"`, omit `temperature`.

## Test Data

### Literal values
| Field | Saved (seed) value | Unsaved-edit value |
|-------|---------------------|---------------------|
| Name | `elitea-1873-discard-<hex8>` (created agent's name) | `<name>-EDITED` |
| Description | `Auto-created for ELITEA-1873 discard-changes test` | `Edited description before discard` |
| Instructions | `You are a test agent.` (module `SEED_INSTRUCTIONS`) | `You are an updated test assistant.` (module `NEW_INSTRUCTIONS`) |

## Test Steps

1. Open an existing agent's detail page and note current Name, Description,
   Instructions.
   - **Verify — PASSES.** Agent detail page loads with the seeded values in
     `agent-name-input` / `agent-description-input` /
     `agent-instructions-input`; Discard (`discard-button`) starts
     `[disabled]`.
2. Modify all three fields to different values without saving
   (`AgentFormPage.update_text_field()` — click + select-all + type, the
   project's established MUI React-onChange pattern; `fill()` does not
   reliably trigger validation).
   - **Verify — PASSES.** All three fields display the new unsaved values;
     Discard AND Save both transition to enabled once the form is dirty
     (confirmed live via DOM state before/after).
3. Click the Discard button and accept the confirmation dialog.
   - **Verify — PASSES.** Clicking `discard-button` opens a MUI "Warning"
     modal ("Are you sure you want to discard changes?", Cancel/Discard
     buttons). Confirmed live this modal and its confirm button carried
     **no testid at all** prior to this case (see Concrete Handles/
     Amendment) — closed before writing the test. `discardApplicationChanges`
     (`useDiscardApplicationChanges.js`) is a **pure client-side Formik
     `resetForm()`** — confirmed via source read, no network request fires
     on discard.
4. Verify all three fields have reverted to their previously saved values.
   - **Verify — PASSES.** `agent-name-input` / `agent-description-input` /
     `agent-instructions-input` all read back their originally-noted saved
     values (exact string equality) after the confirm click; Discard AND
     Save both return to `[disabled]` — confirmed live for a single-field
     edit (Name only) and again for all three fields edited simultaneously
     (`document.querySelector` DOM probes via Playwright MCP,
     2026-08-06).

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (steps above) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | covered |
| Precondition: existing agent with saved Name/Description/Instructions | Agent detail page reachable with known values | Test-data setup (`create_agent_full()` workaround) | agent created, id/name/description/instructions captured | covered |
| Step 1: open agent detail page, note current values | Current saved values noted | Step 1 | `get_name()`/`get_description()`/`get_instructions()` equal the seeded values | covered |
| Step 2: modify all three fields without saving | All three fields display new unsaved values | Step 2 | `get_name()`/`get_description()`/`get_instructions()` equal the edited values | covered |
| Step 3: click Discard (or navigate-away + confirm) | Discard action triggered; confirmation dialog accepted | Step 3 | `discard-confirm-modal` visible after click; `confirm_discard()` clicks `discard-confirm-button` and waits for the modal to detach | covered (Discard-button path only — see Axis 2 note on the navigate-away variant) |
| Step 4: verify all three fields reverted | Name/Description/Instructions all match originally noted saved values | Step 4 | `expect(...).to_have_value(original_*)` on all three fields, exact string equality | covered |
| Expected Final State: "No unsaved modifications remain" | — | Step 4 | `is_discard_enabled()` / `is_save_enabled()` both False post-discard | covered |
| Pass criterion: "all three fields revert... after discard" | — | Step 4 | see above | covered |
| Fail criterion: "one or more fields retain the unsaved modified values" | n/a (negative condition) | Step 4 | exact string equality (not substring) against the ORIGINAL values, not the edited ones | covered |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| Save AND Discard button enabled/disabled transitions (disabled → enabled-when-dirty → disabled-after-discard) | The case's Expected Final State ("No unsaved modifications remain") is a UI-state claim beyond just field values; the disabled-button transition is this app's actual signal for "no pending edit," matching the project's existing pattern for Save (`test_edit_agent_instructions`, ELITEA-1872) |
| `discardApplicationChanges` fires no network request (source-confirmed: pure Formik `resetForm()`) | Documents WHY no network-level assertion is made for the discard action itself (unlike Save, which the project asserts via PUT status) — so the implementer/reviewer don't go looking for one |
| Exact string equality (not substring) between post-discard field values and the originally-noted saved values | The case's Fail criterion explicitly calls out "one or more fields retain the unsaved modified values" as a FAIL — a substring check would be too weak to catch a partial revert |

**Case text note (not a defect, not filed):** the case's Step 3 offers two
alternative triggers — "Click the Discard button (or navigate away and
confirm discard in any dialog)". This AFS/implementation covers the
Discard-button path only, which is the deterministic, directly-testable
mechanism and matches the case's own primary phrasing ("clicking the
Discard button" in the Objective). The navigate-away variant is a distinct
trigger (route-guard interception) not covered here — flagging as a
narrower scope than the case's parenthetical alternative allows, not a
gap against the case's stated Objective.

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| Name field | `agent-name-input` | pre-existing (`AgentFormPage.name_input`) |
| Description field | `agent-description-input` | pre-existing (`AgentFormPage.description_input`) |
| Instructions field | `agent-instructions-input` | pre-existing (`AgentFormPage.instructions_input`) |
| Save button | `agent-save-button` | pre-existing |
| Discard button (tab-bar) | `discard-button` | pre-existing — **confirmed LIVE this run** (a prior implementer note on `test_agent_save_as_version.py` claimed this testid was "not actually wired up... confirmed absent" during ELITEA-1888; re-verified via DOM probe this run and it is present and correctly wired — that note is now stale, left in place as-is per the additive-only rule, not this case's file to touch) |
| Discard confirmation modal | `discard-confirm-modal` | **NEW — added this run.** `ApplicationTabBar.jsx`'s `<Button.DiscardButton>` call site never threaded `modalDataTestId`/`confirmButtonDataTestId`, even though `DiscardButton.jsx` → `Modal.BaseModal` already supported both props (same threading-gap shape ELITEA-1971 fixed for `CredentialsTabBar.jsx`). Generic name (not `agent-discard-confirm-modal`) because `ApplicationTabBar` is a SHARED component — confirmed via `git grep` that it's also used by `EditPipeline.jsx`, matching the pre-existing generic `discard-button`'s own naming (role-overrides § shared components never hardcode feature-scoped testids). EliteaUI commit: `EliteaAI/EliteaUI@cc327ec9` on `automation/testids` (pushed; human cherry-picks to `main`). |
| Discard confirm button (inside modal) | `discard-confirm-button` | **NEW — added this run**, same commit as above. |

## Implementation guidance for the implementer

Not a Rule-6 dedup/extend case — no existing spec in `test-specs/agents/`
covers Discard for the Agent detail page (`test_agent_save_as_version.py`
explicitly notes the gap was out of its scope). `ready-for-automation`, new
coverage.

Pattern to follow: a direct sibling of `test_edit_agent_instructions`
(ELITEA-1872) in the same file/class
(`automation/tests/ui/agents/test_agent_management.py::TestAgentActions`) —
same dedicated-disposable-agent-via-`create_agent_full()` setup, same
try/finally teardown via `agent_api.delete_agent()`. Suggested test name:
`test_discard_changes_reverts_all_unsaved_edits`.

Page-object additions needed on `AgentFormPage` (inherited by
`AgentDetailPage`):
- `discard_confirm_modal` / `discard_confirm_button` `LocatorDescriptor`
  fields (testid-only, per the new handles above).
- `is_discard_enabled()`, `click_discard()`, `confirm_discard()` methods —
  same shape as `CredentialDetailPage`'s existing Discard trio
  (`automation/pages/credential_detail_page.py`).
- Cosmetic cleanup while touching `discard_button`: its pre-existing
  `fallback=` param is dead code (LocatorDescriptor never invokes a
  fallback when a testid is set) — same cleanup `PipelineFormPage.discard_button`
  already received; safe to drop, not a behavior change.

## Known Defects Found

None. The Discard-reverts-all-fields behavior itself has no functional
defect — confirmed live for both a single-field edit and a
simultaneous three-field edit. The only gap found (missing testid on the
confirmation modal/its confirm button) was closed via `add-data-testid`
before implementation, per this project's "missing testid alone ⇒ add it,
don't rung down" policy — not filed as a defect (testid gaps are
implementer work, not product bugs).

## Cleanup steps

1. Created a disposable agent (`elitea-1873-discard-<hex8>`) via
   `AgentAPI.create_agent_full()` with the `reasoning_effort: "none"`
   workaround.
2. Executed Steps 1-4 against it in the implemented test.
3. Deleted the agent via `agent_api.delete_agent()` in a `finally` block —
   matching every other test in `TestAgentActions`.

**Live exploration note (analyst+implementer combined pass):** manual
DOM-probe exploration (Playwright MCP) was performed against agent id `3`
("Test Agent", a pre-existing shared-suite agent) to confirm the
Discard/testid behavior BEFORE writing the automated test — only local
(unsaved) field edits were made and then discarded; **Save was never
clicked**, so no shared/fixture data was mutated. The automated test itself
uses its own dedicated, disposable agent (see Test Data / Cleanup above).
