# Test Case: Drag and drop file attachment

## Metadata
- **TMS ID**: ELITEA-2420
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2420_drag-and-drop-file-attachment.md`
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/726
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token)
- **Analyst**: qa-engineer (Sage)
- **Status**: defect-found

## Defect Found

**Bug filed:** #1583 — Support Assistant widget has no drag-and-drop file attachment support

**Summary:** The case explicitly tests drag-and-drop file attachment (`Step 3: Drag the file from the file system and drop it onto the Support Assistant widget chat area`), but the widget has **no drag-drop event handlers implemented**. All drop attempts are rejected with "Drop target did not accept the drop — its dragover handler did not call preventDefault()".

**Root cause:** Verified via live DOM inspection — no `ondrop` / `ondragover` listeners exist on any element in the widget tree (`.elitea-assistant-window`, `.elitea-assistant-messages`, `.elitea-assistant-input-row`, attach button).

**Workaround:** Click-to-browse works perfectly — clicking "Attach file" button opens a file chooser, file selection succeeds, attachment chip appears, Send button enables, and message with attachment submits successfully. The defect is **isolated to drag-drop entry only**; all other attachment functionality (file-type validation, Send-button-enable logic, message submission with attachment) is intact.

**Case classification:** `defect-found` per `test-case-analysis` § Classify findings — a real product bug prevents execution of the case's stated test objective (drag-and-drop). Automation is paused until the drag-drop handlers are implemented.

## Preconditions
- User is authenticated (on localhost: automatic via `VITE_DEV_TOKEN`; on deployed envs: `auth_state` fixture pre-loads via `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`)
- Support Assistant feature is enabled — confirmed live: launcher renders unconditionally on `/chat`
- A test file is created (e.g. `drag-test.txt` with content `"Drag and drop test"`)

## Test Data
### reuse-existing
- `${BASE_URL}` = `http://localhost:5173` (or the project's configured `APP_PREFIX`-aware base URL)
- Page under test: `/chat`
- Test file: `drag-test.txt`, content `"Drag and drop test"` (19 bytes)

## Test Steps (Case Path — BLOCKED at Step 3)

1. Navigate to `${BASE_URL}/chat`
   - **Verify**: page loads, DOM ready
2. Open the Support Assistant widget
   - **Action**: Click the launcher button (`button[aria-label="Support Assistant"]`)
   - **Verify**: Widget opens; title "ELITEA Support" visible
3. **BLOCKED:** Drag the test file from file system and drop it onto the Support Assistant widget chat area
   - **Expected**: File is accepted — attachment chip appears in input area
   - **Actual**: Drop is rejected with error: "Drop target did not accept the drop — its dragover handler did not call preventDefault()"
   - **Root cause**: No drag-drop handlers implemented in the widget
4. Verify the file is accepted — a file preview or attachment chip appears in the input area
   - **Not reached** — Step 3 blocks execution
5. Verify the Send button becomes enabled
   - **Not reached**
6. Click Send — verify the message (with attachment) is submitted and the assistant acknowledges or processes it
   - **Not reached**

## Alternate Path (Click-to-Browse — PASSING, Not Case Intent)

The following alternate path **works** but is **not what the case tests**:

1. Navigate to `/chat` → Open Support Assistant widget
2. Click "Attach file" button (`button[aria-label="Attach file"]`)
   - **Verify**: Native file chooser opens
3. Select `drag-test.txt` via file chooser
   - **Verify**: File chip appears (`generic: drag-test.txt`), Remove button appears (`button: Remove drag-test.txt`)
4. Verify Send button is now enabled (was disabled before file attachment)
   - **Observed**: Send button (`button[aria-label="Send message"]`) enabled ✓
5. Click Send
   - **Observed**: Message with attachment submits; AI responds with "Echo: " (response truncated in this run but submission succeeded)

**This alternate path is documented for implementation reference only** — it proves the attachment flow's backend/UI logic works, isolating the defect to drag-drop entry. Automation of this case should still **implement the drag-drop path once the defect is fixed**, not substitute click-to-browse.

## Coverage Map

**Axis 1 — Case coverage** (ELITEA-2420 steps 1–6):

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to `/chat` | Target page loads successfully | AFS Step 1 | — | defect-found — executed, passed |
| 2 Prepare test file | File created | Preconditions | — | defect-found — setup passed |
| 3 Drag file and drop onto widget | File accepted, drop succeeds | AFS Step 3 | — | **blocked — defect #1583: no drag-drop handlers** |
| 4 Verify file preview/chip appears | Attachment chip visible in input area | AFS Step 4 | — | **not reached — blocked by Step 3** |
| 5 Verify Send button enabled | Send button becomes enabled | AFS Step 5 | — | **not reached — blocked by Step 3** |
| 6 Click Send, verify submission | Message with attachment sends; AI acknowledges | AFS Step 6 | — | **not reached — blocked by Step 3** |

**Axis 2 — Coverage beyond the case:** None — execution stopped at the defect.

## Expected Results (Post-Fix)
- Drag-drop onto widget chat area / input row / messages container / attach button accepts the file
- Attachment chip appears in input area with file name and Remove button
- Send button transitions from disabled to enabled
- Message with attachment submits successfully
- AI response acknowledges receipt (visible in message history)
- No console errors during the flow

## Blocked Steps
**Step 3** — Drag-and-drop file attachment is not implemented. Bug #1583 filed.

All subsequent steps (4, 5, 6) are blocked by this defect.

## Known Defects
- **#1583** — Support Assistant widget has no drag-and-drop file attachment support (dragover handler missing)

## Stable Handles Reference (For Implementation Post-Fix)

**Third-party package exception:** The Support Assistant ships as `@eliteaai/elitea-assistant` (npm package, source in sibling `../elitea_assistant` repo). It is first-party code (we own the repo) but consumed as a package. Per `.agents/workflow.md` § Connected repos, testids for this widget are added in the **elitea_assistant repo's own `automation/testids` integration branch**, not in EliteaUI. The `add-data-testid` skill's local-source wiring (`VITE_ASSISTANT_LOCAL=1` + vite alias) makes them HMR-live on localhost.

**Existing handles (all via `aria-label`, no testids yet — see exception note above):**

| Element | Handle | Provenance | Notes |
|---|---|---|---|
| Launcher button | `button[aria-label="Support Assistant"]` | on main | Opens widget |
| Widget title | `h2:has-text("ELITEA Support")` or `.elitea-assistant-header-title` | on main | Confirms widget open |
| Attach button | `button[aria-label="Attach file"]` | on main | Opens file chooser (click-to-browse) |
| Send button | `button[aria-label="Send message"]` | on main | Submits message; disabled until input |
| Messages container | `.elitea-assistant-messages` | on main | Holds conversation |
| Input row | `.elitea-assistant-input-row` | on main | Contains attach button + input + send button |

**Handles needed (post-fix):**

| Element | Proposed testid | Notes |
|---|---|---|
| Drop target (input row or messages container) | `support-assistant-drop-zone` | Primary drop target; should accept file drops |
| Attachment chip | `support-assistant-attachment-chip` | Shows attached file name |
| Attachment Remove button | `support-assistant-attachment-remove` | Removes file from attachment list |

**Note:** Current implementation uses `aria-label` handles because the Support Assistant is a connected first-party package consumed by EliteaUI, and its testids are added in its own `automation/testids` branch. This is **not** a #579 stop+flag exception (third-party) — it's a connected-repo testid workflow. Future test PRs should still add testids per the connected-repo discipline; the AFS documents the current state only.

## Evidence Paths
- Screenshot (no drag-drop support): `test-results/screenshots/ELITEA-2420-step-03-no-drag-drop-support.png`
- Screenshot (final state): `test-results/screenshots/ELITEA-2420-final-conversation-state.png`
- Screenshot (alternate path — click works): `test-results/screenshots/ELITEA-2420-step-04-file-attached-via-click.md`, `test-results/screenshots/ELITEA-2420-step-06-after-send-click.png`

## Notes
- The case explicitly tests **drag-and-drop** (`Step 3: Drag the file from the file system and drop it`), not click-to-browse
- Click-to-browse (via Attach button) works perfectly and is documented above for reference, but it is **not a substitute** for the case's stated test objective
- Automation should implement the drag-drop path once the defect is fixed, not fall back to click-to-browse
- The defect is isolated to drag-drop entry — all other attachment functionality (file acceptance, chip rendering, Send-button enable, message submission) works correctly
- This AFS documents the **current defective state** and will need no changes once drag-drop handlers are added — the implementer will simply uncomment the blocked steps and drive the real drag-drop flow
