# Test Case: Agent icon can be changed and persists on the agents list card

## Metadata
- **TMS ID**: ELITEA-1899
- **Linked Story**: none
- **Priority**: low (per case frontmatter) — mapped to `l3`
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI `automation/testids`
  → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (agent), 2026-07-16
- **Status**: **ready-for-automation** — case executed end-to-end live against a freshly-created
  disposable agent. All 7 case steps completed with no blockers, no product defects. Six missing
  testids were discovered absent live and added this run (see EliteaUI Changes below). One
  automation-relevant interaction quirk was discovered and documented (double-click-to-open the
  icon picker — see Automation Hints), and one case-text observation (the case's "Click Save"
  step 5 does not literally apply — see Coverage Map disposition) is recorded as a CLARIFICATION,
  not a defect (reverse-masking guard: the live product's actual behavior — instant auto-persist
  on selection — is correct and the case text is just imprecise about the mechanism).

## Preconditions
- User is logged in to the Elitea platform (satisfied automatically on localhost via
  `auth_state`/`VITE_DEV_TOKEN` — no Keycloak login step needed in this environment).
- An existing agent is available. **Per this project's Hard Rule 10 test-data guidance**, prefer a
  freshly-created, uniquely-named disposable agent over mutating a shared fixture agent's icon —
  icon state is a visible, shared-list-affecting mutation, so a fresh instance per run is
  load-bearing, not incidental (same reasoning as the `l3_remove-variable...ELITEA-1884` AFS).
  Create via `agent_api.create_agent(...)` (existing `automation/api/client.py::AgentAPI`), `yield`,
  then `agent_api.delete_agent(aid)` in a `finally`/fixture-teardown block.

## Test Data
### reuse-existing
- None required — the case is entirely self-contained (creates its own agent).

### generate-per-test (in test setup, cleaned up in its own teardown)
- Agent name: `autotest_ELITEA1899_icon` (or `f"autotest_{request.node.name}"[:32]` per the
  project's existing naming convention)
- Agent description: free text, e.g. "Agent for ELITEA-1899 icon change persistence check"
- No instructions/toolkits/skills needed — the case only exercises the icon field.

## Test Steps

**EXECUTED END-TO-END LIVE 2026-07-16** — all 7 case steps completed with no blockers.

1. Navigate to an agent detail page (`${BASE_URL}/agents/all/{id}?destTab=configuration...`)
   - **Verify**: agent detail page loads
   - **OBSERVED**: page loaded correctly, "General" section shows Name/Description/Tags fields
     with the icon avatar to the left of the Name field.
2. Click the agent icon near the agent name — verify an icon picker opens
   - **Verify**: icon picker dialog opens
   - **OBSERVED**: clicking the icon element (`agent-form-icon-button`) opens a dialog titled
     "Choose the image from the list or upload" (`agent-icon-picker-dialog`), showing a "Default"
     section (15 selectable preset icons plus a "reset to entity-type default" tile) and an
     "Uploaded" section (empty for a fresh agent, "No uploaded icons yet").
   - **AUTOMATION QUIRK (not a product defect — see Automation Hints)**: the icon element only
     opens the dialog on click when its hover-triggered edit-pencil overlay is already rendered.
     A single scripted `.click()` on the icon element (no prior `hover()`) lands on the
     *pre-hover* state and does not open the dialog — it merely triggers the hover state
     (edit-pencil overlay appears). A **second** click (now that the overlay is mounted) opens
     the dialog. Reproduced deterministically 2/2 attempts. Real users are unaffected because
     mouse movement naturally precedes a real click, giving the overlay time to mount before
     mousedown. **Automation implication**: the implementer's page-object method must `hover()`
     the icon element first (or click it twice), not click once and assert the dialog is open.
3. Select a different icon from the picker
   - **Verify**: the new icon is selected
   - **OBSERVED**: clicking a default icon option (`agent-icon-picker-option-{index}`) closes the
     dialog immediately and the icon renders in the agent header. Network: `PUT
     /api/v2/elitea_core/upload_icon/prompt_lib/399/{versionId}` → **200 OK**,
     response body `{"updated": true}`.
4. Verify the new icon is shown in the agent header immediately
   - **Verify**: agent header displays the newly selected icon
   - **OBSERVED**: confirmed via DOM inspection immediately after dialog close —
     `[data-testid="agent-form-icon-button"] img` src updated to the newly selected icon's URL
     (e.g. `https://dev.elitea.ai/app/default_entity_icons/image_1.png`) with no page reload, no
     delay beyond the `PUT` round-trip (~1.2s observed).
5. Click Save
   - **Verify** (per case): Save completes successfully
   - **OBSERVED — CLARIFICATION, not a defect (reverse-masking guard)**: the icon change is
     **already persisted server-side** by the `PUT .../upload_icon/...` call triggered on
     selection (step 3) — the main form's "Save" button remains **disabled** after an icon-only
     change (no other field was modified), because the icon field is not part of the
     formik-tracked draft; it is its own independent, immediately-committed mutation. There is no
     separate "click Save to persist the icon" action to perform in the live product — the case
     text describes an outcome (persistence) via a mechanism (clicking Save) that doesn't match
     how this feature is actually implemented. The **outcome** the case cares about (persistence)
     is still fully verified in steps 6–7 below. Filed as a CLARIFICATION on the tracker (see
     Known Defects Found) rather than asserting a literal Save click, per this project's
     reverse-masking guard (`test-case-analysis` skill).
6. Navigate to the Agents dashboard
   - **Verify**: Agents dashboard loads
   - **OBSERVED**: navigated to `${BASE_URL}/agents/all` (card list view, the default view
     toggle state); page loaded with the full agent list including the just-edited agent.
7. Verify the agent card shows the newly selected icon
   - **Verify**: the agent's card on the dashboard displays the new icon
   - **OBSERVED**: the card matching the agent name showed `[data-testid="entity-card-icon"] img`
     with the exact same `src` (`.../default_entity_icons/image_1.png`) as the header in step 4 —
     confirmed via direct DOM query scoped to the matching `[data-testid="entity-card"]`, not a
     visual/screenshot-only check.

## Expected Results
- Per case: the newly selected icon is visible on the agent's card in the Agents dashboard,
  confirming persistence after save.
- **Actual (observed 2026-07-16)**: matches expected. Icon changed in the picker, appeared
  immediately in the header (step 4), and the identical icon URL was confirmed present on the
  dashboard card after navigating away and back (step 7). Case **PASSES**. Zero console
  errors/warnings throughout (checked both `warning` and `error` levels across the full run).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | session valid | n/a (auto via `auth_state`) | — | asserted (environment-level) |
| Precondition: existing agent available | agent exists | AFS precondition (fresh disposable agent) | — | covered — created via UI create-form live this run (id 4935, deleted at cleanup); implementer should use `AgentAPI.create_agent()` |
| Step 1: Navigate to agent detail page | detail page loads | AFS step 1 | step 1 | covered |
| Step 2: Click agent icon → icon picker opens | dialog opens | AFS step 2 | step 2 | covered — dialog confirmed via `agent-icon-picker-dialog` testid; automation quirk (double-click/hover-first) documented, not a defect |
| Step 3: Select a different icon | new icon selected | AFS step 3 | step 3 | covered — `PUT .../upload_icon/.../{versionId}` → 200, `{"updated": true}` |
| Step 4: New icon shown in header immediately | header updates | AFS step 4 | step 4 | covered — DOM `img.src` verified immediately post-selection, no reload |
| Step 5: Click Save → Save completes successfully | save succeeds | AFS step 5 | step 5 | **CLARIFICATION, not covered as literally worded** — no separate Save action exists for icon changes (already persisted via the picker's own PUT call); implementer should NOT assert on the main Save button for icon persistence — assert on the PUT response / DOM update instead. Filed as tracker CLARIFICATION, see Known Defects. |
| Step 6: Navigate to Agents dashboard | dashboard loads | AFS step 6 | step 6 | covered |
| Step 7: Agent card shows newly selected icon | icon persists on card | AFS step 7 | step 7 | covered — DOM `img.src` on `entity-card-icon` matched header value exactly |
| Objective: icon change persists after save, shown immediately + on list card | as above | AFS steps 3–4, 7 | steps 3,4,7 | covered (via auto-persist mechanism, not literal Save click) |

### Axis 2 — Analyst additions

- Asserted the *exact* icon URL (`img.src`) matches between header (step 4) and dashboard card
  (step 7), not just "some non-default icon is shown" — a stronger, more precise persistence
  check than the case's own wording, made possible by the new `entity-card-icon` /
  `agent-form-icon-button` testids.
- Asserted 0 console errors/warnings across the whole flow (open picker → select → navigate away
  → navigate back) — the case doesn't ask for this but it's part of this project's standard
  side-channel check.
- Documented the double-click/hover-first automation quirk for step 2 — grounded in a
  deterministic 2/2 reproduction with the exact testid selector, not a guess.
- Verified the underlying network contract (`PUT /api/v2/elitea_core/upload_icon/prompt_lib/399/
  {versionId}` → 200, `{"updated": true}`) as the authoritative persistence signal, since the UI's
  main Save button is not part of this feature's persistence path.

## Cleanup
- **Agent created during this pass (id 4935, name `autotest_ELITEA1899_icon`) was deleted** via
  the UI Delete flow (detail page → overflow "⋮" menu → "Delete agent" → typed exact name to
  confirm → Delete). Verified via network: `DELETE
  /api/v2/elitea_core/application/prompt_lib/399/4935` → **204 No Content**. Nothing left behind
  from this analysis run.
- **Recommendation for the implementer**: create per-test via `agent_api.create_agent(...)`,
  `yield`, then `agent_api.delete_agent(aid)` in a `finally`/fixture-teardown block — same pattern
  as `agent_with_toolkit_instructions`/`agent_id` fixtures. A fresh instance per run is
  load-bearing (icon state is a visible list-affecting mutation), not incidental.

## Concrete Handles (discovered during exploration; six testids added this run)

All handles below were directly observed live via Playwright MCP against
`http://localhost:5173/agents/all/{id}` (detail/edit form), `/agents/create` (create form, same
icon-picker component), and `/agents/all` (dashboard card list).

| Element | Testid (confirmed) | Notes |
|---|---|---|
| Agent icon avatar/button (opens picker) — detail/edit form | `agent-form-icon-button` | **NEW — added this run.** `EliteaUI/src/pages/Applications/Components/Applications/ApplicationEditForm.jsx` (the actual component the `/agents/all/{id}` detail page renders — NOT `CreateAgentForm.jsx`, which is a *different* component used only by the `/agents/create` new-agent flow; both happen to reuse the identical `agent-name-input`/`agent-description-input` testid strings, which is what caused the initial confusion — see Automation Hints). Testid also added to `CreateAgentForm.jsx` for the create-form path (same testid string, mutually exclusive routes, matches existing `agent-name-input` reuse pattern). |
| Icon picker dialog | `agent-icon-picker-dialog` | **NEW.** `EliteaUI/src/components/SelectIconDialog.jsx`, passed through `BaseModal`'s existing `data-testid` prop. |
| Icon picker close (X) button | `agent-icon-picker-close-button` | **NEW.** Passed via `BaseModal`'s existing `closeButtonDataTestId` prop — no BaseModal changes needed, prop already existed. |
| "Reset to default" icon option | `agent-icon-picker-default-icon` | **NEW.** `ProjectIconItem.jsx`, first item in the "Default" section. |
| Default icon option (indexed) | `agent-icon-picker-option-{index}` | **NEW, dynamic.** `index` from `applicationDefaultIcons.map((icon, index) => ...)` in `SelectIconDialog.jsx`. Class-level template pattern for the page object: `'[data-testid="agent-icon-picker-option-{}"]'.format(index)`. 15 options observed live (indices 0–14). |
| Uploaded icon option (indexed) | `agent-icon-picker-uploaded-{index}` | **NEW, dynamic.** `index` from `iconList.map((icon, index) => ...)` in `SelectIconDialog.jsx`. Empty list observed this run (no uploaded icons on a fresh project) — pattern confirmed from source, not exercised live (no upload was performed; case doesn't require it). |
| Agent card icon (Agents dashboard list) | `entity-card-icon` | **NEW.** `EliteaUI/src/components/Card.jsx`, sibling of the existing `entity-card` (whole card) / `entity-card-name` testids — same generic component used for agents/skills/pipelines cards, scope is agent-icon-relevant only (per this project's testid-scope ruling, only added where a test now touches it). |
| Agent card (whole card, pre-existing) | `entity-card` | Pre-existing; used to scope-find the target card by `textContent.includes(name)` before reading its icon. |
| Agent Name field (create/detail) | `agent-name-input` | Pre-existing, unchanged. |
| Agent Description field (create/detail) | `agent-description-input` | Pre-existing, unchanged. |
| Delete agent — overflow menu button | `agent-actions-menu-button` (auto-derived testid, confirmed present) | Pre-existing; used for cleanup this run. |
| Delete agent — menu item | `delete-agent-menuitem` (auto-derived testid, confirmed present) | Pre-existing; used for cleanup this run. |
| Delete confirmation — name input | `delete-confirm-name-input` (auto-derived testid, confirmed present) | Pre-existing; used for cleanup this run. |

### Ready Locators for Page Objects

```python
# LocatorDescriptor definitions — testid only, no fallback needed
agent_icon_button = LocatorDescriptor(testid="agent-form-icon-button")
icon_picker_dialog = LocatorDescriptor(testid="agent-icon-picker-dialog")
icon_picker_close_button = LocatorDescriptor(testid="agent-icon-picker-close-button")
icon_picker_default_icon = LocatorDescriptor(testid="agent-icon-picker-default-icon")
# Dynamic (class-level template constant, per this project's canonical pattern):
ICON_PICKER_OPTION = '[data-testid="agent-icon-picker-option-{}"]'
ICON_PICKER_UPLOADED = '[data-testid="agent-icon-picker-uploaded-{}"]'
entity_card_icon = LocatorDescriptor(testid="entity-card-icon")
```

## Network Behavior
- `PUT /api/v2/elitea_core/upload_icon/prompt_lib/399/{versionId}` — icon change, fired
  immediately on selecting an option in the picker (no separate Save needed). **200 OK**,
  response body `{"updated": true}`.
- `GET /api/v2/elitea_core/default_icons/prompt_lib/399` — loads the picker's "Default" icon set
  when the dialog opens. 200 OK.
- `GET /api/v2/elitea_core/upload_icon/prompt_lib/399?limit=20&skip=0` — loads the picker's
  "Uploaded" icon set. 200 OK, empty for a fresh project.
- `POST /api/v2/elitea_core/applications/prompt_lib/399` — agent creation (setup). 201 Created.
- `DELETE /api/v2/elitea_core/application/prompt_lib/399/4935` — cleanup delete. 204 No Content.

## Known Defects Found During Exploration

- **No product defect found.** The flow works end-to-end exactly as the case's *intent*
  describes (icon changes, shows immediately, persists on the list card).
- **CLARIFICATION filed (case-text drift, not a bug — reverse-masking guard applied):** the
  case's step 5 ("Click Save") does not correspond to any real action in the live product for
  this specific field — icon changes commit immediately via their own `PUT` call, independent of
  the form's Save/Discard state. Filed as a tracker issue labelled `question` per this project's
  protocol (options considered: (a) update the TMS case text to remove/reword step 5, (b) leave
  the case as-is and have the automated test simply not perform a literal "click Save" action for
  this step, recommending (b) since forcing a Save click would either no-op harmlessly or, if the
  Save button happens to be enabled from an unrelated pending edit, would trigger an unrelated
  save that isn't part of this case's intent). Filed:
  [EliteaAI/elitea-testing-public#566](https://github.com/EliteaAI/elitea-testing-public/issues/566)
  ("Found while working #103").
- **Automation-relevant UI interaction quirk (not filed as a bug — documented here and in
  Automation Hints instead, since it doesn't affect real users):** the icon avatar requires two
  clicks (or a `hover()` before the click) to open the picker via scripted automation, because the
  clickable edit-pencil overlay only mounts on hover and a single scripted `.click()` doesn't wait
  for it. Reproduced deterministically (2/2). Confirmed via a second, independent click attempt in
  the same session (not a stale/one-off artifact) — this is a genuine DOM/interaction-timing
  characteristic of `EntityIcon.jsx`'s hover-then-render pattern, not synthetic-input poisoning
  (Playwright's native `click()` was used throughout, no `page.evaluate()` clicks).

## Blocked Steps

- **None.** All 7 case steps completed live with no blockers.

## Automation Hints

- Framework: Playwright + pytest, confirmed from `.agents/testing.md`.
- **No existing spec covers this case's observable.** Checked `automation/pages/agent_detail_page.py`,
  `automation/pages/agent_form_page.py`, `automation/pages/agents_list_page.py`, and
  `test-specs/agents/` for any icon-related content before starting — none found (`grep -ril icon`
  turned up unrelated hits like "Read out"/attachment icons in other tests, not agent-icon-picker
  content). **Conclusion: `ready-for-automation` (fresh implementation).**
- **Critical: the detail/edit page and the create page use two DIFFERENT React components** for
  the agent form — `ApplicationEditForm.jsx` (detail/edit, what `/agents/all/{id}` renders) vs
  `CreateAgentForm.jsx` (create-only, what `/agents/create` renders) — despite sharing identical
  `agent-name-input`/`agent-description-input` testid strings. The icon-button testid
  (`agent-form-icon-button`) was added to **both** files this run so it works on either route.
  Implementer note: if a future testid only seems to "work" on one of the two agent-form routes,
  check whether the edit is missing from the sibling component before assuming a flake.
- **Interaction pattern for opening the picker**: use `page.hover(icon_locator)` immediately before
  `page.click(icon_locator)` (or click twice) — see the automation quirk documented in Known
  Defects. A bare single `.click()` will only render the hover overlay and not open the dialog.
- **Recommended implementation shape**: a new focused test (e.g.
  `TestAgentIconManagement::test_agent_icon_change_persists_on_list_card` in
  `tests/ui/agents/test_agent_management.py` or a new file) using
  `agent_api.create_agent(...)` → `yield` → `agent_api.delete_agent(aid)` in teardown, then:
  1. Navigate to the agent detail page.
  2. `hover()` then `click()` the `agent-form-icon-button` to open the picker.
  3. Click an `agent-icon-picker-option-{n}` (n != current, e.g. a fixed known index like 3) and
     capture its resulting `img.src`.
  4. Assert the header icon (`agent-form-icon-button img`) src equals the captured value
     immediately (no reload) — optionally confirm via the underlying `PUT
     .../upload_icon/.../{versionId}` network response equals `{"updated": true}`.
  5. Navigate to `/agents/all`, locate the matching `entity-card` by name, and assert its
     `entity-card-icon img` src equals the same captured value.
  6. Do **not** assert on the main form Save/Discard buttons for this flow — they are unrelated to
     icon persistence (see Coverage Map disposition for step 5).
- All Concrete Handles above are confirmed against the current live DOM as of this run (6 new
  testids added, verified present after HMR reload and after a full page navigation).

## EliteaUI Changes (testids added this run)

Committed straight onto `automation/testids` and pushed (commit `6bb6a23c`, message
`test: [EL-0000] add data-testid for agent icon picker flow (ELITEA-1899)` — note: this repo's
commitlint requires the `[EL-XXXX]` ticket format, not `[ELITEA-XXXX]`; `EL-0000` is the
project's existing convention for edits with no matching internal EL ticket, same pattern seen in
prior history e.g. `fix: [EL-0000] Use info toast for copy action in ProjectContext`). Per this
project's suspended-draft-PR policy (2026-07-16), this is the terminal step for testid work — no
`main` PR was opened; a human will cherry-pick when ready.

| File | Change |
|---|---|
| `src/components/EntityIcon.jsx` | accept optional `data-testid` prop, forward to root container `Box` |
| `src/pages/Applications/Components/Applications/ApplicationEditForm.jsx` | pass `data-testid="agent-form-icon-button"` to `EntityIcon` (detail/edit form) |
| `src/[fsd]/features/agent/ui/agent-details/configurations/form/CreateAgentForm.jsx` | pass `data-testid="agent-form-icon-button"` to `EntityIcon` (create form) |
| `src/components/Card.jsx` | pass `data-testid="entity-card-icon"` to `EntityIcon` (list/dashboard card) |
| `src/components/SelectIconDialog.jsx` | pass `data-testid="agent-icon-picker-dialog"` + `closeButtonDataTestId="agent-icon-picker-close-button"` to `BaseModal`; pass `data-testid="agent-icon-picker-default-icon"` / `agent-icon-picker-option-{index}` / `agent-icon-picker-uploaded-{index}` to the icon-option items |
| `src/[fsd]/features/settings/ui/project-general/general/select-project-icon/ProjectIconItem.jsx` | accept optional `data-testid` prop, forward to root `Box` |
| `src/[fsd]/features/settings/ui/project-general/general/select-project-icon/UserIconItem.jsx` | accept optional `data-testid` prop, forward to the wrapped `ProjectIconItem` |

Verified live: all 6 new testids resolve correctly in the DOM (icon button, dialog, close button,
default-icon option, indexed default options, and the dashboard card icon) after HMR reload and
after a full navigation reload.
