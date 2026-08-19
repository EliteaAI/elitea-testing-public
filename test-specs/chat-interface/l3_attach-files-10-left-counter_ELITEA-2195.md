# Test Case: Chat – File Attachments – Verify Attach Files Option Displays 10 Left Counter

## Metadata
- **TMS ID**: ELITEA-2195
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium — same mapping as the sibling attachment cases ELITEA-2197/2200 in this feature area)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst/Implementer**: test-automation-engineer (agent), combined analyst+implementer dispatch (surface pre-mapped by `test-specs/chat-interface/_surface.md`, "File attachments — 10-file limit…" section)
- **Status**: **ready-for-automation** — case executed live end-to-end via Playwright MCP against `/chat` (blank composer, 0 attachments). All 3 case observables (counter text, icon presence, clickable/enabled state) confirmed exactly as expected, zero defects. Not `extend-existing`: the two candidate covering specs (ELITEA-2091's `test_create_new_conversation_team_project_attachments_and_llm.py`, ELITEA-2197's `test_attach_files_10_file_limit_warning.py`) both touch the "10 left" text as an *intermediate* assertion inside much larger, unrelated flows (LLM switch + drag-drop; 11-file-limit warning) and neither asserts the icon or the enabled/clickable state at all — bolting this case's 3 narrow, independent assertions onto either as a "new test() in an existing describe" would not read as one coherent scenario. A small, dedicated, fast spec matches the case's own narrow scope most faithfully.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (a fresh conversation via the `conversation_id` fixture satisfies this — the attachment counter is pure client-side composer state, seeded to 0 on every mount, so any freshly-loaded conversation qualifies; no need for a "genuinely blank" conversation guard here — that guard concerns SERVER-SIDE message/participant state, not this client-local counter).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- File-count limit: **10** (`ATTACHMENT_LIMITS.MAX_ATTACHMENTS`, `EliteaUI/src/common/constants.js:1084` — same constant ELITEA-2197 confirmed live; this case observes the counter's *initial* value, `MAX_ATTACHMENTS - 0 = 10`, no files are ever attached).

## Test Steps

1. Navigate to Chats and open a conversation (`ChatPage.navigate_to_chat(conversation_id=...)`).
2. Click the **+** (plus menu) button at the bottom-left of the composer.
   - **Verify**: the popup menu opens (`ChatPage.plus_menu_button` -> popper visible).
3. Locate the **"Attach Files"** menu item.
   - **Verify**: it displays **"10 left"** text — confirmed live via `textContent` = `"Attach Files10 left"` (no attachments yet, fresh composer).
4. Verify the option has a paperclip/attachment icon.
   - **Verify**: 1 `<svg>` icon rendered inside the menu item — confirmed live (`AttachIcon`, `@/assets/attach-icon.svg?react`, first-party asset, always rendered regardless of attachment count).
5. Verify the option is clickable.
   - **Verify**: the button's `disabled` attribute is `false` — confirmed live. (`isDisabled` in `AttachmentButton.jsx` is only `true` at max capacity/processing/loading — none apply to a fresh composer.)

## Expected Results
- "Attach Files" menu item text includes "10 left".
- A paperclip/attachment icon (1 `<svg>`) is rendered inside the menu item.
- The menu item is enabled (not `disabled`).
- No console errors during the sequence.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Chats, open any conversation | Conversation open | AFS step 1 | `navigate_to_chat()` completes, composer visible | asserted (setup) |
| 2 Click + icon | Popup menu opens | AFS step 2 | step 2: `attach_files_button` (popper item) becomes visible | asserted |
| 3 Locate 'Attach Files' option | Displays '10 left' on the right | AFS step 3 | step 3: `"10 left" in attach_files_button.text_content()` | asserted |
| 4 Verify paperclip/attachment icon on the left | Icon visible | AFS step 4 | step 4: `attach_files_menuitem_icon` (new testid) visible, count == 1 | asserted |
| 5 Verify the option is clickable | Option clickable | AFS step 5 | step 5: `attach_files_button.is_enabled()` is True | asserted |

### Axis 2 — Analyst additions
- Side-channel check — no console/JS errors during the sequence, per the skill's standard side-channel rule. *added.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown. No attachments are ever sent (no message sent, no upload network call) — nothing else to clean up.

## Concrete Handles (discovered/confirmed during exploration)

| Element | Locator | Provenance | Notes |
|---|---|---|---|
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** | pre-existing; `ChatPage.plus_menu_button` |
| "Attach Files" menu item (showLabel popper instance) | `[data-testid="chat-attach-menuitem-button"]` | **on-main ✓** (confirmed live `git grep` against `origin/main` prior sessions, ELITEA-2197 closure) | pre-existing `ChatPage.attach_files_button` — reused verbatim, no new work. `.text_content()` == `"Attach Files10 left"` on a fresh composer (established pattern, `test_create_new_conversation_team_project_attachments_and_llm.py`). |
| Attach icon (paperclip, `AttachIcon` asset) | `testid needed: chat-attach-menuitem-icon` | needs-adding | `AttachmentButton.jsx`'s icon `Box` (`component={AttachIcon}`) had NO testid — first-party app JSX (`@/assets/attach-icon.svg?react`), not third-party-library-internal chrome, so per `.agents/testing.md` § Locator policy a real testid is genuinely placeable (same reasoning as the precedent `delete_confirm_title_icon`, `chat_page.py:4506-4533`) rather than a #579 scoped-raw-handle exception. Threaded via the SAME `testId` prop the button itself already uses (`data-testid={testId ? \`${testId}-icon\` : undefined}`) — present only at this popper call site, `undefined` at the button's other 3 render sites (hidden instance, `UserMessage.jsx`, `NewChatInput.jsx`), matching the existing same-element-conditional-pair shape #277 already uses for the button's own testid. |

## Network Behavior
- No network request fires — the counter, icon, and enabled state are pure client-side composer render output; no attachment is ever selected/uploaded.

## Known Defects Found During Exploration
- None. All 3 observables confirmed live exactly as the case expects.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Page object: `ChatPage` — reuse `plus_menu_button`, `attach_files_button` (both pre-existing), add `attach_files_menuitem_icon` (new `LocatorDescriptor`, testid `chat-attach-menuitem-icon`). `open_attach_menuitem()` (pre-existing) already implements steps 1-2's click sequence.
- No new page-object method strictly required beyond the new locator field — the test reads `.text_content()` / `.count()` / `.is_enabled()` directly off existing/new `LocatorDescriptor` fields, matching the established pattern in `test_create_new_conversation_team_project_attachments_and_llm.py` (`attach_text = chat.attach_files_button.text_content()`).
- `conversation_id` fixture gives a fresh conversation; no Team-project switch needed (Private/default project suffices — this case doesn't touch "Invite Users", which is the only project-conditional menu item).
