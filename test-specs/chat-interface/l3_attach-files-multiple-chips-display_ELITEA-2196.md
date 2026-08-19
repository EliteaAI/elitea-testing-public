# Test Case: Chat – File Attachments – Upload Multiple Files and Verify They Display Above Message Input Field

## Metadata
- **TMS ID**: ELITEA-2196
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst/Implementer**: test-automation-engineer (agent, combined analyst+implementer slot)
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP against `localhost:5173`. Feature works correctly and matches the case's Objective/Pass criteria. One new testid required (`chat-attachment-remove-chip-{index}` — the ELITEA-2197 AFS reserved `chat-attachment-chip-remove-{index}` for this sibling case, amended during implementation to avoid a prefix collision with an existing shared-caller method; see § Concrete Handles). One case-text clarification (step 2 "begin uploading" — see Coverage Map).
- **Cluster note**: this surface (`FileList.jsx` chip rendering) is already extensively mapped by the merged ELITEA-2195/2197/2200 work (`chat-attachment-chip-{index}` testid, visible/overflow split, counter arithmetic) — this case is the first to assert the chip's own CONTENTS (icon, X button, styling), not just count/name.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (a fresh conversation created via the `conversation_id` fixture satisfies "open conversation" — it does not need pre-existing messages).
- 4 distinct small test files available (see § Test Data — case's own range is "4-5 test files"; 4 is used so all render as VISIBLE chips at the standard wide viewport, keeping this case's own "horizontal row of chips" observable free of the overflow-bucket mechanism that ELITEA-2197 already owns).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Confirmed live: chip background `rgba(255, 255, 255, 0.1)` (a light, low-opacity overlay) composited over the app's own dark canvas (`document.body` computed background `rgb(14, 19, 29)`) — composited relative luminance well under the "dark" threshold. Filename text color `rgb(255, 255, 255)` (pure white) — well over the "light" threshold. Both confirmed identical across all 4 chips this session.

### generate-per-test (created in test setup, no server state — attachments never reach the backend until a message is sent, which this case's steps never do)
- 4 uniquely-named `.txt` files (e.g. `testfile_1.txt` … `testfile_4.txt`), each with distinct trivial content, generated via pytest's `tmp_path` fixture (matches the existing `test_attach_files_10_file_limit_warning` pattern). `.txt` is an allowed extension in this environment (confirmed live, no "invalid file type" toast).

## Test Steps

1. Navigate to the conversation (`ChatPage.navigate_to_chat(conversation_id=...)`).
2. Click the **+** (plus menu) button, then click the **"Attach Files"** menu item to open the native file chooser (`ChatPage.attach_files_via_menu(...)`, reused verbatim from ELITEA-2197/2200's implementation).
   - **Verify**: file chooser opens.
3. Select 4 `.txt` files in a **single** file-chooser action.
   - **Verify**: the 4 files render as chips, all in one horizontal row above the message input, in the same order as selected (`get_visible_attachment_names() == [4 filenames]`, zero overflow — `get_attachment_chip_count() == 4`).
4. Verify each of the 4 chips shows a file-type icon (SVG, the chip's first rendered child) AND the filename text (`get_visible_attachment_names()`, reused).
5. Verify each of the 4 chips has an X (close) button — the newly-testid'd `chat-attachment-chip-remove-{index}` control, visible on every chip. Additionally (Axis 2 addition — a "close button" whose presence-only check would prove nothing about it being a REAL functioning control): click one chip's X button and verify it actually removes that one chip, leaving the other 3 unchanged (mirrors this session's own live manual confirmation).
6. Verify the chips' styling: background is the confirmed live overlay (`rgba(255, 255, 255, 0.1)`) composited over the app's dark canvas — a genuinely DARK rendered background — with the filename text rendered in a genuinely LIGHT color (`rgb(255, 255, 255)`, pure white). Asserted via computed relative luminance (WCAG formula) rather than a hardcoded exact-string match on the raw (pre-composite) `background-color`, since the raw CSS value alone (`rgba(255,255,255,0.1)`) does not by itself read as "dark" — only the COMPOSITED result (chip overlay + page canvas) does, and that is what the case's own plain-language "dark background" describes.

## Expected Results
- All 4 attached files render as chips in a single horizontal row above the composer, immediately, client-side (no network request — see § Network Behavior).
- Each chip: file-type icon + filename visible, an X (close) button present and functional.
- Chip styling: composited dark background, light (white) filename text.
- No console errors during the sequence.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click + icon, select 'Attach Files' | File picker opens | AFS step 2 | `page.expect_file_chooser()` inside `attach_files_via_menu()` | asserted |
| 2 Select 4-5 files to upload | Files begin uploading | AFS step 3 | — | **clarification** — confirmed live (and already documented by the merged ELITEA-2197 AFS's own § Network Behavior): attaching is entirely client-side; **no network request fires** at selection time — files are only uploaded to the backend when a message is actually SENT, which no case in this cluster's steps does. "Begin uploading" does not describe an observable network/progress event in the live product. The real, live, self-consistent observable — the chips render immediately, proving the attach succeeded — is what AFS step 3 asserts (reverse-masking guard: asserting a fabricated "uploading" state that the product never produces would be masking in the reverse direction). |
| 3 Verify files displayed as chips above message input field | Chips visible in horizontal row | AFS step 3 | `get_attachment_chip_count() == 4`, `get_visible_attachment_names()`, all 4 chips share one `y` coordinate (bounding-box row check) | asserted |
| 4 Verify each chip shows file icon and filename | Icon and name visible | AFS step 4 | per-chip: `children[0]` is an `<svg>` (read-only DOM structural check, evaluate-scoped to the already-testid'd chip — no new testid needed, same precedent as the ELITEA-2091 "child icon count scoped under testid'd parent" model-selector check) + filename text via `get_visible_attachment_names()` | asserted |
| 5 Verify each chip has an X (close) button | X button on each chip | AFS step 5 | new testid `chat-attachment-chip-remove-{index}`, `.count()==1` + `.is_visible()` per chip; PLUS a functional click-and-verify-removal check | asserted *(strengthened — presence alone would not distinguish a real control from an inert decoration; verified functional per this session's own live confirmation)* |
| 6 Verify chips have dark background with light text | Styling correct | AFS step 6 | computed relative luminance of (chip background composited over page canvas) vs. filename text color, both read via `.evaluate()` on the testid'd chip | asserted |

### Axis 2 — Analyst/implementer additions
- Step 5's X-button check is extended to a functional click-and-verify (not just presence) — *added: a presence-only check of an unlabelled `onClick` `Box` proves nothing about whether it actually functions; this session's own manual exploration confirmed clicking it correctly removes exactly the targeted chip and leaves siblings unchanged, so the shipped test asserts the same real behavior.*
- Side-channel check: no console errors during the whole sequence — *added: standard per the skill's "check the side channels even when the UI looks fine" rule; none observed live.*
- 4 files (not 5) chosen deliberately so ALL render as visible chips with zero overflow at the standard 1700×1100 viewport — *added: keeps this case's own "chips in a horizontal row" / "each chip has an icon+name+X" observable unambiguous; the visible/overflow split mechanism (and its own "assert the total, not a hardcoded visible count" rule) is already ELITEA-2197's dedicated scope, not re-derived here.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown (`ConversationAPI.delete_conversation`).
- No server-side file/attachment cleanup needed — attachments never get sent to the backend in this flow (no message was sent).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** | pre-existing |
| "Attach Files" menu item (popper) | `[data-testid="chat-attach-menuitem-button"]` | **on-main ✓** (added by ELITEA-2197/2200, `EliteaAI/EliteaUI@38fdb119`) | pre-existing, `ChatPage.attach_files_button` |
| Attachment chip (per file, visible row) | `[data-testid="chat-attachment-chip-{index}"]` | **on-main ✓** (added by ELITEA-2197/2200, `EliteaAI/EliteaUI@38fdb119`) | pre-existing, `ChatPage.CHAT_ATTACHMENT_CHIP` |
| Attachment chip remove (X) icon | `testid needed: chat-attachment-remove-chip-{index}` | **needs-adding — ADDED this session** | `FileList.jsx:98` (`EliteaAI/EliteaUI@7f29c3dc`, `automation/testids`, not yet on `main` — human cherry-pick pending). Reserved by the ELITEA-2197 AFS's own Concrete Handles table as `chat-attachment-chip-remove-{index}` ("not required for ELITEA-2197... only add if a sibling case needs it") — this is that sibling case, but the reserved NAME was amended during implementation (Phase 2 amend-in-PR): `chat-attachment-chip-remove-{index}` shares the `chat-attachment-chip-` prefix with `ChatPage.CHAT_ATTACHMENT_CHIP_PREFIX`, which the existing, merged `get_attachment_chip_count()` (ELITEA-2197) uses — every remove button would be double-counted as an extra chip (live-confirmed: 4 attached files resolved to a count of 8). Renamed to `chat-attachment-remove-chip-{index}`, a distinct prefix, zero collision. |
| Attachment file-type icon (per chip) | scoped structural read: `chip.evaluate("el => el.children[0].tagName")` | n/a — no new testid | Read-only presence check under the already-testid'd chip parent (canon precedent: ELITEA-2091's "child icon count scoped under that one testid'd parent... no new testid needed" for the model-selector's `CheckedIcon`). Not interacted with, only its presence is verified. |
| Chip/text computed style (background, text color) | `chip.evaluate("el => getComputedStyle(el)...")` scoped on the testid'd chip | n/a — computed-style read | Same idiom as `test_delete_confirmation_modal_ui_validation.py`'s `chat.delete_confirm_button.evaluate("el => getComputedStyle(el).backgroundColor")` — a read, not a substitution or an added locator. |

## Network Behavior
- No network request fires for the attach-files flow itself (client-side only; files aren't uploaded until a message is actually sent, which this case's steps never do — same as the already-documented ELITEA-2197 finding).

## Known Defects Found During Exploration
- None. (Step 2's "begin uploading" wording mismatch is a case-text CLARIFICATION, not a functional defect — see Coverage Map row.)

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Page object: extend `automation/pages/chat_page.py`'s `ChatPage` — reuse `attach_files_via_menu()`, `get_attachment_chip_count()`, `get_visible_attachment_names()` verbatim (all pre-existing, ELITEA-2197/2200). Add: `CHAT_ATTACHMENT_CHIP_REMOVE` template constant, `get_attachment_chip_remove_button(index)`, `remove_attachment_chip(index)`, `get_attachment_chip_visual_facts(index)` (returns background/text-color/icon-presence facts via one scoped `.evaluate()` call).
- Viewport: reuse the established wide, fixed viewport (`1700×1100`, ELITEA-2197 precedent) so 4 files render with zero overflow, deterministically.
- Wait strategy: chip render is synchronous/client-side — no network wait needed; `expect(...)` web-first assertions on chip count/visibility are sufficient.
- `conversation_id` fixture (`automation/fixtures/data_fixtures.py:38`) gives a fresh, isolated conversation — reuse it.
