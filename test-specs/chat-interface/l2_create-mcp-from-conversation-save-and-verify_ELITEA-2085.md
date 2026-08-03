# Test Case: Chat – Create MCP from Conversation – Save Configuration and Verify MCP is Created

## Metadata
- **TMS ID**: ELITEA-2085
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", observed live as `projectId=399`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live (all 12 steps observed against the real app). No product defect found. New page-object surface needed only for the in-chat MCP-canvas *entry point*, *create button*, *close button*, and *title* — the underlying form fields (Name/URL/Client Secret/etc.) are the exact same `ToolkitForm`/`McpFormPage` component and testids already used by the standalone MCP-creation flow (`mcp_form_page.py`), confirmed by reading `ToolkitEditor.jsx`'s render of the shared `ToolkitForm`/`ToolkitTypeSelector` components.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation in the Chats section — satisfied directly via `ChatPage.click_create_conversation()` (existing method); unlike ELITEA-2079's precondition chain, this case has **no dependency on any prior un-automated sibling case** — "an open conversation" is the whole precondition, and any conversation (freshly created or pre-existing) satisfies it.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Private project (`${ELITEA_PROJECT_ID}`, `399`) — ambient default for a fresh dev-token session in this environment.

### generate-per-test
- **New conversation** — via `ChatPage.click_create_conversation()`; cleaned up via `conversation_api.delete_conversation(id)`.
- **New MCP "test"** — case's literal Test Data: MCP Name `test`, URL `https://api.githubcopilot.com/mcp`, Client Secret (any test value — this analysis used a dummy placeholder string; a real value is not required to reach "Not Connected"/reach the participant-listed state, since the MCP never actually authenticates in this flow). Cleaned up via the MCP's own delete (API or UI, `toolkit_api`) — do NOT rely on conversation deletion to cascade.

## Test Steps

1. Navigate to Chats and open a conversation.
   - **Verify**: `ChatPage.click_create_conversation()`; conversation view displayed (message input visible).
2. Click + icon, select "MCPs", click "+ Create New MCP".
   - **Verify**: `plus-menu-button` → `mcps-menuitem` (hover) → `mcps-create-new-button` (all confirmed **on-main ✓**, existing pattern: `PlusChatButton.jsx`'s `EXPANDABLE_ITEMS` config + `PlusChatSubmenu.jsx`'s `${sectionKey}-create-new-button`, `sectionKey="mcps"`). "New MCP" canvas opens.
3. Click "Remote" tab and select "Remote MCP".
   - **Verify**: `category-filter-tab` (confirmed **on-main ✓** — 2 instances live, text "Local"/"Remote"; filter by `has_text=re.compile("^Remote$")`) → `toolkit-type-card-mcp` (confirmed **on-main ✓**, existing `McpFormPage.remote_mcp_type_card`; live card text = "Remote MCP", matching this step exactly). Configuration canvas opens.
4. Type "test" in "Toolkit Name *" field.
   - **Verify**: `toolkit-form-name-input` (confirmed **on-main ✓**, existing `McpFormPage.name_input` — same component/testid as the standalone MCP-creation form).
5. Type "https://api.githubcopilot.com/mcp" in "Url *" field.
   - **Verify**: `toolkit-field-url-input` (confirmed **on-main ✓**, existing `McpFormPage.url_input`).
6. Enter a test secret value in "Client Secret" field.
   - **Verify**: `toolkit-field-client_secret-input-field` (confirmed **on-main ✓**, existing `McpFormPage.client_secret_input_field` — the actual fillable input; `toolkit-field-client_secret-input` is the wrapping container, also present, per existing page object's dual-field pattern).
7. Click the "Create" button.
   - **Verify**: Create button — confirmed **NO TESTID** live (role-based `get_by_role("button", name="Create")` only; `CreateToolkitButton.jsx`, the component `ToolkitEditor.jsx` renders for BOTH Toolkit and MCP creation, carries zero `data-testid` at any level — confirmed by reading the full component source). `testid needed: mcp-canvas-create-button`, see § Concrete Handles for the threading recommendation. Confirmed live: `POST /api/v2/elitea_core/tools/prompt_lib/399` → `201 Created`; success toast "The toolkit has been created successfully" (`toast-message`, confirmed **on-main ✓**) — matches this step's expected result text exactly.
8. Verify the canvas header shows "test" as the MCP name.
   - **Verify**: confirmed live — canvas header title reads exactly `test`. Title element — confirmed **NO TESTID** live (`EditorHeader.jsx`'s title `Typography`; `ToolkitEditor.jsx`'s `<BaseEditor title={toolkitName}>` call does not pass `titleTestId`, though the prop exists and is wired end-to-end). `testid needed: mcp-canvas-title`, see § Concrete Handles.
9. Verify a "Not Connected" warning banner appears with orange background and "Login" button.
   - **Verify**: `toolkit-connection-status` (confirmed **on-main ✓**, existing `McpFormPage.connection_status` — SAME component/testid reused directly inside the chat canvas, no gap). Confirmed live: orange-background banner with a "Login" button, text content includes "Not Connected"-class messaging (live banner is partially obscured by the success toast in the same viewport region; both are simultaneously present and independently assertable — the toast auto-dismisses, the banner persists).
10. Click X to close the canvas.
    - **Verify**: canvas close button — confirmed **NO TESTID** live (same `EditorHeader.jsx` close `IconButton` as the Pipeline/Agent canvases; `ToolkitEditor.jsx`'s `<BaseEditor>` call does not pass `closeButtonTestId`). `testid needed: mcp-canvas-close-button`, see § Concrete Handles. Confirmed live via bounding-box probe (first header button, no visible text) that clicking it fully unmounts the canvas (all canvas-scoped testids — `toolkit-form-name-input`, `toolkit-field-url-input`, etc. — absent from the DOM afterward). Only conversation window displayed.
11. Verify a "MCPS" section appears in the PARTICIPANTS panel with "test" listed.
    - **Verify**: expand via `chat-participants-panel-toggle-button` (confirmed **on-main ✓**). Confirmed live, exact text: `PARTICIPANTS` / `MCPS` / `test`. Badge testids `chat-participants-badge-mcp` / `chat-participants-badge-icon-mcp` confirmed **on-main ✓** (same `PARTICIPANTS_BADGE` dynamic template, `.format("mcp")`, already used for Agents/Pipelines/Toolkits participant types).
12. Verify an orange warning triangle icon appears next to the MCP with text "Server is disconnected! Reconnect it to use. Log in."
    - **Verify**: confirmed live, exact text match: `Server is disconnected! Reconnect it to use. Log in.` Warning icon element — confirmed **NO TESTID** live (`ParticipantWarning.jsx`, the shared warning-icon component rendered for BOTH MCP and Pipeline misconfigured/disconnected participants per issues #684/#687 — zero `data-testid` anywhere in the file). `testid needed: chat-participant-warning-icon` (generic name — the component is already participant-type-agnostic, not a feature-scoped hardcode inside a shared component; see § Concrete Handles).

## Expected Results
- All 12 steps pass cleanly as specced above. No product defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: open conversation | — | step 1 | `click_create_conversation()` | asserted |
| 1 Navigate to Chats, open conversation → Conversation view displayed | conversation displayed | step 1 | message input visible | asserted |
| 2 Click +, MCPs, + Create New MCP → New MCP canvas opens | canvas opens | step 2 | `mcps-menuitem`/`mcps-create-new-button` click chain | asserted |
| 3 Click Remote tab, select Remote MCP → Configuration canvas opens | config canvas opens | step 3 | `category-filter-tab`("Remote") + `toolkit-type-card-mcp` | asserted |
| 4 Type "test" in Toolkit Name → Name entered | name entered | step 4 | `toolkit-form-name-input` value | asserted |
| 5 Type URL → URL entered | url entered | step 5 | `toolkit-field-url-input` value | asserted |
| 6 Enter test secret → Secret entered | secret entered | step 6 | `toolkit-field-client_secret-input-field` value | asserted |
| 7 Click Create → MCP saved, success message | saved + toast | step 7 | `201` POST response + `toast-message` text | asserted |
| 8 Verify canvas header shows "test" | header updated | step 8 | canvas title text == "test" | asserted |
| 9 Verify Not Connected banner, orange bg, Login button | disconnected warning visible | step 9 | `toolkit-connection-status` + banner text/Login button | asserted |
| 10 Click X to close → Only conversation window displayed | canvas closed | step 10 | canvas testids absent from DOM post-close | asserted |
| 11 Verify MCPS section in PARTICIPANTS with "test" | MCP listed | step 11 | `PARTICIPANTS`/`MCPS`/`test` text + badge testids | asserted |
| 12 Verify orange warning triangle + exact disconnected text | disconnected warning in PARTICIPANTS | step 12 | exact text match "Server is disconnected! Reconnect it to use. Log in." | asserted |
| Expected Final State: "MCP 'test' created and appears in PARTICIPANTS with disconnected/not-connected state" | — | steps 7, 11, 12 | — | asserted |
| Pass/Fail: "MCP is not created or does not appear in PARTICIPANTS" is FAIL condition | — | all steps | side-channel console/network checks throughout | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 7 asserts the underlying `POST /api/v2/elitea_core/tools/prompt_lib/399` → `201` — *added: confirms creation via the API, not just the toast/DOM transition, matching this suite's established pattern.*
- Step 10 asserts the canvas's own testids are fully absent from the DOM post-close (not just "a click happened") — *added: rules out a partial/animating-close false-positive.*
- A pre-existing, already-tracked React console warning ("Each child in a list should have a unique 'key' prop", `CategorySection.jsx` inside `ToolkitTypeSelector.jsx`) fires during step 3's type-selection render — confirmed via `gh issue list` dedup check to already be tracked as issue #656 (filed against the identical component/warning during ELITEA-1868 analysis). **Not filed as a new defect** — same root cause, same component, pre-existing. Recommend the implementation filter this specific console message the same way `test_create_agent_via_chat_canvas.py` filters its own known-noise console pattern, so it can't mask a genuinely NEW console error appearing alongside it.
- Console/network side-channel checked after every step — confirmed clean of NEW errors/failed requests (the one pre-existing #656 warning aside) across all 12 steps in this session.

## Cleanup
1. Delete the created MCP/toolkit (`toolkit_api.delete_toolkit(id)` or the UI's MCPs-list delete action).
2. Delete the created conversation via `conversation_api.delete_conversation(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `cd EliteaUI && git fetch origin` (this session) then `git grep` on `origin/main`.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| `+` menu → MCPs menuitem | `mcps-menuitem` | on-main ✓ | `PlusChatButton.jsx`'s `EXPANDABLE_ITEMS` static config. |
| `+` menu → MCPs submenu → "+ Create New MCP" | `mcps-create-new-button` | on-main ✓ | `PlusChatSubmenu.jsx`'s `${sectionKey}-create-new-button`, `sectionKey="mcps"`. |
| "Local"/"Remote" category tabs | `category-filter-tab` | on-main ✓ | Shared across both instances — disambiguate by `.filter(has_text=...)`, matching this project's existing multi-instance-testid idiom (e.g. `PLUS_MENU_ITEM_SUFFIX`-style counting). |
| "Remote MCP" type card | `toolkit-type-card-mcp` | on-main ✓ | Existing `McpFormPage.remote_mcp_type_card` — SAME component reused inside the chat canvas (`ToolkitTypeSelector.jsx`), confirmed identical testid live. |
| Toolkit Name field | `toolkit-form-name-input` | on-main ✓ | Existing `McpFormPage.name_input`. |
| Url field | `toolkit-field-url-input` | on-main ✓ | Existing `McpFormPage.url_input`. |
| Client Secret field | `toolkit-field-client_secret-input-field` | on-main ✓ | Existing `McpFormPage.client_secret_input_field`. |
| Canvas Create button | **NO TESTID** | needs-adding | `testid needed: mcp-canvas-create-button`. `CreateToolkitButton.jsx` (shared between Toolkit and MCP creation, `ToolkitEditor.jsx` renders it for both) has zero `data-testid`. **Declared improvisation** (canon gap — no existing precedent for threading a per-entity-type testid through this specific shared button): recommend an optional `testId` prop on `CreateToolkitButton` (mirrors the `closeButtonTestId`/`titleTestId` optional-prop shape `BaseEditor`/`EditorHeader` already use), with `ToolkitEditor.jsx` passing `isMCP ? 'mcp-canvas-create-button' : undefined` — only the MCP branch is named since this case is the only one touching this button on this batch; the Toolkit-creation call path is untouched (case scope per `.agents/role-overrides.md` § locator policy — "touches" = this case's own executed path). Currently only resolvable via `get_by_role("button", name="Create")`. |
| Canvas title (post-create, shows entity name) | **NO TESTID** | needs-adding | `testid needed: mcp-canvas-title`. `ToolkitEditor.jsx`'s `<BaseEditor title={toolkitName}>` call omits `titleTestId` (prop exists, wired end-to-end in `EditorHeader.jsx`). Same conditional-naming approach as the Create button: `isMCP ? 'mcp-canvas-title' : undefined`. |
| Canvas X (close) button | **NO TESTID** | needs-adding | `testid needed: mcp-canvas-close-button`. Same `EditorHeader.jsx` close `IconButton`, same omitted `closeButtonTestId` prop, same conditional-naming approach: `isMCP ? 'mcp-canvas-close-button' : undefined`. Currently only resolvable via a position-based probe (first header button, no text) — blocks step 10 without this addition. |
| "Not Connected" disconnected-status banner | `toolkit-connection-status` | on-main ✓ | Existing `McpFormPage.connection_status` — SAME component reused directly inside the chat canvas, confirmed identical testid live. No gap. |
| Participants badge / popper (MCPS section) | `chat-participants-badge-mcp`, `chat-participants-badge-icon-mcp` | on-main ✓ | Existing dynamic `PARTICIPANTS_BADGE` template (`.format("mcp")`) already in `chat_page.py` — no new handle needed. |
| Participant-row disconnected-warning icon/tooltip | **NO TESTID** | needs-adding | `testid needed: chat-participant-warning-icon`. `ParticipantWarning.jsx` (shared between MCP and Pipeline participant-warning rendering — confirmed by cross-referencing issues #684/#687, which describe the identical component's behavior for both entity types) has zero `data-testid` anywhere in the file. A single, UNconditional generic testid is appropriate here (not a ternary-pair or feature-scoped-hardcode situation — the component is already entity-agnostic by design, so a generic name matches the shared-component naming rule directly, no per-caller threading needed). |

## Network Behavior
- `POST /api/v2/elitea_core/tools/prompt_lib/399` → `201 Created` on Create (step 7).
- No 4xx/5xx observed at any point in this session's execution of this case's own 12 steps.

## Known Defects Found During Exploration
None. One pre-existing, already-tracked non-blocking console warning observed and dedup-checked (not re-filed):
- **Issue #656** ("[MINOR][ELITEA-1868] Toolkit type-picker: React 'unique key prop' console warning in CategorySection list") — fires identically during this case's step 3 (MCP type-selection render uses the same `ToolkitTypeSelector`/`CategorySection` components as the standalone Toolkit-creation flow #656 was filed against). Confirmed via `gh issue list --label bug` dedup check before considering a new filing — same component, same warning text, already tracked. Recommend filtering this specific console message in the automated test (matching the project's existing precedent for filtering known dev-only noise, e.g. `test_edit_instructions`'s #538 filter).

## Blocked Steps
None. All 12 case steps were executed and observed end-to-end live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Reuse, don't rewrite**: the MCP-creation FORM itself (`toolkit-form-name-input`, `toolkit-field-url-input`, `toolkit-field-client_secret-input-field`, `toolkit-type-card-mcp`, `toolkit-connection-status`) is the exact same `ToolkitForm`/`ToolkitTypeSelector` component set the standalone `McpFormPage` already drives — compose `ChatPage` (canvas entry point, close, participants) + `McpFormPage` (form internals) on the SAME `page`, mirroring the `AgentFormPage`-reuse pattern from `test_create_agent_via_chat_canvas.py`. Do not write a new form-field page object from scratch.
- Three `needs-adding` testids share one shape (an `isMCP`-conditional optional prop on a component already shared with the plain-Toolkit creation path): `mcp-canvas-create-button` (on `CreateToolkitButton.jsx`, new `testId` prop — DECLARED IMPROVISATION, no existing precedent for this exact button, see § Concrete Handles), `mcp-canvas-title` and `mcp-canvas-close-button` (both on `ToolkitEditor.jsx`'s `<BaseEditor>` call, reusing `BaseEditor`/`EditorHeader`'s ALREADY-WIRED `titleTestId`/`closeButtonTestId` props — purely a missing call-site value, same shape as `agent-canvas-title`/`agent-canvas-close-button` added for ELITEA-2166). A fourth, independent testid is needed for the PARTICIPANTS-panel warning icon: `chat-participant-warning-icon` on `ParticipantWarning.jsx` (unconditional — the component is already entity-type-agnostic).
- No sanctioned-RED / known-defect handling needed — this case's happy path is fully clean.
- Wait strategy: no fixed sleeps — `wait_for(state="visible")` on the connection-status banner and the PARTICIPANTS panel row after the toggle click; standard toast-visible/toast-dismissed idiom (`wait_for_toast()`, `dismiss_toast()`, existing `ChatPage` methods) for the success toast in step 7.
