# Test Case: Chat – Create MCP from Conversation – Enter Configuration Data and Discard Changes

## Metadata
- **TMS ID**: ELITEA-2084
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", `projectId=399`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, `.agents/test-automation.yaml` batch tiering, chat-remaining-w16)
- **Status**: **ready-for-automation** — case executed end-to-end live (all 12 steps observed against the real app) this session. No product defect found. This is the Discard-variant sibling of the already-automated ELITEA-2085 (Save-and-verify) and shares its canvas/form page-object surface entirely — the ONLY new page-object surface needed is the MCP canvas's Discard chrome (`discard_button`/`discard_confirm_modal`/`discard_confirm_button`), which **already has its testids on `automation/testids`** (added as an `isMcpTestIdScope`-conditional mirror during ELITEA-2081's Toolkit-canvas Discard implementation — confirmed live via `page.evaluate` DOM probe this session, no new `add-data-testid` work required). `McpCanvasPage` itself just needs the three new `LocatorDescriptor` fields + `click_discard()`/`confirm_discard()` methods, mirroring `ToolkitCanvasPage`'s existing ELITEA-2081 shape 1:1.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation in the Chats section — satisfied via the `conversation_id` fixture (API-created, real `/chat/{id}` URL), same precondition pattern as the sibling ELITEA-2085/ELITEA-2076/ELITEA-2081 cases in this batch family.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Private project (`${ELITEA_PROJECT_ID}`, `399`) — ambient default for a fresh dev-token session in this environment.

### generate-per-test
- **New conversation** — via the `conversation_id` fixture; auto-deleted after the test.
- Case's own literal Test Data: MCP Name `test`, URL `https://api.githubcopilot.com/mcp`, Client Secret (any test value — this analysis used a dummy placeholder string). **No MCP is ever persisted by this flow** (Discard, never Create) — confirmed live via the network-level check in step 9 below; nothing to clean up on the MCP side.

## Test Steps

1. Navigate to Chats and open a conversation.
   - **Verify**: `ChatPage.navigate_to_chat(conversation_id=...)` (existing method, `conversation_id` fixture); `message_input` (`chat-message-input`) visible.
2. Click the + icon and select "MCPs".
   - **Verify**: `plus-menu-button` click → `mcps-menuitem` (hover, confirmed **on-main ✓**) becomes visible. MCPs submenu opens (search box + entity list + "Create New MCP" menuitem, confirmed live).
3. Click "+ Create New MCP" at the top.
   - **Verify**: `mcps-create-new-button` (confirmed **on-main ✓**). Confirmed live: canvas slides in on the right, heading "New MCP", header shows X / "Discard" (disabled) / "Create" (disabled) — both start disabled (form not yet dirty).
4. Verify "Local" and "Remote" tabs are shown.
   - **Verify**: `category-filter-tab` (confirmed **on-main ✓**, 2 instances — filter by text "Local"/"Remote"). Confirmed live: both tabs visible; Local panel shows "Still no local MCP available..." empty state, Remote panel shows the "Remote MCP" type card.
5. Click the "Remote" tab and select "Remote MCP".
   - **Verify**: `category-filter-tab`(text="Remote") → `toolkit-type-card-mcp` (confirmed **on-main ✓**, existing `McpFormPage.remote_mcp_type_card`). Confirmed live: heading updates to "New Remote MCP"; the full `ToolkitForm` configuration panel renders (Toolkit Name, Description, Url, Headers, Client Id, Client Secret, Scopes, Timeout, caching/SSL toggles, Tools section).
6. Type "test" in "Toolkit Name *" field.
   - **Verify**: `toolkit-form-name-input` (confirmed **on-main ✓**, existing `McpFormPage.name_input`). Confirmed live: field shows `test`.
7. Type "https://api.githubcopilot.com/mcp" in "Url *" field.
   - **Verify**: `toolkit-field-url-input` (confirmed **on-main ✓**, existing `McpFormPage.url_input`). Confirmed live: field shows the full URL.
8. Enter a test value in "Client Secret" field.
   - **Verify**: `toolkit-field-client_secret-input-field` (confirmed **on-main ✓**, existing `McpFormPage.client_secret_input_field`). Confirmed live: field accepts the value (masked by default — "Password" toggle is pressed). **Side observation, confirmed live**: once the form is dirty, the canvas header's Discard button transitions from disabled → enabled (`data-testid="mcp-canvas-discard-button"`, confirmed present via DOM probe this session) — added as an intermediate Axis-2 checkpoint, same idiom as ELITEA-2076's own step-6 addition for the sibling Pipeline-canvas case.
9. Click the "Discard" button.
   - **Verify**: `mcp-canvas-discard-button` — **NOT YET IN THE PAGE OBJECT, but the testid itself already exists on `automation/testids`** (added as an `isMcpTestIdScope`-conditional mirror during ELITEA-2081's Toolkit-canvas Discard fix — `ToolkitEditor.jsx`'s single `<BaseEditor>` call site threads `discardButtonTestId={isMcpTestIdScope ? 'mcp-canvas-discard-button' : 'toolkit-canvas-discard-button'}`, confirmed by reading the component source and by a live DOM probe this session: `document.querySelector('[data-testid="mcp-canvas-discard-button"]')` found the button, `disabled: false` once the form was dirty). Clicking it opens a confirmation `Warning` dialog (`mcp-canvas-discard-confirm-modal`, same conditional mirror, confirmed live: `"WarningAre you sure you want to discard changes?CancelDiscard"`) — the SAME `Button.DiscardButton` unconditional confirm-before-`onDiscard` mechanism ELITEA-2076/ELITEA-2081 already document, not new UI logic.
10. Verify the canvas remains open showing empty or default fields (after confirming Discard).
    - **Verify**: confirmed live — clicking `mcp-canvas-discard-confirm-button` (same conditional mirror) closes the modal and `ToolkitEditor.jsx`'s `handleDiscard` (creation-mode branch: `setEditToolDetail(null); setFormikInitialValues({ type: '' })`) reverts the canvas ALL THE WAY back to the type-picker/empty state — NOT merely blank Name/Url/Secret fields on the Remote-MCP form. Confirmed live via DOM probe post-confirm: heading reads `"New MCP"` again, header Discard/Create both `disabled` again, `"Choose the MCP type"` section is back with both Local/Remote panels visible, `toolkit-form-name-input`/`toolkit-field-url-input`/`toolkit-field-client_secret-input-field` are absent from the DOM (the Remote-MCP form itself is unmounted, replaced by the type-picker). This matches the case's own wording ("Canvas clears all entered data" / "canvas remains open showing empty or default fields") — the *default* state of this canvas IS the type-picker, confirmed by this exact same code path already live-verified for the identical Toolkit-creation flow in ELITEA-2081 (same `ToolkitEditor.jsx`, same `handleDiscard`, `isMCP`/`isMcpTestIdScope` only switches testid strings, not behavior).
11. Click X to close the canvas.
    - **Verify**: `mcp-canvas-close-button` (confirmed **on-main ✓**, existing `McpCanvasPage.close_button`). Confirmed live via DOM probe: canvas chrome (`mcp-canvas-close-button`) absent from the DOM post-close; `chat-message-input` visible — only the conversation window displayed.
12. Verify no "MCPS" section appears in the PARTICIPANTS panel and no MCP was created.
    - **Verify**: `ChatPage.is_participants_badge_visible(section="mcp")` returns `False` — confirmed live (`chat-participants-badge-mcp` absent from the DOM at participant count 0, same established idiom `test_pipeline_discard_changes_clears_canvas.py`/`test_close_toolkit_canvas_without_saving.py` already use for their own "no X participant" assertions). **Network-level confirmation**: captured via `page.on("response", ...)` across the whole flow — only `GET /api/v2/elitea_core/tools/prompt_lib/399?...` list-refresh calls fired (from opening the MCPs submenu, twice — once plain, once with `mcp=true`); **zero** `POST` to `/tools/prompt_lib/` at any point, confirmed live this session.

## Expected Results
All 12 steps pass cleanly as specced above. No product defect found — Discard correctly reverts the canvas to the type-picker/empty state and never creates an MCP.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: open conversation | — | Setup | `conversation_id` fixture + `navigate_to_chat()` | asserted |
| 1 Navigate to Chats, open conversation → Conversation view displayed | conversation displayed | step 1 | message input visible | asserted |
| 2 Click + icon, select MCPs → MCPs submenu opens | submenu opens | step 2 | `mcps-menuitem` visible after plus-menu click | asserted |
| 3 Click + Create New MCP → "New MCP" canvas opens with "Choose the MCP type" | canvas opens | step 3 | `mcps-create-new-button` click chain, heading "New MCP" | asserted |
| 4 Verify Local/Remote tabs shown → both visible | both tabs visible | step 4 | `category-filter-tab` × 2 visible | asserted |
| 5 Click Remote tab, select Remote MCP → config canvas opens | config canvas opens | step 5 | `category-filter-tab`("Remote") + `toolkit-type-card-mcp` click, heading "New Remote MCP" | asserted |
| 6 Type "test" in Toolkit Name → Name entered correctly | name entered | step 6 | `toolkit-form-name-input` value == "test" | asserted |
| 7 Type URL → URL entered correctly | url entered | step 7 | `toolkit-field-url-input` value == full URL | asserted |
| 8 Enter test Client Secret → Secret value entered | secret entered | step 8 | `toolkit-field-client_secret-input-field` value set; Discard transitions disabled → enabled | asserted |
| 9 Click Discard → Canvas clears all entered data | data cleared | steps 9-10 | discard-confirm-modal shown + confirmed | asserted |
| 10 Verify canvas remains open showing empty/default fields | canvas open, cleared | step 10 | heading == "New MCP", Discard/Create re-disabled, type-picker visible, form-field testids absent from DOM | asserted |
| 11 Click X to close the canvas → Canvas closes completely | canvas closed | step 11 | canvas chrome testids absent from DOM, message input visible | asserted |
| 12 Verify no "MCPS" section in PARTICIPANTS and no MCP created | no MCP participant | step 12 | `is_participants_badge_visible(section="mcp")` == False + zero create-POST | asserted |
| Expected Final State: "Entered data is cleared after Discard; closing the canvas does not create an MCP. PARTICIPANTS panel shows no MCPS section." | — | steps 10, 12 | field/DOM-state + participants-badge + network assertions | asserted |
| Pass/Fail: "MCP appears in PARTICIPANTS despite discarding" is a FAIL condition | — | step 12 | badge-absence + zero-POST network check | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 8 adds an intermediate assertion that the Discard button transitions from disabled → enabled once the form becomes dirty — *added: gives the reviewer/implementer a clean, independently-verifiable checkpoint before step 9's click, mirroring ELITEA-2076's own step-6 addition for the sibling Pipeline-canvas case and ELITEA-2081's `is_discard_enabled()` check for the sibling Toolkit-canvas case.*
- Step 10 adds a DOM-level assertion that the type-picker (not merely blank form fields) is what "empty or default fields" means for THIS specific canvas variant — *added: the case's own wording is ambiguous between "blank Remote-MCP form" and "reverted to type-picker"; the live product's actual `handleDiscard` behavior (creation-mode branch always resets `editToolDetail` to `null`) settles it as the latter, so the implementation must assert the type-picker state, not merely empty string values on fields that no longer exist in the DOM. This is the SAME code path ELITEA-2081 already live-confirmed for the identical Toolkit-creation flow (`ToolkitEditor.jsx`'s `handleDiscard`, shared unconditionally between Toolkit and MCP creation regardless of `isMCP`).*
- Step 12 asserts the underlying network layer (zero `POST` to `/tools/prompt_lib/` across the whole flow) alongside the DOM-level/participants-badge check — *added: the case's own Pass/Fail criteria explicitly calls out "MCP appears in PARTICIPANTS despite discarding" as a fail condition; a network-level check is a stronger, system-produced signal of "not created" than the DOM/participants-badge check alone. Confirmed live this session: only pre-existing `GET .../tools/prompt_lib/399?...` list-refresh calls fired (from opening the `+` menu's MCPs submenu, once plain and once with `mcp=true`), zero `POST`.*
- A pre-existing, already-tracked React console warning ("Each child in a list should have a unique 'key' prop", `CategorySection.jsx` inside `ToolkitTypeSelector.jsx`) fires during step 5's type-selection render — same root cause already dedup-tracked as issue #656 (ELITEA-1868 analysis) and already filtered by the sibling ELITEA-2085/ELITEA-2081 tests in this same file family. **Not re-filed.** Recommend the implementation filter this specific console message the same way, so it can't mask a genuinely NEW console error appearing alongside it.
- Console/network side-channel checked after every step — confirmed clean of NEW errors/failed requests (the one pre-existing #656 warning aside) across all 12 steps in this session.

## Cleanup
1. Delete the created conversation via `conversation_api.delete_conversation(id)` (handled automatically by the `conversation_id` fixture's teardown).
2. No MCP/toolkit cleanup needed — this flow never persists an MCP (confirmed live via the network-level check in step 12).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `cd EliteaUI && git fetch origin` (this session) then `git grep` on `origin/main` and `origin/automation/testids`, plus a live DOM probe (`page.evaluate`) against the running `automation/testids`-served dev server this session.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| `+` menu → MCPs menuitem | `mcps-menuitem` | on-main ✓ | Existing, reused from ELITEA-2085. |
| `+` menu → MCPs submenu → "+ Create New MCP" | `mcps-create-new-button` | on-main ✓ | Existing, reused from ELITEA-2085. |
| "Local"/"Remote" category tabs | `category-filter-tab` | on-main ✓ | Existing, reused from ELITEA-2085 — disambiguate by `.filter(has_text=...)`. |
| "Remote MCP" type card | `toolkit-type-card-mcp` | on-main ✓ | Existing `McpFormPage.remote_mcp_type_card`, reused from ELITEA-2085. |
| Toolkit Name field | `toolkit-form-name-input` | on-main ✓ | Existing `McpFormPage.name_input`, reused from ELITEA-2085. |
| Url field | `toolkit-field-url-input` | on-main ✓ | Existing `McpFormPage.url_input`, reused from ELITEA-2085. |
| Client Secret field | `toolkit-field-client_secret-input-field` | on-main ✓ | Existing `McpFormPage.client_secret_input_field`, reused from ELITEA-2085. |
| Canvas title | `mcp-canvas-title` | on-`automation/testids` only — awaiting human promotion to `main` | Existing `McpCanvasPage.title` (ELITEA-2085). |
| Canvas X (close) button | `mcp-canvas-close-button` | on-`automation/testids` only — awaiting human promotion to `main` | Existing `McpCanvasPage.close_button` (ELITEA-2085). |
| Canvas Create button | `mcp-canvas-create-button` | on-`automation/testids` only — awaiting human promotion to `main` | Existing `McpCanvasPage.create_button` (ELITEA-2085) — not used by THIS case (never clicked; Discard path only) but present in the DOM throughout. |
| Canvas Discard button | `mcp-canvas-discard-button` | **on-`automation/testids` only** — added during ELITEA-2081's Toolkit-canvas Discard implementation (commit `bc08563f`, `isMcpTestIdScope`-conditional mirror at `ToolkitEditor.jsx`'s single `<BaseEditor>` call site) — awaiting human promotion to `main` | **NOT YET on `McpCanvasPage`** — the testid exists in the DOM (confirmed live this session via `page.evaluate` DOM probe: found, `disabled: false` once the form is dirty) but no `LocatorDescriptor` field references it yet. `testid needed: none` (already exists) — **page-object field needed**: `McpCanvasPage.discard_button`, mirroring `ToolkitCanvasPage.discard_button` exactly (same testid-string shape, different literal value). |
| Discard confirmation modal | `mcp-canvas-discard-confirm-modal` | on-`automation/testids` only (same commit as above) — awaiting human promotion to `main` | **NOT YET on `McpCanvasPage`** — confirmed live via `page.evaluate` (`modalText: "WarningAre you sure you want to discard changes?CancelDiscard"`). Page-object field needed, mirroring `ToolkitCanvasPage.discard_confirm_modal`. |
| Discard-confirm button (inside the modal) | `mcp-canvas-discard-confirm-button` | on-`automation/testids` only (same commit as above) — awaiting human promotion to `main` | **NOT YET on `McpCanvasPage`** — confirmed live via `page.evaluate` (found, clicked successfully, modal closed, form reverted to type-picker). Page-object field needed, mirroring `ToolkitCanvasPage.discard_confirm_button`. |
| PARTICIPANTS mcp badge | `chat-participants-badge-mcp` | on-main ✓ | Existing dynamic `PARTICIPANTS_BADGE` template (`.format("mcp")`), reused from ELITEA-2085. |
| Message input | `chat-message-input` | on-main ✓ | Existing `ChatPage.message_input`. |

## Network Behavior
- `GET /api/v2/elitea_core/tools/prompt_lib/399?sort_by=created_at&sort_order=desc&query=&limit=20&offset=0` → `200 OK` and `GET .../tools/prompt_lib/399?...&mcp=true&...` → `200 OK` — list-refresh calls fired when the `+` menu's MCPs submenu opened (unrelated to this case's own Discard flow).
- **Zero** `POST` to `/tools/prompt_lib/` at any point — confirmed live across the full Name/Url/Client-Secret-typed → Discard → confirm-Discard → close sequence. This is the case's own central concern (Pass/Fail: "MCP appears in PARTICIPANTS despite discarding" is a fail) and is asserted directly in the test.
- No 4xx/5xx observed at any point in this session's execution of this case's own 12 steps.

## Known Defects Found During Exploration
None. One pre-existing, already-tracked non-blocking console warning observed (not re-filed, same as ELITEA-2085/ELITEA-2081):
- **Issue #656** ("[MINOR][ELITEA-1868] Toolkit type-picker: React 'unique key prop' console warning in CategorySection list") — fires identically during this case's step 5 (MCP type-selection render uses the same `ToolkitTypeSelector`/`CategorySection` components as the standalone/Save-variant flow #656 was filed against). Already tracked; recommend filtering the same way the sibling test files in this family already do.

## Blocked Steps
None. All 12 case steps were executed and observed end-to-end live this session.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Reuse, don't rewrite**: compose `ChatPage` (canvas entry point, participants badge) + `McpFormPage` (form internals — Name/Url/Client Secret/type-picker) + the EXISTING `McpCanvasPage` (close/title/create chrome, ELITEA-2085) on the SAME `page` — exactly the same composition ELITEA-2085's test already uses. This case adds only the Discard trio to `McpCanvasPage`.
- **`McpCanvasPage` needs three new fields + two new methods**, mirroring `ToolkitCanvasPage`'s existing ELITEA-2081 `discard_button`/`discard_confirm_modal`/`discard_confirm_button` + `click_discard()`/`confirm_discard()` shape 1:1 (same underlying `Button.DiscardButton`/`BaseModal` components, different call-site testid strings — `mcp-canvas-discard-*` vs `toolkit-canvas-discard-*`). **No `add-data-testid` work is required** — the testids already exist on `automation/testids` (added as the `isMcpTestIdScope`-conditional mirror during ELITEA-2081, confirmed live via DOM probe this session).
- Confirming Discard on a **freshly-selected, never-yet-created** MCP type reverts the WHOLE canvas to the type-picker (not merely blanking the Remote-MCP form fields) — `ToolkitEditor.jsx`'s `handleDiscard` creation-mode branch (`setEditToolDetail(null)`) is unconditional and applies identically whether `isMCP` is true or false. Implementation must assert the type-picker's return, not attempt to read now-unmounted `toolkit-form-name-input`/etc. as empty strings.
- No sanctioned-RED / known-defect handling needed — this case's happy path is fully clean, same as ELITEA-2085.
- Wait strategy: no fixed sleeps — `wait_for(state="visible"/"detached"/"hidden")` throughout, matching `ToolkitCanvasPage.click_discard()`/`confirm_discard()`'s existing idiom. Network-absence assertion via a `page.on("response", ...)` listener collecting any `POST` whose URL contains `/tools/prompt_lib/`, same idiom as ELITEA-2076/ELITEA-2081's own network-absence checks.
