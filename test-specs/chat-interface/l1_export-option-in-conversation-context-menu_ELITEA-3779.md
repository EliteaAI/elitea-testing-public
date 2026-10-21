# Test Case: Chat - Export option appears in the conversation context menu

## Metadata
- **TMS ID**: ELITEA-3779
- **Priority**: l1 (case: high)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scratch pytest via framework auth, headless), project Private
- **User set**: `${TEST_USER}`
- **Status**: ready-for-automation
- **surface_key**: `chat-conversation-context-menu`
- **Neighbour checked**: `automation/tests/ui/chat/test_chat_export_download.py` (ELITEA-3784) only asserts the Export item is visible then clicks it; it does not assert order, item set, enabled state, label, icon, dismissal. Different observable, so NOT covered/extend.

## Preconditions
- Test creates its own conversation via `conversation_api.create_conversation(name)` (empty is enough), deletes it in `finally`.
- Open the page with `page.goto(f"{app_base_url}/app/chat")` + `chat.dismiss_platform_banner_dialog()` (NOT `navigate_to_chat()`/`wait_for_page_load()` - they time out on DEV on the blank-chat landing, 15s `chat-message-input` wait; reproduced 3x this run, POSSIBLE REGRESSION in that helper on the blank landing - see findings). Wait on `get_conversation_item(id)` visible instead.

## Steps (observed live)
1. Chat list shows the created item `chat-conversation-item-{id}` (bg while hovered: `rgba(106, 232, 250, 0.1)`).
2. Hover item -> hover state (computed background changes; 3-dot `conversation-menu-menu-button` becomes visible inside the item).
3. **Right-click opens NO menu** (0 `chat-conversation-menu-*-menuitem` after `button="right"`). Case text drift (same as ELITEA-3784): the menu opens from the hover 3-dot button (`ChatPage.open_conversation_context_menu`). Clarification, not a defect.
4. After clicking the 3-dot button, `[role="menu"]` is present with exactly 7 items, in DOM order:
   1. `rename` "Rename" 2. `move-to` "Move to" (2 svgs: icon + chevron) 3. `playback` "Playback" 4. `export` "Export" 5. `share-external` "Share externally" 6. `pin` "Pin on top" 7. `delete` "Delete".
   Case lists "Duplicate" - it does NOT exist on DEV (drift). `make-public` key is in `CONVERSATION_MENU_ITEM_KEYS` but not rendered for a private-project chat.
5. Export item: `role="menuitem"`, `aria-disabled` absent (not disabled), `is_enabled()` true, text exactly "Export", 1 `svg` icon (no testid on the svg). Position: 4th of 7, directly after Playback and before Share externally.
6. Clicking elsewhere (`page.mouse.click(1000,500)`) closes the menu (menuitem count 0), conversation item still visible/unchanged.
7. Keyboard (case step 13-14 "if supported"): focus lands on the menu container (DIV, no role/testid, tabindex -1); ArrowDown/Tab do NOT move focus to items, Enter does nothing (no export modal). Keyboard navigation to Export is NOT supported on DEV -> per the case's own conditional, do not automate step 14. Optional: Escape closes the menu (Escape on the later-opened modal verified to leave 0 modals).

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| 1 | `chat-conversation-item-{id}` (`ChatPage.CONVERSATION_ITEM`, `get_conversation_item`) | - | testid on DEV ✓ |
| 1 | `conversation-menu-menu-button` scoped in item (`get_conversation_menu_button(id)`) | - | testid on DEV ✓ (shared non-unique, scope to item) |
| 1 | `chat-conversation-menu-{key}-menuitem` (`get_conversation_menu_item(key)`; keys rename, move-to, playback, export, share-external, pin, delete) | - | testid on DEV ✓ |
| 1 | prefix enumerator `CONVERSATION_MENU_ITEM_PREFIX` (+ `get_open_conversation_menu_item_count()`) | - | testid on DEV ✓; DOM order = visual order (enumerate with a loop over `.count()`, read `data-testid` of each) |
| ladder | export item icon: `svg` inside the export menuitem | `chat-conversation-menu-export-icon` | ladder css `svg` scoped under the testid'd menuitem (exactly 1); declare as ScopedLocator within the item |
| ladder | `share-external` key missing from `CONVERSATION_MENU_ITEM_KEYS` (page object tuple has `share`, DEV renders `share-external`) | - | note: tuple is only documentation; `get_conversation_menu_item` formats any key |

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| Step 1-2 chat list / conversation visible | item visible | `get_conversation_item` visible | covered |
| Step 3 hover | hover state | item hover; assert 3-dot button becomes visible (and/or bg colour changes) | covered |
| Step 4 right-click | context menu appears | hover + 3-dot button | **clarification** (right-click opens nothing; assert 0 items after right-click optional as Axis 2 only if stable) |
| Step 5 menu has multiple options | multiple options | count == 7 | covered |
| Step 6 Export visible | visible | `to_be_visible` on export item | covered |
| Step 7 order Rename, Move to, Playback, Duplicate, Export, Share externally, Pin on top, Delete | that order | assert ordered list == [rename, move-to, playback, export, share-external, pin, delete] | covered with **clarification** (no Duplicate on DEV) |
| Step 8 positioning | between other options | Export index 3 of 7, neighbours playback/share-external | covered |
| Step 9 enabled | not greyed | `to_be_enabled` + no `aria-disabled="true"` | covered |
| Step 10 label | text "Export" | `to_have_text("Export")` | covered |
| Step 11 icon | icon present | 1 `svg` in export item | covered |
| Step 12 click elsewhere | menu closes, no action | click empty area; 0 menuitems; conversation item still there; no modal | covered |
| Step 13-14 keyboard | works if supported | NOT supported (observed) | **out-of-scope / not applicable** per "if supported"; recorded as observation |
Axis 2 extra: opening the menu does not open the export modal (`export-chat-modal` count 0) - guards accidental trigger.

## Open items / findings
- Clarifications: right-click does not open the menu; "Duplicate" absent; keyboard navigation unsupported (arrow/tab do not move focus to items; arguably an a11y gap - menu items are `role=menuitem tabindex=-1` but focus stays on container). Not filed as a bug: case says "if supported"; no explicit requirement.
- No console instrumentation in scratch run; no product defect.

## Automation Hints
- Single test, no new page-object locators required beyond the optional icon ScopedLocator; reuse `open_conversation_context_menu`, `get_conversation_menu_item`, `CONVERSATION_MENU_ITEM_PREFIX`. Add a small page-object method returning the ordered list of open-menu item keys (loop `.count()` and read `data-testid`, strip prefix/suffix).
- `@pytest.mark.tms("ELITEA-3779")`, markers ui/chat/regression/p1. No sleeps; wait for first menuitem visible, and for `to_have_count(0)` after click-away.
