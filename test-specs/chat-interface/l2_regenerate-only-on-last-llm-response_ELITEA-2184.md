# Test Case: Chat – Regenerate Button Visible on Last LLM Response

## Metadata
- **TMS ID**: ELITEA-2184
- **Priority**: l2 (case: high)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scratch pytest run with project fixtures; Playwright MCP chrome was not installed in this session)
- **User set**: `${TEST_USER}`
- **Status**: **ready-for-automation** (executed live; Regenerate and Delete are conditional on "last message", not on hover alone; see Observations)
- **Neighbours read**: ELITEA-2181 AFS (action icons), `_surface.md` (Streaming section), ELITEA-2182/2183 specs. Not a duplicate: no merged spec asserts Regenerate absent on earlier responses.

## Preconditions
- Logged in; fresh conversation via `conversation_id` fixture. Case says "at least one LLM response"; to prove "earlier" vs "last" we need TWO exchanges (send 2 short prompts, e.g. "Reply with the single word: one" / "... two"; each completes in a few seconds on DEV).

## Test Steps
1. Open `/app/chat/<conversation_id>`, send two prompts, wait for each AI response (`wait_for_ai_response(initial_count=<count before send>)`). Timeline has 4 `chat-message-item` (user, AI, user, AI).
   - Verify: 2 AI items (filter with `ChatPage._is_ai_message`).
2. Scroll to / hover the LAST AI item.
   - Verify: `chat-read-out-button`, `chat-copy-button`, `chat-regenerate-button`, `chat-delete-button` all visible within that item (observed count 1 each).
3. Hover the EARLIER AI item (move mouse to (0,0) first to clear residual hover).
   - Verify: `chat-regenerate-button` count == 0 and `chat-delete-button` count == 0 within it (not in DOM at all). Read-out and Copy ARE present (count 1, hover-revealed), so do not assert "no action icons" on earlier responses.
4. Page-level: `chat-regenerate-button` count over whole page == 1, and it lives inside the last AI item.

## Observations (live, 2026-10-20)
- Source (`ChatMessageWrapper.jsx` `onRegenerate={... isLastMessage && ...}`, `ApplicationAnswerActions.jsx:114-121`): Regenerate is rendered only when `onRegenerate` is passed, i.e. last message; Delete likewise (`isLastMessage && ...onDelete`).
- Earlier AI item: read-out 1, copy 1, regenerate 0, delete 0. Last AI item: 1,1,1,1.
- Last item's Regenerate remained visible after moving the mouse to (0,0) (not hover-only on the last message in this run); the earlier item's Copy/Read-out are hover-gated. Do not assert hover-gating for Regenerate; assert visibility after hovering (case step 2 wording still satisfied).
- Regenerate button has testid `chat-regenerate-button` on DEV, but no aria-label (`BUTTON:` empty). Note ELITEA-2181 AFS said testid "needed"; it is now served.
- Console/network: not inspected beyond test pass (no errors surfaced).

## Coverage Map
### Axis 1
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precond: logged in; conversation with LLM response | - | setup | fixtures + 2 sends | asserted (2 responses needed to define "earlier") |
| 1 Scroll to last LLM response | visible | step 2 | last AI item visible | asserted |
| 2 Hover last response | regenerate + speaker, copy, delete visible | step 2 | 4 testids visible | asserted |
| 3 Hover earlier response | no Regenerate | step 3 | count==0 | asserted |
| 4 Regenerate only on last | exactly one | step 4 | page-wide count==1, inside last item | asserted |
### Axis 2
- Earlier item also lacks Delete (count 0): added, same `isLastMessage` gate, cheap and grounded in source.
- Earlier item DOES carry Read-out/Copy: recorded as a note, not asserted (hover-gated, not case scope).

## Concrete Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Message item | 1 | `chat-message-item` (`ChatPage.messages_container`) | - | testid on DEV ✓ |
| AI-authored filter | - | `ChatPage._is_ai_message` / `AI_MESSAGE_LOGO` (img alt "Elitea") | - | existing, used live ✓ |
| Regenerate | 1 | `chat-regenerate-button` (`ChatPage.regenerate_action_button`) | - | testid on DEV ✓ |
| Read-out | 1 | `chat-read-out-button` | - | testid on DEV ✓ |
| Copy | 1 | `chat-copy-button` (`copy_action_button`) | - | testid on DEV ✓ |
| Delete | 1 | `chat-delete-button` (`delete_action_button`) | - | testid on DEV ✓ |
Use `.within(ai_item)` scoping; do not use `.nth()` sibling picks except enumerating all AI items.

## Automation Hints
- Dismiss `platform-banner-close` if present. Hover: `page.mouse.move(0,0)` before hovering each item (residual-hover gotcha).
- Transit flag: `ChatPage.navigate_to_chat(conversation_id=...)` timed out 15s again (3 tries; same as 2182/2183 notes). Workaround: `page.goto(f"{settings.app_base_url}/app/chat/<id>")` (app_base_url has NO /app) then wait for `chat-message-input`. Implementer should check why.
- No sleeps; use expect with auto-wait for visibility/count.

## Known Defects / Blocked
None.
