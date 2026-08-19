# Test Case: Chat – Attached files display with filenames, icons, and truncation for long names

## Metadata
- **TMS ID**: ELITEA-2467
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **extend-existing** — targets `automation/tests/ui/chat/test_attach_files_multiple_chips_display.py`
  (`TestAttachFilesMultipleChipsDisplay`, ELITEA-2196), already on this batch's trunk
  `tests/batch-chat-remaining-w13` (not yet on `origin/automation/base`). That module already
  covers this case's steps 1/2/4/5 (attach, icon+filename presence, dark styling, +N count) —
  see Coverage Map. Two gaps remain: (a) step 3 (long-filename truncation) was never exercised
  by the covering test (short filenames only); (b) step 6 — the "+N" indicator's
  click-to-expand behavior — is genuinely new: existing tests (ELITEA-2196/2197) click the
  overflow button only as page-object PLUMBING to read hidden filenames, never assert the
  click-to-expand INTERACTION itself as its own observable.
- **Cluster note**: analysed together with ELITEA-2199 (same live session — shared
  login/navigation/attach discovery, same `FileList.jsx` surface) but written as a **separate
  AFS** — the cases diverge in STEPS: this case's step 6 (+N click-to-expand) has no
  counterpart in ELITEA-2199, whose own step 6 only asks for a count (already covered — see
  ELITEA-2199's own AFS). Unlike ELITEA-2199, this case's step 2 does **not** claim
  "type-appropriate" icons (just "a file icon on the left") — already satisfied by the
  covering test's existing `has_file_icon` presence check, so no icon-genericity gap/clarification
  applies here.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (reuse the covering test's `conversation_id` fixture).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Viewport `1700×1100` (ELITEA-2196/2197 precedent) — confirmed live this session: at this
  width, 4 files render as visible chips before overflow kicks in (matches ELITEA-2196's own
  finding); a 7th file pushes 3 into the "+N" overflow bucket.

### generate-per-test (created in test setup, no server state)
- 1 genuinely long filename (same file as ELITEA-2199's AFS — confirmed live: `scrollWidth`
  731px vs `clientWidth` 116px, genuine CSS-ellipsis truncation).
- 7 distinct small `.txt` files (`extra_file_1.txt`…`extra_file_7.txt` or similar) — confirmed
  live this session at `1700×1100`: attaching 7 files renders exactly 4 visible chips + a
  `"+3"` overflow button (`FileList.jsx`'s `maxItemsToShow` split, same width-driven mechanism
  ELITEA-2197 already documents — never hardcode "4 visible", assert the total).

## Test Steps

1. Navigate to the conversation (reuse `conversation_id` fixture).
2. Attach the 1 long-filename file alone (separate attach action, isolates the truncation
   check from the overflow check's own file count).
   - **Verify**: the chip's filename element genuinely visually truncates (`scrollWidth >
     clientWidth` on the name element, scoped under the chip's testid — identical check to
     ELITEA-2199's AFS step 4; implementer may factor this into one shared helper both new
     test methods call).
3. In a fresh conversation/attach state, attach 7 distinct `.txt` files in a single
   file-chooser action.
   - **Verify**: `chat_attachment_overflow_button` is visible with text `"+3"` (4 visible + 3
     hidden = 7 total — confirmed live this session).
4. Click the `chat_attachment_overflow_button`.
   - **Verify**: the button's `aria-expanded` attribute flips to `"true"` (confirmed live) AND
     a MUI `role="menu"` becomes visible — this IS the "clickable to expand" the case's step 6
     asks for (a click-triggered dropdown menu, not inline scroll — the case's own "expand OR
     scroll" wording is satisfied by either; live product uses expand).
5. Verify the opened menu lists exactly the 3 hidden files' names, via the existing
   `chat-attachment-overflow-item-{index}` testid'd items — in the same order as attached
   (confirmed live: `extra_file_5.txt`, `extra_file_6.txt`, `extra_file_7.txt`, in selection
   order).

## Expected Results
- The long-filename chip's name text is genuinely, visually truncated (`scrollWidth >
  clientWidth`).
- 7 attached files render as 4 visible chips + a `"+3"` overflow indicator.
- Clicking the `"+3"` indicator opens a menu (`aria-expanded="true"`, `role="menu"` visible)
  listing the exact 3 hidden filenames, in order — proving the indicator is a REAL, functioning
  click-to-expand control, not an inert count display.
- No console errors during the sequence.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Chats, attach files of different types | Target page/section loads | — | `ChatPage.navigate_to_chat()` / `attach_files_via_menu()` (`chat_page.py:2685`) | **already-covered** — ELITEA-2196's own test exercises this identical navigation+attach flow (`test_attach_files_multiple_chips_display.py:144-161`). No new assertion needed. |
| 2 Verify each chip shows a file icon on the left and filename next to it | Condition holds | — | `has_file_icon` structural read + `get_visible_attachment_names()`, `test_attach_files_multiple_chips_display.py:183-187` | **already-covered** — ELITEA-2196's own test (Step 4) asserts this exact observable. Unlike ELITEA-2199's case text, THIS case's wording does not claim type-differentiation — plain icon presence is the full ask, already satisfied. No new assertion, no clarification needed here. |
| 3 Verify long filenames are truncated with "..." to fit in the chip | Condition holds | AFS step 2 | `scrollWidth > clientWidth` on the chip's name element, scoped `.evaluate()` | asserted *(gap — same as ELITEA-2199's AFS step 4; the covering test's filenames are all short)* |
| 4 Verify chips have consistent dark background styling, clearly readable | Condition holds | — | composited-luminance check, `chat_page.py:2885` | **already-covered** — ELITEA-2196's own test (Step 6, `test_attach_files_multiple_chips_display.py:207-228`) asserts this exact observable. No new assertion needed. |
| 5 Verify if more than 4-5 files attached a "+N" indicator shows additional count | Condition holds | AFS step 3 | `chat_attachment_overflow_button` text parse (`get_attachment_overflow_count()`, `chat_page.py:2814`) | **already-covered** (mechanism) / asserted (this test's own trigger) — the numeric-count mechanism is Rule-6-equivalent to ELITEA-2197's existing test (`test_attach_files_10_file_limit_warning.py:149-160`), but AFS step 3 still exercises it as a NECESSARY setup precondition for step 4-5's click-to-expand check below (can't test clicking "+N" without first attaching enough files to render it) — included as a live assertion, not a re-derivation of ELITEA-2197's coverage. |
| 6 Verify the "+N" indicator is clickable to expand or scroll to view more files | Condition holds | AFS steps 4-5 | `aria-expanded` attribute + `role="menu"` visibility + `chat-attachment-overflow-item-{index}` text content, all confirmed live this session | asserted *(genuine gap — existing tests, ELITEA-2196's `get_all_attached_file_names()` and ELITEA-2197's own test, click the overflow button only as PLUMBING inside a helper method to read hidden names for a total-count assertion; neither asserts the click→expand interaction itself as an observable — this is the first test to do so)* |

### Axis 2 — Analyst additions
- Side-channel check: no console errors during the whole sequence — *added: standard per the
  skill's "check the side channels even when the UI looks fine" rule.*
- `aria-expanded` toggling to `"true"` is asserted alongside menu visibility — *added: proves
  the control's own accessibility state machine works, not just that a `<ul>` happens to
  appear in the DOM; matches `FileList.jsx`'s own `aria-expanded={open ? 'true' : undefined}`
  wiring (line 117), so this assertion exercises code the component author explicitly wrote
  for exactly this purpose.*
- The 3 hidden filenames are asserted by exact name + order (not just a count of 3) — *added:
  a bare count wouldn't distinguish "the menu opened and shows the right files" from "the menu
  opened and shows garbage" — same "assert the specific names, never a bare count" discipline
  ELITEA-2198's AFS already established for chip removal.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown (`ConversationAPI.delete_conversation`).
- No server-side file/attachment cleanup needed — attachments never reach the backend in this flow.

## Concrete Handles (discovered during exploration)

**Zero new testids required** — every handle this gap needs already exists, confirmed live
against a fresh `git fetch origin` this session:

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Attachment chip (per file, visible row) | `[data-testid="chat-attachment-chip-{index}"]` | **on-main ✓** | pre-existing (`ChatPage.CHAT_ATTACHMENT_CHIP`, `chat_page.py:387`) |
| "+N" overflow button | `chat_attachment_overflow_button` `LocatorDescriptor` | **on-main ✓** | pre-existing (`chat_page.py:407-409`); confirmed live: `aria-expanded` attribute present, flips `undefined` → `"true"` on click |
| Overflow menu item (per hidden file) | `CHAT_ATTACHMENT_OVERFLOW_ITEM` template, `[data-testid="chat-attachment-overflow-item-{index}"]` | **on-main ✓** | pre-existing (`chat_page.py:415-416`); `get_overflow_attachment_names()` (`chat_page.py:2839`) already opens the menu and reads these — reuse for the name-list assertion, extend to ALSO assert `aria-expanded`/menu-visibility as their own checks |
| Chip filename element (layout read) | `chip.evaluate("el => { const s=el.querySelector('span'); return {scrollWidth: s.scrollWidth, clientWidth: s.clientWidth}; }")` | n/a — read-only | Same idiom as ELITEA-2199's AFS — shared helper candidate. |

## Network Behavior
- No network request fires for the attach-files flow itself (client-side only; unchanged from
  ELITEA-2196/2197's already-documented finding).

## Known Defects Found During Exploration
- None. (No case-text mismatch on this case's own wording — see Coverage Map row 2's note on
  why the ELITEA-2199 icon-genericity clarification, issue #1591, does not apply here.)

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Page object: `get_overflow_attachment_names()` (`chat_page.py:2839`) already clicks the
  overflow button and reads item text — extend it (or add a sibling
  `is_attachment_overflow_menu_open()` returning the `aria-expanded` state +
  `role="menu"` visibility) so the NEW test can assert the click-to-expand interaction
  explicitly, not just consume its side effect.
- Implementer's call whether to add a NEW test method to
  `TestAttachFilesMultipleChipsDisplay` (same class ELITEA-2198 already extended) or a new
  top-level function in the same module.
- Reuse `attach_files_via_menu()` / `close_plus_menu_popper()` / `wait_for_attachment_chip_count()`
  verbatim (all pre-existing, ELITEA-2196/2197).
- Viewport: reuse `1700×1100` (module-level constants already defined in the target file); 7
  files at this width confirmed live to yield 4 visible + `"+3"` overflow — deterministic, do
  not hardcode without re-confirming if the module's viewport constants ever change.
- `conversation_id` fixture (`automation/fixtures/data_fixtures.py:38`) — reuse.
- Truncation-check helper is a natural shared extraction with ELITEA-2199's AFS — implementer
  may write ONE helper (e.g. `ChatPage.get_attachment_chip_name_overflow_facts(index)`) both
  new test methods call, rather than duplicating the `.evaluate()` inline twice.
