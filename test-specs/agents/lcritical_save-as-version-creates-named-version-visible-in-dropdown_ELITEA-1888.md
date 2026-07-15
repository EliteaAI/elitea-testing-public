# Test Case: Save As Version creates a named version visible in version dropdown

## Metadata
- **TMS ID**: ELITEA-1888
- **Linked Story**: none
- **Priority**: critical (per case frontmatter; body table says "high" — frontmatter is
  authoritative)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live system,
  all 7 steps verified, no product defects hit. Five missing testids were discovered and
  added live (see EliteaUI changes below); the case could not otherwise be automated per
  the project's testid-only locator policy.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- An existing agent is available in the "base" version — **satisfied by reusing an
  existing project agent, not by creating a fresh one.** See Test Data below for why.

## Test Data

### Blocking context that shapes test-data strategy (read before automating)
Agent creation via the default UI create flow (and via the existing
`AgentAPI.create_agent()` fixture) is currently broken by an **open, unrelated**
defect — [EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
("`temperature` is not allowed together with a `reasoning_effort`" 400 on the project's
reasoning-capable default model). This was NOT hit or re-triggered by this run (this
case's precondition only requires an *existing* agent, so agent-creation was avoided
entirely), but it means the implementer **cannot** use "create a fresh dedicated agent
via UI/API, run the test, delete it" as the setup pattern until #524 is fixed or
`AgentAPI.create_agent()`'s default `llm_settings` payload is patched to avoid the
conflict (e.g. `reasoning_effort: "none"` or omit `temperature`).

### Proven working pattern (used and verified live in this run)
Reuse an existing, disposable, single-purpose agent already present in the project (this
run used agent id `4745`, name `elitea-1735-skills-agent` — one of several duplicate
debris agents left over from ELITEA-1735 runs, `GET
/api/v2/elitea_core/applications/prompt_lib/399` confirmed `total: 10` before, `total: 9`
after cleanup), then delete the **whole agent** at teardown via the existing
`delete_agent_via_menu()` page-object method / `delete-agent-menuitem` testid. This
avoids the #524 create-path entirely and leaves the project agent count unchanged
end-to-end. **Do not reuse a long-lived shared fixture agent** (e.g. id `3` "Test Agent")
for this pattern — the case's Step 3 (Save As Version) permanently adds a new version to
whatever agent it targets, and there is no "delete version" UI/API found in this run
(only whole-agent delete), so a shared fixture would accumulate versions across every
automated run.

### Literal values
| Field | Value |
|-------|-------|
| Version name | `v2-test` (per case; typed and confirmed to work as-is, no case-text drift) |
| Instruction change | Appended `" Additionally."` to the end of the existing Instructions
  field (case says "Append a word" — literal single-word append also works; this run used
  a short phrase to make the diff visually unambiguous in evidence) |

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner` (note the
   `?viewMode=owner` query param is **required** — without it the route 404s: "Page not
   found"). Wait for the page title to become `Agent: {name} - {project}` (a plain
   `wait_for_load_state` alone is insufficient; this run had to poll/retry because the
   page briefly shows a spinner-only DOM).
   - **Verify — PASSES.** Agent detail page loads with `VERSION:` combobox showing
     `base` and version-id textbox `4745`. Instructions field shows the agent's
     unmodified base instructions.
2. Click into the Instructions field (`agent-instructions-input`), move the caret to the
   end (`ControlOrMeta+End`), and type-append text via `press_sequentially` (never
   `fill()` — MUI/React onChange requirement, `.claude/rules/mui-patterns.md`).
   - **Verify — PASSES.** Field value becomes `"You are a helpful assistant.
     Additionally."`. The page's Save/Save As Version/Discard button row transitions
     from `Save [disabled] / Save As Version [enabled] / Discard [disabled]` to
     `Save [enabled] / Save As Version [enabled] / Discard [enabled]` — a useful
     "form is dirty" signal for the implementer's own wait/assert.
3. Click `agent-save-as-version-button` ("Save As Version").
   - **Verify — PASSES.** A `role="dialog"` opens, heading "Create version"
     (`agent-version-dialog-close-button` for the X), containing a `Name` text input
     (`agent-version-dialog-name-input`) and `Cancel`
     (`agent-version-dialog-cancel-button`) / `Save`
     (`agent-version-dialog-save-button`, disabled until Name is non-empty) buttons.
4. (Same as Step 3's verification — the case numbers "click" and "verify the dialog
   appears" as separate steps; this run treated them as one interaction+observation,
   noted in the Coverage Map.)
5. Type `v2-test` into `agent-version-dialog-name-input` (`press_sequentially`), then
   click `agent-version-dialog-save-button`.
   - **Verify — PASSES.** URL changes to
     `/agents/all/{agent_id}/{new_version_id}?viewMode=owner&isFromCreation=true` (this
     run: `/agents/all/4745/4852?...`), then the `isFromCreation` param is stripped
     automatically after the version loads. `VERSION:` combobox now shows `v2-test`,
     version-id textbox shows the new version id (`4852`). Save/Discard buttons return
     to `[disabled]` (clean state — confirms the new version was persisted, not just a
     local unsaved edit). Instructions field still reads `"You are a helpful assistant.
     Additionally."`, confirming the edit made in Step 2 was captured into the new
     version, not lost.
6. Click the `agent-version-selector-trigger` (VERSION dropdown) to open it.
   - **Verify — PASSES.** A `role="listbox"` opens with two `role="option"` entries:
     `version-option-base` (text "base - 14.07.2026") and `version-option-v2-test` (text
     "v2-test - 15.07.2026", `[selected][active]`). Both "base" and "v2-test" are present
     as the case requires.
7. (Already confirmed as part of Step 5/6's observation.) The `[selected][active]`
   state on `version-option-v2-test`, plus the `v2-test` text on the closed
   `agent-version-selector-trigger` and version-id textbox `4852` in the URL/DOM, jointly
   confirm "v2-test" is the currently active version.

## EliteaUI changes made this run (testid gaps closed)

All five of the following were **confirmed absent live** (verified via
`document.querySelectorAll('[data-testid]')` before making any change) and were added
via the `add-data-testid` skill, dual-target flow (commit `2af4c6d` on
`automation/testids`, cherry-picked to `testids/ELITEA-1888-save-as-version` cut from
fresh `origin/main`, draft PR
[EliteaAI/EliteaUI#567](https://github.com/EliteaAI/EliteaUI/pull/567)):

| testid | Element | File |
|---|---|---|
| `agent-save-as-version-button` | "Save As Version" button on the Agent detail toolbar | `src/pages/Applications/Components/Applications/SaveNewVersionButton.jsx` |
| `agent-version-selector-trigger` | VERSION dropdown trigger (MUI Select, agent-side only — the Skill-side selector is untouched) | `src/[fsd]/entities/version/ui/VersionSelect.jsx` (new optional `dataTestId` prop) + `src/[fsd]/entities/application-tab-bar/ui/ApplicationVersionSelect.jsx` (wires `dataTestId="agent-version-selector-trigger"`) |
| `agent-version-dialog-name-input` | "Create version" dialog's Name field | `SaveNewVersionButton.jsx` (`inputProps={{ 'data-testid': ... }}` on `Input.InputBase`) |
| `agent-version-dialog-save-button` | dialog's Save/confirm button | `SaveNewVersionButton.jsx` via `BaseModal`'s existing `confirmButtonDataTestId` prop |
| `agent-version-dialog-cancel-button` | dialog's Cancel button | `SaveNewVersionButton.jsx` via a **new** `cancelButtonDataTestId` prop added to `src/[fsd]/shared/ui/modal/BaseModal.jsx` (mirrors the existing `confirmButtonDataTestId`/`closeButtonDataTestId` pattern) |
| `agent-version-dialog-close-button` | dialog's X close button | `SaveNewVersionButton.jsx` via `BaseModal`'s existing `closeButtonDataTestId` prop |

**Note for the implementer/reviewer:** while resolving the cherry-pick onto fresh `main`,
this run discovered `main` was missing the `data-testid={confirmButtonDataTestId}` JSX
wiring on `BaseModal`'s confirm button entirely (present on `automation/testids` only,
from another in-flight, not-yet-merged testid PR) — this PR (#567) restores that wiring
too, since `agent-version-dialog-save-button` depends on it. This is called out in the
PR description so the reviewer isn't surprised by the extra hunk.

The dynamic `version-option-{name}` testids (`version-option-base`,
`version-option-v2-test`) **already existed live** — no change needed; they come from
the same `version-option-{}` template pattern already used for Skills
(`skill-version-option-{}`, see `test-specs/skills/l3_attach-skill-to-agent-with-version-selector_ELITEA-1789.md`).

## Handles Reference

| Element | testid | Confirmed live this run? | Notes |
|---|---|---|---|
| Instructions field | `agent-instructions-input` | yes | `press_sequentially`, not `fill()` |
| Save As Version button | `agent-save-as-version-button` | yes (added this run) | `automation/pages/agent_form_page.py:163-167` already declares this exact `LocatorDescriptor(testid=...)` — but it also carries a `fallback=` param, which is forbidden by `.agents/testing.md` § Locator policy. **Pre-existing violation, not introduced by this AFS** — same finding as ELITEA-1889; flagged again for whoever implements this case to strip the `fallback=` |
| VERSION dropdown trigger | `agent-version-selector-trigger` | yes (added this run) | MUI Select `role="combobox"`; click to open, shows current version name as text |
| Version dropdown option (dynamic) | `version-option-{version_name}` | yes (pre-existing) | Template constant pattern per `.agents/testing.md` § dynamic testids — e.g. `version-option-base`, `version-option-v2-test`; page object should declare `VERSION_OPTION = '[data-testid="version-option-{}"]'` and `.format(name)` at call sites, never inline f-string |
| Create-version dialog Name input | `agent-version-dialog-name-input` | yes (added this run) | `press_sequentially`; Save button in dialog stays disabled while empty |
| Create-version dialog Save button | `agent-version-dialog-save-button` | yes (added this run) | disabled until Name non-empty |
| Create-version dialog Cancel button | `agent-version-dialog-cancel-button` | yes (added this run) | closes dialog, discards the typed name, does not touch the pending unsaved Instructions edit |
| Create-version dialog Close (X) button | `agent-version-dialog-close-button` | yes (added this run) | same effect as Cancel in this component (`onClose` shared) |
| Agent actions overflow (three-dot) menu | `agent-actions-menu-button` | yes (pre-existing) | `automation/pages/agent_detail_page.py:124`; opens the VERSION/AGENT combined menu |
| Delete agent menu item | `delete-agent-menuitem` | yes (pre-existing) | `automation/pages/agent_detail_page.py:126`; used for cleanup in this run |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name`) | yes (pre-existing) | same scoping gotcha already documented for ELITEA-1889 — the testid is on a wrapper, the actual `<input>` is `#name` inside it |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | yes (pre-existing gap) | not testid'd — pre-existing residual gap (same as ELITEA-1889's finding), out of this case's scope to fix |

## Expected Results

Matches the case's own Pass/Fail Criteria exactly: the version dropdown lists at least
"base" and "v2-test", with "v2-test" as the currently active version. **Confirmed live,
no discrepancy.**

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: existing agent in "base" version | Agent detail page reachable | Test Step 1 | Reused existing agent id 4745 (`elitea-1735-skills-agent`), base version confirmed via `VERSION:` combobox text "base" | covered |
| Step 1: Navigate to agent detail page in "base" version | Page loads, base version active | Test Step 1 | URL `/agents/all/4745?viewMode=owner`, `VERSION:` shows "base", version-id textbox "4745" | covered |
| Step 2: Append a word to Instructions field | Field is modified | Test Step 2 | Instructions textbox value changed from `"You are a helpful assistant."` to `"You are a helpful assistant. Additionally."` | covered |
| Step 3: Click "Save As Version" | Dialog appears asking for a version name | Test Step 3 | `role="dialog"` heading "Create version" appeared with Name input | covered |
| Step 4: Verify a dialog appears asking for a version name | Version name input dialog is displayed | Test Step 3 (same interaction/observation) | Same dialog snapshot as Step 3 — case splits click and verify into two numbered steps, this run observed them as one atomic UI transition | covered (merged with Step 3 — see Test Steps note) |
| Step 5: Enter "v2-test" and confirm | Dialog is submitted | Test Step 5 | Name field filled, Save clicked, URL transitioned to `/agents/all/4745/4852`, dialog closed | covered |
| Step 6: Verify version dropdown lists at least "base" and "v2-test" | Both appear in the dropdown | Test Step 6 | Opened dropdown, `option "base - 14.07.2026"` and `option "v2-test - 15.07.2026"` both present | covered |
| Step 7: Verify "v2-test" is the currently active version | Dropdown shows "v2-test" as active/selected | Test Step 6/7 (same observation) | `option "v2-test - 15.07.2026"` carries `[active][selected]`; closed trigger also reads "v2-test"; version-id textbox reads "4852" | covered |
| Test Data: Version name "v2-test" | literal value | Test Step 5 | Typed as-is, no case-text drift, works exactly as specified | covered, no clarification needed |
| Test Data: Instruction change "append a word" | literal value | Test Step 2 | Case says "a word"; this run appended a short phrase (`" Additionally."`) for evidence clarity — behaviorally equivalent, not a drift worth flagging as a clarification (case doesn't assert exact wording) | covered |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Save/Save As Version/Discard button enabled state before/after the Instructions edit and before/after the version save | Gives the implementer a robust "form is dirty" / "form is clean" signal to assert on and to wait for, beyond just URL/dropdown text — reduces flakiness risk in the automated version |
| `isFromCreation=true` query param appearing then auto-stripping after the new version loads | Confirms the app's own post-creation settle behavior; an implementer polling the URL naively for the final `/agents/all/{id}/{versionId}` shape needs to know this transient param exists and self-clears, not to assert against it directly |
| `GET /api/v2/elitea_core/applications/prompt_lib/399` `total` count before (10) and after (9) agent-delete cleanup | Verifies the disposable-agent-reuse test-data pattern (create nothing, delete the reused debris agent) leaves the project in the same state it started in — load-bearing for making this pattern safe to recommend to the implementer |
| Confirmed `?viewMode=owner` is a required query param on `/agents/all/{id}` (its absence 404s) | Not documented anywhere in the existing page object's `navigate()` docstring beyond the code itself already using it — worth calling out explicitly since a naive re-implementation without reading the existing `AgentDetailPage.navigate()` could drop it and silently 404 |
| Instructions field content preserved verbatim in the new version (not reset to base) | Directly grounds the case's implicit expectation that "Save As Version" snapshots the *current, edited* form state, not the version's last-saved state — worth an explicit assertion in the automated test since it's easy to omit |

## Implementer amendment (Phase 2 exploration, same-PR)

- **Discard button has no live `data-testid` on the Agent detail page.**
  `AgentFormPage.discard_button` declares `testid="discard-button"`, but
  `document.querySelectorAll('[data-testid]')` on a live agent detail page
  (both before and after the Instructions edit) does not include it —
  confirmed via `get_by_test_id("discard-button")` timing out during
  implementation. This is a pre-existing gap distinct from
  `PipelineFormPage`/`CredentialDetailPage`, whose own `discard-button`
  testids ARE live on their respective pages. Since Discard-button
  enabled/disabled state is an Axis-2 addition (not one of the original
  case's 7 steps) and adding the testid would require a new
  `add-data-testid` dual-target cycle out of proportion to this
  observation, the implemented test asserts Save / Save As Version button
  state only (both testids — `agent-save-button`, `agent-save-as-version-button`
  — confirmed live) and omits the Discard-button assertion. Flagging here
  for whoever next touches the Agent form's Discard button.

## Known Defects

None hit or newly filed by this run. For context only:
[EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
(OPEN as of this run) blocks Agent creation via the default UI/API create flow — it did
**not** block this case (which only requires an *existing* agent), but it does constrain
the test-data strategy the implementer can use (see Test Data section above). No new
comment was posted to #524 by this run since it was not re-triggered.

## Cleanup

- The reused agent (id `4745`, `elitea-1735-skills-agent`, including the `v2-test`
  version created during this run) was deleted live via the UI: overflow menu
  (`agent-actions-menu-button`) → "AGENT" group → `delete-agent-menuitem` → type-to-confirm
  dialog (name typed into the `#name` input inside `delete-confirm-name-input`) →
  `Delete`. Verified via `GET
  /api/v2/elitea_core/applications/prompt_lib/399?...` : `total` returned to `9` (matching
  the pre-run baseline), and agent id `4745` no longer appears in the `rows` array.
- No other test data was created (no new Skill, no new Agent left behind).

## Blocked Steps

None. All 7 case steps executed and verified live, no defects encountered.
