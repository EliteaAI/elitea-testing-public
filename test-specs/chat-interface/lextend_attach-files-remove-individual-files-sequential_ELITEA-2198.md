# Test Case: Chat – Attachment Removal – Remove Individual Files by Clicking X Button

## Metadata
- **TMS ID**: ELITEA-2198
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst/Implementer**: test-automation-engineer (agent, combined analyst+implementer slot)
- **Status**: **extend-existing** — targets `test-specs/chat-interface/l3_attach-files-multiple-chips-display_ELITEA-2196.md` /
  `automation/tests/ui/chat/test_attach_files_multiple_chips_display.py` (already on this batch's trunk
  `tests/batch-chat-remaining-w13`, not yet merged to `origin/automation/base`). Case executed live
  against `localhost:5173` via a real pytest run of the appended test (evidence below). Feature works
  correctly, matches Objective/Pass criteria. Zero new testids (the covering spec's ELITEA-2196 work
  already added `chat-attachment-remove-chip-{index}` and every page-object method this case needs).
  Zero defects.
- **Extension target**: `test-specs/chat-interface/l3_attach-files-multiple-chips-display_ELITEA-2196.md`
  covers "attach 4, click X on chip 0, verify the other 3 remain" — this case's own steps 1-2 are the
  SAME mechanism, already proven there. The genuinely new observable is steps 3-4: click X on a
  **second, different** chip (after the first removal already happened) and verify exactly 2 remain
  with the correct filenames — i.e. that individual removal is not a one-shot/first-click-only affordance
  but keeps working correctly across sequential removals, decrementing state consistently each time.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation with 4 files attached (a fresh conversation via the `conversation_id`
  fixture + `attach_files_via_menu()`, same as the covering ELITEA-2196 test — no pre-existing messages
  required for "open conversation").

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

### generate-per-test (created in test setup, no server state — attachments never reach the backend
until a message is sent, which this case's steps never do; same finding as ELITEA-2196/2197)
- 4 uniquely-named `.txt` files, generated via `tmp_path` (same pattern as the covering test).

## Test Steps

1. Attach 4 files via the **+ > Attach Files** flow; verify all 4 chips shown.
   - **Verify**: 4 chips visible (`wait_for_attachment_chip_count(4)`, `get_visible_attachment_names()`
     matches selection order).
2. Click the X (remove) button on the first file chip (index 0).
   - **Verify**: first chip removed; 3 remain (`wait_for_attachment_chip_count(3)`, remaining names ==
     the last 3 of the original 4, in order).
3. Click the X (remove) button on another chip — the (post-renumbering) chip now at index 0, i.e. a
   **different** file than the one removed in step 2.
   - **Verify**: that file removed; 2 remain (`wait_for_attachment_chip_count(2)`, remaining names == the
     last 2 of the original 4, in order).
4. Verify the remaining files are still shown correctly.
   - **Verify**: 2 chips visible, each showing its own filename + a functioning X button (chip 0 → 1
     `.count()`, chip 1 → 1 `.count()`) — confirms removal state is internally consistent (no ghost
     chip, no duplicate, no drop of an unrelated file).

## Expected Results
- Removing a chip decrements the visible count by exactly 1 and leaves every *other* file's chip intact,
  **repeatably across two consecutive removals** — not just on the first click.
- After 2 removals, exactly 2 chips remain, showing the 2 files that were never clicked, in original
  selection order.
- No console errors during the sequence.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Attach 4 files; verify all 4 chips shown | 4 chips visible | AFS step 1 | `wait_for_attachment_chip_count(4)` + `get_visible_attachment_names()` | asserted |
| 2 Click X on first file chip | First chip removed; 3 remain | AFS step 2 | `wait_for_attachment_chip_count(3)` + `get_visible_attachment_names() == file_names[1:]` | asserted — same mechanism the covering ELITEA-2196 test already proves (its own Step 5 functional check), re-driven here as this case's own precondition for step 3, not re-claimed as new coverage |
| 3 Click X on another chip | That file removed; 2 remain | AFS step 3 | `wait_for_attachment_chip_count(2)` + `get_visible_attachment_names() == file_names[2:]` | asserted — **the gap**: a SECOND sequential removal, not exercised by the covering test |
| 4 Verify remaining files still shown | 2 chips visible | AFS step 4 | per-chip name match (already covered by step 3's list-equality) + per-chip remove-button `.count()==1` (functioning affordance, not a stale/ghost DOM node) | asserted |

### Axis 2 — Analyst/implementer additions
- Side-channel check: no console errors during the whole sequence — *added: standard per the skill's
  "check the side channels even when the UI looks fine" rule; none observed live.*
- Order-preservation assertion (`get_visible_attachment_names() == file_names[2:]`, not just a bare
  count) — *added: a count-only check would pass even if removal silently dropped the WRONG file (e.g.
  an off-by-one index bug after renumbering); asserting the exact remaining filenames catches that
  class of defect, which the case's own "verify remaining files still shown" line implies but does not
  spell out mechanically.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown (`ConversationAPI.delete_conversation`).
- No server-side file/attachment cleanup needed (attachments never reach the backend in this flow).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** | pre-existing |
| "Attach Files" menu item (popper) | `[data-testid="chat-attach-menuitem-button"]` | **on-main ✓** | pre-existing, `ChatPage.attach_files_button` |
| Attachment chip (per file, visible row) | `[data-testid="chat-attachment-chip-{index}"]` | **on-main ✓** | pre-existing, `ChatPage.CHAT_ATTACHMENT_CHIP` |
| Attachment chip remove (X) icon | `[data-testid="chat-attachment-remove-chip-{index}"]` | **on `automation/testids` only (awaiting human promotion to `main`)** — added by the covering ELITEA-2196 implementation (`EliteaAI/EliteaUI@7f29c3dc`) | pre-existing as of this batch's trunk; `ChatPage.CHAT_ATTACHMENT_CHIP_REMOVE`, `get_attachment_chip_remove_button()`, `remove_attachment_chip()` — all reused verbatim, zero new testids for this case |

## Network Behavior
- No network request fires for attach or remove (client-side only, same as ELITEA-2196/2197).

## Known Defects Found During Exploration
- None.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Extend `TestAttachFilesMultipleChipsDisplay` in
  `automation/tests/ui/chat/test_attach_files_multiple_chips_display.py` with a new, sibling test method
  (additive-only — the existing `test_attach_multiple_files_displays_chips_above_composer` is untouched).
  Reuse `attach_files_via_menu()`, `close_plus_menu_popper()`, `wait_for_attachment_chip_count()`,
  `get_visible_attachment_names()`, `remove_attachment_chip()` verbatim — all pre-existing from ELITEA-2196.
- Viewport: reuse the established `1700×1100` viewport so all 4 files render with zero overflow.
- `conversation_id` fixture (`automation/fixtures/data_fixtures.py:38`) gives a fresh, isolated conversation.
