# Test Case: Attachment blocking during active run

## Metadata
- **TMS ID**: ELITEA-2877
- **Linked Story**: EliteaAI/elitea_issues#6115, EliteaAI/elitea_issues#6448
- **Priority**: l1
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to Elitea.
- Chat interface is accessible, a fresh conversation exists (`conversation_id`
  fixture).
- Mid-turn injection enabled for the project — shared fixture, see ELITEA-2875
  AFS.
- A small test file available on disk for the attach attempt (reuse the
  project's existing test-file fixture/factory if one exists — not
  independently located this pass; a plain `.txt` file with trivial content
  is sufficient, matching the case's "any small file" data requirement).

## Test Data
### reuse-existing
- Long-running prompt (same as ELITEA-2875).
- Plain-text interjection: e.g. `"plain text interjection, no attachment"`.
- Test file: any small `.txt` file.

## Test Steps
1. Navigate to a fresh conversation, send the long-running prompt, and reach
   the interjectable window (`interjection-composer` present).
   - **Verify**: `interjection-composer` present.
2. Check the attachment entry point's state. **This is NOT a standalone
   visible button** — reach it via `plus-menu-button` → `chat-attach-menuitem-button`
   inside the opened popper (see `_surface.md` ELITEA-2197/2200 section for why;
   same mechanism applies here).
   - **Verify**: `chat-attach-menuitem-button` carries the DOM `disabled`
     attribute (confirmed live: `el.disabled === true`,
     `el.hasAttribute('disabled') === true`, computed `pointer-events: none`)
     while the run is active.
3. Attempt to trigger a file attach while the run is active and confirm it is
   blocked. Two independently-confirmed signals, both exercised:
   - **Click attempt**: clicking the disabled `chat-attach-menuitem-button`
     fires **zero** `filechooser` events (confirmed live via a real
     `page.on("filechooser")` listener — 0 opens across the attempt).
   - **Drag-and-drop attempt**: dropping a file onto the composer while
     streaming is blocked by the SAME gate at the `onDrop` handler level
     (`disableAttachments || isLoading || isStreaming` in
     `NewChatInput.jsx`, confirmed via source read) and surfaces
     `toastError('Attachments are not allowed.')` instead of attaching —
     **not independently drag-tested live this pass** (see Blocked Steps);
     the disabled-button + zero-filechooser proof already satisfies this
     case's Pass/Fail criteria on its own, since both attempts share one
     upstream `isStreaming` gate.
   - **Verify**: no file becomes attached via either path (no attachment
     chip renders in the composer).
4. Send a plain-text interjection message (no attachment) while the run is
   still active.
   - **Verify**: `chat-inject-button` click succeeds, `interjection-queue-item`
     count increments by 1, and its text matches the sent message.
5. Verify the queued message carries no attachment indicator.
   - **Verify**: the `interjection-queue-item` element has zero
     `[data-testid*="attachment"]` descendants (confirmed live:
     `PendingInjectionItem.jsx` only ever renders the item's text, there is
     no attach-while-queued path at all).
6. Wait for the agent run to complete (full drain — `interjection-composer`
   and `interjection-queue-area` both gone).
   - **Verify**: use `wait_for_ai_response()`/poll loop, never a sleep.
7. Verify the attachment button re-enables after completion.
   - **Verify**: re-open the plus menu (`plus-menu-button` →
     `chat-attach-menuitem-button`) and confirm the `disabled` attribute is
     gone (`el.disabled === false`, confirmed live within ~1s of the run
     ending).

## Expected Results
- The attach entry point (`chat-attach-menuitem-button`) is disabled during
  an active run — both a click and a drag-and-drop attempt are blocked.
- A plain-text interjection is still accepted and queues successfully, with
  no attachment indicator.
- The attach entry point re-enables once the run completes.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Login and start agent run | Agent starts processing message | step 1 | step 1 | asserted |
| 2 Check attachment button state | Attachment button is disabled (grayed out) | step 2 | step 2: `disabled` attribute + `pointer-events` | asserted |
| 3 Attempt to drag and drop a file onto chat input | File drop is blocked, no file attached | step 3 | step 3: `onDrop` gate (source-confirmed), click path (live-confirmed) | asserted *(drag path source-confirmed, not independently live-drag-tested — see Blocked Steps)* |
| 4 Send plain text interjection message | Message is queued successfully | step 4 | step 4: queue item count/text | asserted |
| 5 Verify no attachment on queued message | Queued message has no attachment indicator | step 5 | step 5: zero attachment descendants | asserted |
| 6 Wait for agent run to complete | Agent response finishes | step 6 | step 6: full-drain poll | asserted |
| 7 Verify attachment button re-enabled | Attachment button becomes active/clickable again | step 7 | step 7: `disabled` attribute gone | asserted |

Axis 2 — Analyst additions:
- Step 3 asserts via a real `filechooser` listener (0 opens) rather than only
  checking the `disabled` attribute — *added: a `disabled` DOM attribute alone
  doesn't prove the click is actually inert in every browser/MUI-version
  combination; the filechooser-count assertion is the behavioral proof the
  case's own Pass/Fail criteria ("File attachment succeeds during active
  run" as the Fail condition) actually demands.*

## Cleanup
1. Delete the conversation via `conversation_id` fixture teardown.
2. Restore `midturn_injection_enabled` per the shared fixture's teardown.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Plus menu trigger | `[data-testid="plus-menu-button"]` (existing `ChatPage.plus_menu_button`) | n/a — confirmed on-main |
| Attach Files menu item (REAL entry point) | `[data-testid="chat-attach-menuitem-button"]` (existing `ChatPage.attach_files_button`, per its own docstring re-pointed away from the dead `chat-attach-button` testid — see ELITEA-2197/2200 `_surface.md` section) | n/a — confirmed on-main; `attach_files_button` field already correctly aliased |
| Interjection-aware composer wrapper | `[data-testid="interjection-composer"]` | n/a |
| Send-to-running-agent (inject) button | `[data-testid="chat-inject-button"]` | n/a |
| Queue item | `[data-testid="interjection-queue-item"]` | n/a |

## Network Behavior
No attach-related network call fires during the blocked attempts (confirmed:
0 `filechooser` events means no file-selection flow, hence no upload POST, is
ever reached). The plain-text interjection's `POST .../elitea_core/inject/...`
fires normally, same as ELITEA-2875.

## Known Defects Found During Exploration
None found.

## Blocked Steps
- The drag-and-drop half of step 3 was source-confirmed
  (`NewChatInput.jsx`'s `onDrop` handler shares the identical
  `disableAttachments || isLoading || isStreaming` gate as the click path,
  and short-circuits to the same `toastError`) but **not independently
  exercised live** — Playwright's synthetic `dragenter`/`dragover`/`drop`
  event dispatch for a real OS file-drag is unreliable without a genuine
  file-system-backed drag source, and the click-path + source-read evidence
  already satisfies the case's stated Pass/Fail criteria (both failure modes
  share one upstream gate). Implementer: if a true drag-and-drop assertion is
  wanted, Playwright's `page.locator(...).dispatchEvent('drop', { dataTransfer
  })` with a constructed `DataTransfer`-like object is the usual escape
  hatch; flagging rather than shipping an unverified mechanism as fact.

## Automation Hints
- Shares the `midturn_injection_enabled` fixture with the rest of this
  family.
- Use a real `page.on("filechooser")` listener (clear/reset it between
  attempts) to prove the click path is inert — don't rely solely on the
  `disabled` DOM attribute.
- `ChatPage.attach_files_button` already uses the correct re-pointed testid
  (`chat-attach-menuitem-button`) per existing project convention — reuse
  `ChatPage.open_attach_menuitem()` to open the popper before asserting the
  item's disabled state, don't re-derive the popper-open sequence.
