# Test Case: Chat – File Error States – Verify Unsupported File Format Displays Error Message

## Metadata
- **TMS ID**: ELITEA-2200
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via a `sync_playwright` scratch driver (no Playwright MCP tools were surfaced this dispatch; `.agents/memory/qa-engineer/no_playwright_mcp_use_sync_playwright_script.md`). Message text, dismiss-via-X, and non-attachment all match the case exactly. **One isolated, tail-end defect found and filed**: the banner's visual severity is `info` (blue), not error-level — issue #1121 — does not block the rest of the case; asserted via `expect.soft()` per the sanctioned-RED analysis-time entry (`.agents/testing.md` § Merge gate).
- **Cluster note**: analysed together with ELITEA-2197 (same live session, shared login/navigation/attach-control discovery) but written as a **separate AFS** — the two cases differ in STEPS (unsupported-type+dismiss vs. limit+chip-count), not just data, per test-case-analysis § Execute "merge only when cases differ solely in data."

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (a fresh conversation created via `conversation_id` fixture / `ConversationAPI.create_conversation()` satisfies "open conversation").
- An unsupported file is available — confirmed live with a `.mp4` file (the case's own first example).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Unsupported extension: **`.mp4`** — confirmed live, rejected. (Allowed-extension list is backend-driven/dynamic — see § Automation Hints; do not hardcode it.)

### generate-per-test (created in test setup, cleaned up via file cleanup / no server state)
- One file with an unsupported extension (e.g. `unsupported.mp4`), trivial placeholder content, generated via pytest's `tmp_path` fixture (matches the existing `test_attach_files_button_sends_file_with_message` pattern, `tests/ui/chat/test_chat_interface.py:288-290`).

## Test Steps
1. Navigate to the conversation (`ChatPage.navigate_to_chat(conversation_id=...)`).
2. Click the **+** (plus menu) button, then click the **"Attach Files"** menu item to open the native file chooser.
   - **Verify**: file chooser opens (`page.expect_file_chooser()`).
3. Select the unsupported file (`unsupported.mp4`) via the file chooser.
   - **Verify**: an error/info notification appears (`[data-testid="toast-message"]`, confirmed live: appears within ~1s of selection).
4. Verify banner text is exactly: `Invalid file types detected: unsupported.mp4 (.mp4). Only <dynamic allowed-extensions list> files are allowed.` — assert the **stable prefix/suffix** (`"Invalid file types detected: unsupported.mp4 (.mp4). Only "` … `" files are allowed."`), not the full dynamic middle list (see § Automation Hints).
5. Verify the banner's severity styling — **soft-assert, known defect #1121**: live is `MuiAlert-colorInfo`/`MuiAlert-filledInfo` (blue, info icon), not error-level, despite the case (and its own title/objective) expecting "error". **Implementer amendment (drift caught during automation):** per `.agents/testing.md` § Merge gate's analysis-time sanctioned-RED entry (already cited in this AFS's Metadata line), the assertion is written as the CORRECT/expected behavior — `[data-testid="toast-alert"][data-severity="error"]` — soft-asserted with `# Known defect: #1121`. This is RED-by-design against current live behavior (which returns `data-severity="info"`) and flips green when #1121 ships. (The AFS originally said to assert the current, defective `"info"` value instead — that would have made the test pass today and only go red once the bug is FIXED, backwards from the sanctioned-RED intent; corrected here to match the AFS's own cited policy.)
6. Verify the banner is dismissed by clicking its close (X) icon.
   - Confirmed live: MUI's default `Alert` close button (`aria-label="Close"`, auto-rendered because `Toast.jsx` passes `onClose`); clicking it removes `[data-testid="toast-message"]` from the DOM within ~600ms.
7. Verify the unsupported file was never added to the attachment area.
   - Confirmed live (post-dismiss, so no toast-text substring can false-positive the check): zero matches for `unsupported.mp4` anywhere on the page, and no `"+N"` overflow control appeared (0 attachments total).

## Expected Results
- Toast: `Invalid file types detected: unsupported.mp4 (.mp4). Only <allowed-extensions> files are allowed.`
- Toast severity is currently `info` (blue) — **known defect #1121**, case expects error-level.
- Toast dismissible via its X (aria-label `"Close"`).
- `unsupported.mp4` never appears as an attachment chip; 0 files attached.
- No console errors during the sequence (confirmed live — none observed).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click + icon, Attach Files; select unsupported file type | File selected | AFS steps 2–3 | step 3: file chooser + `set_files` | asserted |
| 2 Verify an error notification/banner appears at top of conversation | Error banner shown | AFS step 3 | step 3: `[data-testid="toast-message"]` visible | asserted *(banner presence — hard assert)* |
| — (implicit in step 2's "error") severity is error-level | red/error styling | AFS step 5 | step 5: `data-severity` attribute | **known defect** — live is `info`, not `error`; filed #1121; soft-assert, see § Known Defects |
| 3 Verify banner text: 'Invalid file types detected:' + filename + supported formats list | Error text contains filename and supported formats | AFS step 4 | step 4: prefix/suffix match | asserted |
| 4 Verify the error banner can be dismissed by clicking X | Banner dismissed | AFS step 6 | step 6: toast absent after click | asserted |
| 5 Verify the unsupported file is NOT added to the attachment area | File not attached | AFS step 7 | step 7: 0 chips, 0 overflow | asserted |

### Axis 2 — Analyst additions
- Step 3 asserts no console errors during the reject sequence — *added: standard side-channel check; none observed.*
- Step 7's "not attached" check is run **after** dismissing the toast (step 6), not before — *added: the toast's own message text contains the substring `unsupported.mp4`, so checking file-presence while the toast is still open would false-positive against the toast text itself rather than a real attachment chip. Confirmed this ordering matters live (see § Automation Hints).*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown (`ConversationAPI.delete_conversation`).
- No server-side file cleanup needed — the file is rejected client-side, never uploaded.

## Concrete Handles (discovered during exploration)

Same attach-control surface as ELITEA-2197 (same live session) — see that AFS's handles table for the plus-menu/attach-menuitem/testid-provenance detail; not repeated here except where this case's own steps diverge.

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** | pre-existing |
| "Attach Files" menu item | `testid needed: chat-attach-menuitem-button` | needs-adding | same as ELITEA-2197's handle — one implementation covers both cases |
| Toast message text | `[data-testid="toast-message"]` | **on-main ✓** (`EliteaUI/src/components/Toast.jsx:66`) | pre-existing |
| Toast severity (color/icon) | `testid needed: toast-alert` with `data-severity={severity}` | needs-adding | same field as ELITEA-2197; here asserted with `data-severity="error"` (the CORRECT/expected value per this case, soft-asserted — known defect #1121, live currently returns `"info"`) rather than `"warning"` (ELITEA-2197's assertion) |
| Toast dismiss (X) button | `testid needed: toast-dismiss-button` | needs-adding | `Toast.jsx`'s `<Alert onClose={onCloseHandler} ...>` auto-renders MUI's default close `IconButton` (no custom `action` prop today) — it currently has **no testid**, only `aria-label="Close"` (MUI default). Add via `Alert`'s `action` prop: `action={<IconButton data-testid="toast-dismiss-button" onClick={onCloseHandler} ...><CloseIcon/></IconButton>}` (replaces the auto-rendered default). Confirmed live: clicking the default (aria-label) close button dismisses the toast correctly — behavior to preserve exactly, just needs a stable handle. |
| Attachment area (for "not attached" check) | reuse `chat-attachment-chip-{index}` / `chat-attachment-overflow-button` (see ELITEA-2197's handles table) | needs-adding | this case only needs to assert **absence** (count == 0) — no new testid beyond what ELITEA-2197 already specs |

## Network Behavior
- No network request fires — client-side-only validation, file is never uploaded.

## Known Defects Found During Exploration
- **[MINOR]** Unsupported-file-type toast renders `severity="info"` (blue, info icon) instead of an error-level severity — filed `EliteaAI/elitea-testing-public#1121`. Root cause (source-confirmed): `AttachmentButton.jsx`'s `displayErrorMessages()` calls `toastInfo(...)` for the invalid-file-types branch, while the sibling 10-file-limit branch in the same function correctly uses `toastWarning(...)`. Message text, dismiss behavior, and non-attachment are all correct — only the visual severity cue is wrong. Automation: `expect.soft()` on the severity assertion (AFS step 5) with `# Known defect: #1121`; hard-assert everything else.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Page object: extend `automation/pages/chat_page.py`'s `ChatPage` — reuse the `open_attach_menuitem()` helper specced in ELITEA-2197's AFS; add `get_toast_severity()` (reads the new `data-severity` attribute) and `dismiss_toast()` (clicks the new `toast-dismiss-button`).
- **Don't hardcode the full allowed-extensions list in the assertion** — it's sourced dynamically from the backend (`useAllowedExtensions()` → `GET` document-loaders query, `EliteaUI/src/hooks/useFileTypes.js`) and could change between environments/deployments. Assert the stable prefix (`"Invalid file types detected: unsupported.mp4 (.mp4). Only "`) and suffix (`" files are allowed."`) via a regex or `startswith`/`endswith` pair, not a full-string equality.
- Wait strategy: after `file_chooser.set_files(...)`, wait for `[data-testid="toast-message"]` to become visible; after clicking dismiss, wait for it to become hidden/detached (confirmed live: ~600ms) rather than a fixed sleep.
- **Ordering matters for the "not attached" check** (step 7): run it AFTER dismissing the toast (step 6), not before — the toast's own text contains the filename substring and will false-positive a naive `page.get_by_text(filename)` check while still open.
- `conversation_id` fixture (`automation/fixtures/data_fixtures.py:38`) gives a fresh, isolated conversation — reuse it.
- Reused live session's login/navigation transit with ELITEA-2197 (same dispatch) — both confirmed the `plus-menu-button` → popper → `AttachmentButton` (`showLabel`) path works identically for both cases.
