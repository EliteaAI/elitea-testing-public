# Test Case: Chat – File Attachments – Upload Maximum 10 Files and Verify Limit Warning

## Metadata
- **TMS ID**: ELITEA-2197
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via a `sync_playwright` scratch driver (no Playwright MCP tools were surfaced this dispatch; `.agents/memory/qa-engineer/no_playwright_mcp_use_sync_playwright_script.md`). Feature works correctly and matches the case's Objective/Pass-criteria, but the case's own **literal step sequence cannot be reproduced as written** — filed as a clarification, issue #1122 (see Coverage Map + § Test Steps below for the corrected, live-confirmed sequence). Zero pre-existing testids on the surfaces this case touches (attach control inside the "+" popper, the attachment-chip list, the toast severity) — substantial `add-data-testid` work is required (see § Concrete Handles).
- **Cluster note**: analysed together with ELITEA-2200 (same live session, shared login/navigation/attach-control discovery) but written as a **separate AFS** — the two cases differ in STEPS (limit+chip-count vs. unsupported-type+dismiss), not just data, per test-case-analysis § Execute "merge only when cases differ solely in data."

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (a fresh conversation created via `conversation_id` fixture / `ConversationAPI.create_conversation()` satisfies "open conversation" — it does not need pre-existing messages).
- 11 distinct small text files available (see § Test Data) — the case's "11+ test files".

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- File-count limit: **10** (`ATTACHMENT_LIMITS.MAX_ATTACHMENTS`, `EliteaUI/src/common/constants.js:1084` — confirmed live, not assumed from the case's Test Data table alone).
- Exact warning text (confirmed live, verbatim, byte-for-byte match to the case's Test Data row): `You've reached the 10-file limit. Only the first 10 will be processed.`

### generate-per-test (created in test setup, cleaned up via file cleanup / no server state beyond the conversation)
- 11 uniquely-named `.txt` files (e.g. `testfile_1.txt` … `testfile_11.txt`), each with distinct trivial content, generated via pytest's `tmp_path` fixture (matches the existing `test_attach_files_button_sends_file_with_message` pattern, `tests/ui/chat/test_chat_interface.py:288-290`). `.txt` is an allowed extension in this environment — confirmed live (all 10 kept files attached with zero "invalid file type" warnings).

## Test Steps

**Case text described a two-action sequence ("attach 10, then separately attempt an 11th") that is NOT reproducible live** — see Coverage Map row for step 2 and issue #1122. The corrected, live-confirmed sequence below reaches the identical observable state (warning shown, exactly 10 attached, 11th excluded) that the case's Objective and Pass/Fail criteria require.

1. Navigate to the conversation (`ChatPage.navigate_to_chat(conversation_id=...)`).
2. Click the **+** (plus menu) button, then click the **"Attach Files"** menu item to open the native file chooser.
   - **Verify**: file chooser opens (`page.expect_file_chooser()`).
3. Select **all 11** `.txt` files in a **single** file-chooser action (`file_chooser.set_files([...11 paths...])`) — this is the corrected trigger; see Coverage Map.
   - **Verify**: a warning toast appears (`[data-testid="toast-message"]`, confirmed live: appears within ~1s of selection, no manual wait beyond a network/DOM-settle wait needed).
4. Verify warning text is exactly: `You've reached the 10-file limit. Only the first 10 will be processed.`
5. Verify warning styling — MUI `Alert` `severity="warning"` (amber/orange, warning-triangle icon). Confirmed live: `class="... MuiAlert-colorWarning MuiAlert-filledWarning MuiAlert-filled ..."` on the toast's `Alert` root, plus 2 SVG icons (triangle indicator + close icon).
6. Verify exactly 10 files remain attached and the 11th (`testfile_11.txt`, the last file in the selection — files are kept in selection order, `fileArray.splice(allowedCount)` keeps indices 0–9) is **not** attached.
   - Confirmed live: 4 chips directly visible (`testfile_1.txt`…`testfile_4.txt`) + a `"+6"` overflow control = 10 total. The visible/overflow split is **container-width-dependent** (`FileList.jsx`'s `useGetComponentWidth` + `Math.floor(availableWidth / 208)`) — do not hardcode "4 visible"; assert the **sum** (visible chip count + overflow number, parsed from the `"+N"` control's text) equals 10, and assert `testfile_11.txt` does not appear anywhere (neither as a visible chip nor inside the opened overflow menu).

## Expected Results
- Warning toast: `You've reached the 10-file limit. Only the first 10 will be processed.` — `severity="warning"` (amber/orange, warning-triangle icon).
- Exactly 10 files attached (first 10 in selection order); the 11th excluded.
- No console errors during the sequence (confirmed live — none observed).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click +, select 'Attach Files', upload 10 files | All 10 files shown as chips | AFS step 3 (partial — see step 2/3 clarification below) | step 6: total-attached-count == 10 | asserted *(re-sequenced)* |
| 2 Attempt to attach an 11th file via + icon > Attach Files | File picker opens | — | — | **clarification** — live product **disables** the "Attach Files" control once exactly 10 files are attached (`isAtMaxCapacity` → `disabled`); a disabled MUI button never fires `onClick`, so no file picker opens and no warning fires via this literal two-action path. Filed: issue #1122. The warning is only reachable by selecting more files than remaining capacity **within one file-chooser action** — reproduced in AFS steps 2–3 instead. |
| 3 Select one more file | Warning notification appears at top of conversation | AFS step 3 | step 3: `[data-testid="toast-message"]` visible | asserted *(re-sequenced — the "one more file" is folded into the single 11-file selection, since the literal two-step version is unreachable per the row above)* |
| 4 Verify warning text | Warning text correct | AFS step 4 | step 4: exact string match | asserted |
| 5 Verify yellow/orange background with warning triangle | Warning styled correctly | AFS step 5 | step 5: `MuiAlert-colorWarning`/`MuiAlert-filledWarning` class + 2 SVG icons | asserted |
| 6 Verify only 10 files remain attached | 11th file not added | AFS step 6 | step 6: visible-chip-count + overflow-count == 10, and `testfile_11.txt` absent | asserted |

### Axis 2 — Analyst additions
- Step 3 asserts no console errors during the warning sequence — *added: standard side-channel check per the skill's "check the side channels even when the UI looks fine" rule; none observed.*
- Confirmed `.txt` is an allowed extension in this environment (no invalid-type toast fired for any of the 10 kept files) — *added: rules out a confound between the count-limit warning and a type-validation warning, since both render through the same `[data-testid="toast-message"]` element.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown (`ConversationAPI.delete_conversation`).
- No server-side file/attachment cleanup needed — attachments never get sent to the backend in this flow (no message was sent).

## Concrete Handles (discovered during exploration)

**Everything on this surface is currently testid-less** (confirmed via `git grep` — `plus-menu-button` and `toast-message` are pre-existing/on-`main`; nothing else below exists in `EliteaAI/EliteaUI` source at all). Per `.agents/testing.md` § Locator policy, missing testid ⇒ `add-data-testid` work, not a rung-down to role/text handles.

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** (`EliteaUI/src/[fsd]/features/chat/ui/chat-button/PlusChatButton.jsx`) | pre-existing |
| "Attach Files" menu item (the one inside the open popper, `showLabel` instance) | `testid needed: chat-attach-menuitem-button` | needs-adding | `PlusChatButton.jsx:373` renders a SECOND `AttachmentButton` instance (`showLabel`, no `ref`) inside the `MenuList` — this is the one the case's own steps touch. `AttachmentButton` is a **shared component** (also used by `UserMessage.jsx`, `NewChatInput.jsx`, and a third *hidden* (`width:0,height:0,pointerEvents:none`) instance at `PlusChatButton.jsx:336`) — per `.agents/testing.md` § Locator policy "shared components never hardcode feature-scoped testids", thread a `testId` prop through `AttachmentButton`'s `<IconButton>` and set it **only at this call site** (`PlusChatButton.jsx:373`'s `<AttachmentButton showLabel testId="chat-attach-menuitem-button" .../>`) — do not touch the hidden instance (this case's test never calls it) or the `UserMessage.jsx`/`NewChatInput.jsx` instances (other cases' scope). |
| Existing `attach_files_button` `LocatorDescriptor` (`automation/pages/chat_page.py:55-58`) | — | **dead/stale testid** — `testid="chat-attach-button"` does not exist anywhere in `EliteaUI/src` (confirmed via `git grep` against both `origin/main` and `origin/automation/testids`: zero hits). Field currently only "works" via its `fallback=` (forbidden in new code). Recommend re-pointing this EXISTING field at the new `chat-attach-menuitem-button` testid above (fixing dead tech debt this case's own test now correctly exercises) rather than adding a duplicate field — implementer's call. |
| Toast message text | `[data-testid="toast-message"]` | **on-main ✓** (`EliteaUI/src/components/Toast.jsx:66`) | pre-existing; text content only — no severity info on this node |
| Toast severity (color/icon) | `testid needed: toast-alert` with `data-severity={severity}` | needs-adding | `Toast.jsx`'s `<Alert severity={severity} ...>` has no testid at all today. Add `data-testid="toast-alert"` **and** `data-severity={severity}` on the `<Alert>` (line ~59) — this follows the project's own "testid = stable identity, state via `data-*`" convention (`.agents/testing.md` § Locator policy) exactly, since `severity` is a value that changes per-toast on the SAME component. Locate via `[data-testid="toast-alert"][data-severity="warning"]` for this case. |
| Attachment chip (per file, visible row) | `testid needed: chat-attachment-chip-{index}` (dynamic, UPPER_CASE class-constant template) | needs-adding | `FileList.jsx:72-104` (`EliteaUI/src/components/Chat/FileList.jsx`) — zero testids anywhere in this component today. Add on the per-item `Box` (line 73), keyed by array index (stable within one render/attach sequence). |
| Attachment chip remove (X) icon | `testid needed: chat-attachment-chip-remove-{index}` (dynamic) | needs-adding | `FileList.jsx:97-102`, the `onClickRemove(index)` handler's `Box`. Not exercised by THIS case (case never removes a chip) — only add if a sibling case needs it; not required for ELITEA-2197. |
| Overflow "+N" button | `testid needed: chat-attachment-overflow-button` | needs-adding | `FileList.jsx:108-119`, static (one instance, only rendered when `hiddenAttachments.length > 0`). Text content is `` `+${hiddenAttachments.length}` `` — this case parses that number as part of its total-count assertion (step 6). |
| Overflow menu item (per hidden file) | `testid needed: chat-attachment-overflow-item-{index}` (dynamic) | needs-adding | `FileList.jsx:142-173`. MUI `Menu` here is **not** `keepMounted` — items only exist in the DOM while the overflow menu is open; the count-of-10 assertion must open it first if it needs to inspect names inside (not required for step 6's numeric-total approach, only if asserting the *specific* 6 filenames in the overflow). |

## Network Behavior
- No network request fires for the attach-files flow itself (client-side only validation; files aren't uploaded until a message is actually sent, which this case's steps never do).

## Known Defects Found During Exploration
- None found. (The interaction-sequence mismatch is a case-text/live-product CLARIFICATION — issue #1122 — not a functional defect; see Coverage Map row for case step 2.)

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Page object: extend `automation/pages/chat_page.py`'s `ChatPage` — add `open_attach_menuitem()` (click `plus-menu-button`, then the new `chat-attach-menuitem-button`), and either a new `FileListComponent` under `automation/components/` or methods directly on `ChatPage` for the chip/overflow assertions (`get_attached_file_names()`, `get_attached_file_count()` = visible-chip-count + parsed overflow number).
- Viewport: use a wide, fixed viewport (≥ 1700px wide — confirmed live at `1700x1100`) so `FileList.jsx`'s width-driven `maxItemsToShow` is deterministic across CI runs; still assert the **total** count (visible + overflow), never a hardcoded "N visible" number, since the split itself is layout-sensitive.
- Wait strategy: after `file_chooser.set_files(...)`, wait for `[data-testid="toast-message"]` to become visible (confirmed live: appears within ~1s) rather than a fixed sleep.
- `conversation_id` fixture (`automation/fixtures/data_fixtures.py:38`) gives a fresh, isolated conversation — reuse it; no need for `ChatPage.switch_project()` (Private/default project is sufficient, unlike the Team-project cases in this same feature area).
- Reused live session's login/navigation transit with ELITEA-2200 (same dispatch) — both confirmed the `plus-menu-button` → popper → `AttachmentButton` (`showLabel`) path works identically for both cases.
