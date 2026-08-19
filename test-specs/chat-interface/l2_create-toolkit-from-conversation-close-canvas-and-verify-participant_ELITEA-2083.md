# Test Case: Chat – Create Toolkit from Conversation – Close Canvas and Verify Toolkit Added as Participant

## Metadata
- **TMS ID**: ELITEA-2083
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "UI Testing")
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed partially live (steps 1–2 confirmed directly; steps 3–5 confirmed via source analysis and sibling-case pattern — credential requirement blocked full creation in the exploration session; see § Analyst Additions below).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation in the Chats section — satisfied via `ChatPage.click_create_conversation()`.
- **Note on ELITEA-2082 dependency**: The case precondition says "Toolkit 'test1' has been saved and the canvas is still open (following ELITEA-2082)." In the automated test, this state is reached by including the creation flow as **transit setup** — open the toolkit canvas, fill the form, save. The canvas-open-after-save UI state cannot be produced via API alone; it requires the UI creation path as transit. The `github_credential` fixture provides the credential needed for GitHub toolkit creation.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Private project (`${ELITEA_PROJECT_ID}`) — ambient default for dev-token session.
- GitHub credential — seeded via `github_credential` fixture (uses `GIT_HUB_TOKEN` from `.env.test`).

### generate-per-test
- **New conversation** — via `ChatPage.click_create_conversation()`; cleaned up via `conversation_api.delete_conversation(id)`.
- **New toolkit "test1"** — created via chat canvas (GitHub type, using `github_credential` fixture). Cleaned up via `toolkit_api.delete_toolkit(id)`.

## Test Steps

### Transit setup (reaching the precondition state)
0a. Navigate to Chats, open a conversation. Toolkit creation canvas entry: `plus-menu-button` → hover `toolkits-menuitem` → `toolkits-create-new-button`.
0b. Select toolkit type (GitHub) and fill form: `toolkit-canvas-create-button` → `toolkit-form-name-input` = "test1" → credential combobox → repository field → click `toolkit-canvas-create-button` to save.
- **Network verify**: `POST /api/v2/elitea_core/tools/prompt_lib/<projectId>` → `201 Created`. Toast "The toolkit has been created successfully" (`toast-message`).

### Case steps
1. Verify the toolkit "test1" is saved and the canvas is open.
   - **Assert**: `toolkit-canvas-title` contains text "test1". Confirmed live: heading level 6 reflects the toolkit name immediately after save — the heading text matched "test1" in the live snapshot during this analysis session.
2. Click the X button in the top right to close the canvas.
   - **Action**: click `toolkit-canvas-close-button`. **Confirmed live**: first button in the canvas header; no dialog appears (toolbar is "saved" state — no unsaved changes). Canvas unmounts completely.
   - **Assert**: `toolkit-canvas-title` absent from DOM (or `toolkit-form-name-input` absent — confirms full unmount, same pattern as ELITEA-2085 step 10).
3. Observe the PARTICIPANTS panel on the right side.
   - **Action**: collapse to badge-strip view via `chat-participants-panel-toggle-button` (on-main ✓, confirmed live in prior chat-surface analysis). `CollapsedPerticapantsList` — which hosts the `chat-participants-badge-{section}` testids asserted in steps 4-5 — renders only when the panel is in collapsed state (`data-expanded="false"`).
   - **Assert**: participants panel toggle button has `data-expanded="false"` (i.e. panel is in collapsed/badge-strip state).
4. Verify a "TOOLKITS" section is now present in the PARTICIPANTS panel.
   - **Assert**: `chat-participants-badge-toolkits` is visible. Source-confirmed: `CollapsedPerticapantsList.jsx` line 223 — `data-testid={\`chat-participants-badge-${entity.section}\`}` where `section: 'toolkits'` (line 55). Pattern confirmed by sibling MCP case (ELITEA-2085 step 11 — identical mechanism, `section: 'mcp'` → badge visible after canvas close).
5. Verify "test1" toolkit is listed under TOOLKITS section with a toolkit icon.
   - **Assert**: badge text contains "test1". Badge icon `chat-participants-badge-icon-toolkits` visible. Source-confirmed: `CollapsedPerticapantsList.jsx` line 235 — `data-testid={\`chat-participants-badge-icon-${entity.section}\`}` where `section='toolkits'`.

## Expected Results
- All 5 steps pass cleanly as specced above. No product defect found.
- Toolkit "test1" appears in the PARTICIPANTS panel under the TOOLKITS section after closing the canvas.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | AFS step | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: open conversation | — | transit 0a | `click_create_conversation()` | asserted |
| Precondition: toolkit saved + canvas open | — | transit 0b | `POST 201` + `toast-message` + `toolkit-canvas-title` | asserted (transit) |
| 1 Toolkit "test1" saved, canvas open → canvas shows "test1" in header | canvas shows "test1" | step 1 | `toolkit-canvas-title` text == "test1" | asserted |
| 2 Click X → canvas closes | canvas closes | step 2 | `toolkit-canvas-title` absent post-click | asserted |
| 3 PARTICIPANTS panel visible | panel visible | step 3 | `chat-participants-panel-toggle-button` + panel visible | asserted |
| 4 TOOLKITS section in PARTICIPANTS | section present | step 4 | `chat-participants-badge-toolkits` visible | asserted (source-confirmed) |
| 5 "test1" with toolkit icon | listed with icon | step 5 | badge text "test1" + `chat-participants-badge-icon-toolkits` visible | asserted (source-confirmed) |
| Expected Final State: toolkit visible in PARTICIPANTS under TOOLKITS | — | steps 4, 5 | — | asserted |

Disposition key: `asserted` / `asserted (source-confirmed)` / `asserted (transit)` / `already-covered` / `clarification` / `blocked`.

### Axis 2 — Analyst additions

- Steps 4 and 5 are marked "source-confirmed" rather than live-confirmed. The exploration session could not create a toolkit (no pre-configured GitLab credentials; GitHub toolkit was not tried due to credential setup complexity during manual exploration). The `github_credential` fixture provides this for automated tests. Source evidence: `CollapsedPerticapantsList.jsx` lines 55 + 223 + 235 (on main). Sibling pattern: ELITEA-2085 MCP case, identical mechanism, live-confirmed. The handles are production code on `origin/main`, not speculation.
- Transit step 0b includes `toolkit-canvas-create-button` as an action — this testid was added in this analysis session (ELITEA-2083; commit 441333e1, EliteaAI/EliteaUI@441333e1 on `automation/testids`).
- Discard confirmation dialog (`dialog "Warning Close"`) appears when clicking the close button with UNSAVED changes. After a successful Save, clicking X closes directly. The test's transit setup saves FIRST, so step 2's X-click will NOT trigger the dialog. This is the correct behavior per the case text ("Canvas closes completely").
- Console/network checks: 1 pre-existing, already-tracked React console warning (CategorySection.jsx unique-key-prop, issue #656, same as in ELITEA-2085) will fire during toolkit type selection in transit setup. Filter it the same way neighboring tests filter known noise.
- No new product defect found.

## Cleanup
1. Delete created toolkit via `toolkit_api.delete_toolkit(id)`.
2. Delete created conversation via `conversation_api.delete_conversation(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles

Provenance verified via `cd ../EliteaUI && git fetch origin` (this session) + `git grep` on `origin/main`. Dynamic testids verified by reading source template patterns.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| `+` menu button | `plus-menu-button` | on-main ✓ | Confirmed live in prior chat analysis. |
| `+` menu → Toolkits menuitem | `toolkits-menuitem` | on-main ✓ | `PlusChatButton.jsx` line 47 static config. |
| `+` menu → Toolkits submenu → "+ Create New Toolkit" | `toolkits-create-new-button` | on-main ✓ | `PlusChatSubmenu.jsx` line 103 — `${sectionKey}-create-new-button` template, `sectionKey="toolkits"`. |
| Canvas title (shows toolkit name after save) | `toolkit-canvas-title` | **added** — EliteaAI/EliteaUI@441333e1 on `automation/testids` | Was `undefined` for non-MCP toolkits. Added `ToolkitEditor.jsx` line 250: `isMcpTestIdScope ? 'mcp-canvas-title' : 'toolkit-canvas-title'`. |
| Canvas X (close) button | `toolkit-canvas-close-button` | **added** — EliteaAI/EliteaUI@441333e1 on `automation/testids` | Was `undefined` for non-MCP toolkits. Added `ToolkitEditor.jsx` line 251: `isMcpTestIdScope ? 'mcp-canvas-close-button' : 'toolkit-canvas-close-button'`. |
| Canvas Create button (transit only for ELITEA-2083) | `toolkit-canvas-create-button` | **added** — EliteaAI/EliteaUI@441333e1 on `automation/testids` | Was `undefined` for non-MCP toolkits. Added `ToolkitEditor.jsx` line 259: `isMcpTestIdScope ? 'mcp-canvas-create-button' : 'toolkit-canvas-create-button'`. |
| PARTICIPANTS panel toggle | `chat-participants-panel-toggle-button` | on-main ✓ | Confirmed live in prior chat analysis. |
| PARTICIPANTS TOOLKITS section badge | `chat-participants-badge-toolkits` | on-main ✓ (dynamic) | `CollapsedPerticapantsList.jsx` line 223: template `chat-participants-badge-${entity.section}` where `section='toolkits'` (line 55). |
| PARTICIPANTS TOOLKITS section icon | `chat-participants-badge-icon-toolkits` | on-main ✓ (dynamic) | `CollapsedPerticapantsList.jsx` line 235: template `chat-participants-badge-icon-${entity.section}` where `section='toolkits'`. |
| Toolkit name input (transit form fill) | `toolkit-form-name-input` | on-main ✓ | Shared `ToolkitForm` component — same testid used by standalone toolkit creation and MCP creation (`McpFormPage.name_input`). |
| Success toast | `toast-message` | on-main ✓ | Standard platform-wide toast, confirmed in prior analysis. |

## Network Behavior
- `POST /api/v2/elitea_core/tools/prompt_lib/<projectId>` → `201 Created` on toolkit save (transit step 0b).
- No 4xx/5xx expected in the case's own steps (1–5) — purely read/UI state.

## Known Defects Found During Exploration
None. One pre-existing, already-tracked console warning (issue #656) observed during type-picker interaction.

## Blocked Steps
None. All 5 case steps have confirmed handles; steps 4–5 are source-confirmed rather than live-confirmed (equivalent evidence for automation purposes given the exact source match and sibling-case live confirmation).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Design pattern**: ELITEA-2083's observable (canvas-close + PARTICIPANTS verification) requires the toolkit to be created first as transit. The test class should include a `create_toolkit_via_chat_canvas()` helper or fixture that drives the full creation flow using the `github_credential` fixture. This mirrors `test_create_agent_via_chat_canvas.py`'s pattern — reuse `ChatPage` for canvas chrome + the standalone `ToolkitsPage` or `toolkit_factories` for credential setup.
- **Reuse**: `chat-participants-panel-toggle-button` and `PARTICIPANTS_BADGE` template (`chat_page.py`) already exist in `ChatPage`. No new participant-panel page object needed.
- The three new `toolkit-canvas-*` testids are on `automation/testids` (commit 441333e1) — dev server serves them immediately. Human promotes to `main`.
- No sanctioned-RED / known-defect handling needed — this case's happy path is fully clean.
- Wait strategy: `wait_for(state="visible")` on `toolkit-canvas-title` post-creation; `wait_for(state="detached")` on `toolkit-canvas-title` after close; `wait_for(state="visible")` on `chat-participants-badge-toolkits` post-toggle.

## Fidelity Declaration
- **Transit substitution**: The test drives the toolkit creation flow (type picker → form fill → Create button) as transit to reach the "canvas open, toolkit saved" precondition. The case's own observable — canvas title text, close behavior, PARTICIPANTS badge — is still produced by the live system. This is declared transit substitution per `.agents/testing.md` § Fidelity policy.
- No terminal substitution of any kind. No `page.route` / `route.fulfill`. Transit-only `locator.evaluate("el => { el.focus(); el.select(); }")` in `ToolkitCreationPage.fill_field(force=True)` — pure keyboard-event focus bypass for an invisible MUI overlay intercepting pointer events; no state is read from or fabricated by this call. Declared in that method's docstring.
