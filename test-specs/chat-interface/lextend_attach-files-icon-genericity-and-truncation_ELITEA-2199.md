# Test Case: Chat – Attachment Preview – Verify Attached Files Display with Filenames and Icons

## Metadata
- **TMS ID**: ELITEA-2199
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **extend-existing** — targets `automation/tests/ui/chat/test_attach_files_multiple_chips_display.py`
  (`TestAttachFilesMultipleChipsDisplay`, ELITEA-2196), already on this batch's trunk
  `tests/batch-chat-remaining-w13` (not yet on `origin/automation/base`). That module already
  covers this case's steps 1/3/5/6 (attach, filenames-next-to-icons, dark styling, +N count) —
  see Coverage Map. Two gaps remain, both requiring genuinely different test DATA than the
  covering test used (all-`.txt`, short names): (a) step 2's "type-appropriate icon" claim is
  **case-text drift** — the live product renders one generic icon for every attachment
  regardless of type (clarification filed, issue **#1591**) — the gap assertion asserts the
  corrected, live-confirmed invariant instead; (b) step 4 (long-filename truncation) was never
  exercised — the covering test's filenames are all short.
- **Cluster note**: analysed together with ELITEA-2467 (same live session — shared
  login/navigation/attach discovery, same `FileList.jsx` surface) but written as a **separate
  AFS** — the two cases diverge in STEPS: ELITEA-2467 additionally requires asserting the "+N"
  overflow indicator's click-to-expand behavior, which THIS case's steps never ask for (its own
  step 6 only asks the indicator to show a count, already covered — see Coverage Map). Both
  AFS's Gap assertions include a truncation check on genuinely overlapping ground — expected,
  per test-case-analysis § Execute: "some overlap when cases differ in steps is acceptable, the
  implementer may consolidate at the code level."

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (the covering test's `conversation_id` fixture already satisfies
  this — the new test method reuses the same fixture).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Viewport `1700×1100` (ELITEA-2196/2197 precedent) — keeps `FileList.jsx`'s width-driven
  visible/overflow split deterministic.

### generate-per-test (created in test setup, no server state — attachments are client-side
until a message is sent, which this case's steps never do)
- **3 genuinely different file types** (the case's own "different types" wording, never
  exercised by the covering test's all-`.txt` set): one `.png` (a minimal valid 1×1 PNG, not
  just a renamed `.txt`), one `.pdf` (minimal `%PDF-1.4` header content), one `.txt`. Confirmed
  live this session: all three attach successfully, no "invalid file type" toast for any.
- **1 genuinely long filename** (≥ 90 chars, e.g.
  `this_is_a_genuinely_very_long_filename_that_should_definitely_get_truncated_in_the_ui_chip_display.txt`)
  — confirmed live: at the 200px-wide chip / ~116px-wide name column, this filename's rendered
  `scrollWidth` (731px) is far past its `clientWidth` (116px) — genuine CSS-ellipsis truncation
  (`text-overflow: ellipsis`, `TypographyWithConditionalTooltip.jsx`), not merely a short name
  that happens to fit.

## Test Steps

1. Navigate to the conversation (reuse `conversation_id` fixture, same as the covering test).
2. Click **+** → **Attach Files**; select the `.png` + `.pdf` + `.txt` files (3 different types)
   in a single file-chooser action.
   - **Verify**: 3 chips render, one per file (`wait_for_attachment_chip_count(3)`).
3. Verify all 3 chips render the exact same icon markup — i.e. the live-confirmed invariant
   that supersedes the case's literal "type-appropriate icon" wording (issue #1591): read each
   chip's icon `outerHTML` via a scoped `.evaluate()` (same idiom as the covering test's
   `has_file_icon` structural read) and assert all 3 are identical, proving the product does
   **not** vary the icon by file type — the corrected, live-confirmed observable.
4. In a separate attach action (fresh chip set, avoids interference with step 2-3's 3-file
   layout), attach the 1 long-filename file alone.
   - **Verify**: the chip's filename element genuinely visually truncates —
     `scrollWidth > clientWidth` on the name element, scoped under the chip's testid (same
     idiom as the covering test's luminance check — a computed-layout read, not a new
     locator).

## Expected Results
- 3 chips (image/pdf/text) render, each showing the exact same generic file-type icon — the
  product does not differentiate by type (case-text clarification, issue #1591; NOT the
  literal case wording).
- The long-filename chip's name text is genuinely, visually truncated (`scrollWidth >
  clientWidth`), matching the case's "truncated with '...'" (the mechanism is CSS
  `text-overflow: ellipsis`, confirmed via source — `TypographyWithConditionalTooltip.jsx`).
- No console errors during the sequence.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click + icon, Attach Files; select files of different types | Files upload | AFS step 2 | `wait_for_attachment_chip_count(3)`, reusing `ChatPage.attach_files_via_menu()` (ELITEA-2196/2197, `chat_page.py:2685`) | asserted (new: exercises 3 genuinely DIFFERENT types, the covering test used only `.txt`) |
| 2 Verify each file chip shows a type-appropriate icon on the left | Icons reflect file types | AFS step 3 | scoped `.evaluate()` reading each chip's `<svg>` `outerHTML`, asserting all 3 are IDENTICAL | **clarification** (issue **#1591**) — live product (`FileList.jsx:88`, confirmed via source AND this session's live run) renders the exact same `AttachedFileIcon` SVG for every attachment regardless of type; zero branching logic exists. Reverse-masking guard: the case's assumption is what's stale, not the product — AFS asserts the corrected, live-confirmed invariant (icon does NOT vary by type) instead of the literal wording. |
| 3 Verify filenames are shown next to icons | Filenames visible | — | `get_visible_attachment_names()` (`chat_page.py:2834`) | **already-covered** — ELITEA-2196's own test (`test_attach_multiple_files_displays_chips_above_composer`, Step 4) asserts this exact observable at `automation/tests/ui/chat/test_attach_files_multiple_chips_display.py:183-187`. No new assertion needed. |
| 4 Verify long filenames are truncated with '...' | Truncation applied | AFS step 4 | `scrollWidth > clientWidth` on the chip's name `<span>`, scoped `.evaluate()` under the testid'd chip parent | asserted *(gap — the covering test's filenames, `testfile_1.txt`…`testfile_4.txt`, are all short; truncation was never exercised)* |
| 5 Verify chips have consistent dark background styling | Styling consistent | — | composited-luminance check, `chat_page.py:2885` `get_attachment_chip_visual_facts()` | **already-covered** — ELITEA-2196's own test (Step 6) asserts this exact observable (`test_attach_files_multiple_chips_display.py:207-228`). No new assertion needed. |
| 6 Verify if more than 4-5 files, a '+N' indicator shows additional count | +N indicator shown | — | `get_attachment_overflow_count()` (`chat_page.py:2814`), `get_total_attached_file_count()` (`chat_page.py:2826`) | **already-covered** — ELITEA-2197's own test (`test_attach_11_files_shows_10_file_limit_warning`, Step 6, `automation/tests/ui/chat/test_attach_files_10_file_limit_warning.py:149-160`) asserts the identical mechanism: total attached (visible + parsed `"+N"` overflow number) equals the expected count. Different trigger scenario (10-file-limit vs this case's plain "4-5+ files"), same underlying observable and same code path (`FileList.jsx`'s `hiddenAttachments.length` → the `"+N"` button text) — behaviourally equivalent per Rule-6. No new assertion needed. |

### Axis 2 — Analyst additions
- Side-channel check: no console errors during the whole sequence — *added: standard per the
  skill's "check the side channels even when the UI looks fine" rule.*
- Step 2 deliberately uses a real `.png` (valid PNG header/IDAT, not a renamed `.txt`) and a
  real minimal `.pdf` (`%PDF-1.4` header) — *added: a renamed-extension file could pass a
  naive extension check but wouldn't be a genuine test of "different types" if the app does
  any content sniffing; confirmed live neither triggers an "invalid file type" toast, same as
  the covering test's `.txt` confirmation.*
- Truncation is asserted via `scrollWidth > clientWidth` (a genuine layout read), not merely
  "the CSS class is present" — *added: matches this suite's own existing discipline for
  genuine-overflow checks (`chat_starter_tile_tooltip_content`'s "conditional on genuine
  visual truncation" precedent, `chat_page.py:848-853`; `chat_messages_scroll_container`'s
  "not just CSS overflow-y" discipline, `chat_page.py:770-774`) — a CSS `text-overflow:
  ellipsis` rule with room to spare wouldn't actually clip anything.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown (`ConversationAPI.delete_conversation`).
- No server-side file/attachment cleanup needed — attachments never reach the backend in this flow.

## Concrete Handles (discovered during exploration)

**Zero new testids required** — every handle this gap needs already exists, confirmed live
against a fresh `git fetch origin` this session:

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Attachment chip (per file, visible row) | `[data-testid="chat-attachment-chip-{index}"]` | **on-main ✓** | pre-existing (`ChatPage.CHAT_ATTACHMENT_CHIP`, `chat_page.py:387`) |
| Chip icon (structural read, no locator) | `chip.evaluate("el => el.children[0].outerHTML")` | n/a — read-only | Same "no new testid needed" precedent as `get_attachment_chip_visual_facts()`'s existing `has_file_icon` check (`chat_page.py:2885-2919`) — extend that method (or add a sibling read) to also capture the icon's `outerHTML` for cross-chip identity comparison. |
| Chip filename element (layout read) | `chip.evaluate("el => { const s=el.querySelector('span'); return {scrollWidth: s.scrollWidth, clientWidth: s.clientWidth}; }")` | n/a — read-only | Same idiom as the existing luminance check — a computed-layout read scoped under the already-testid'd chip, not a new locator. |

## Network Behavior
- No network request fires for the attach-files flow itself (client-side only; unchanged from
  ELITEA-2196/2197's already-documented finding).

## Known Defects Found During Exploration
- None as a functional defect. Case-text clarification filed: issue **#1591** — "Attachment
  chips show one generic file icon, not a type-appropriate icon per file type" (contrasts with
  the Artifacts feature's type-aware icon system, `EliteaUI/src/slices/fileTypes.js`, which
  `FileList.jsx` does not reuse).

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Page object: extend `ChatPage.get_attachment_chip_visual_facts()` (`chat_page.py:2885`) to
  also return the icon's `outerHTML` (or add a sibling `get_attachment_chip_icon_markup(index)`
  method) and a `{scrollWidth, clientWidth}` pair for the name element — both additive, no
  existing signature changes.
- Implementer's call whether to add a NEW test method to
  `TestAttachFilesMultipleChipsDisplay` (same class ELITEA-2198 already extended, per that
  class's own docstring precedent) or a new top-level function in the same module — either is
  consistent with this module's own established "sibling test, same file" pattern.
- Reuse `attach_files_via_menu()` / `close_plus_menu_popper()` / `wait_for_attachment_chip_count()`
  verbatim (all pre-existing, ELITEA-2196/2197).
- Viewport: reuse `1700×1100` (module-level constants already defined in the target file).
- `conversation_id` fixture (`automation/fixtures/data_fixtures.py:38`) — reuse.
