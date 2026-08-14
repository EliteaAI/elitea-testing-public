---
name: BaseModal aria-labelledby/id mismatch (bug #694) + chat conversation-menu testid gaps
description: BaseModal's Dialog aria-labelledby points at a nonexistent id (breaks a11y app-wide AND the merged delete-conversation test); conversation-menu-menu-button testid is duplicated across every sidebar item (must scope by parent); no data-active state attribute on conversation items; chat's 7 context-menu items carry zero testids
type: feedback
---

## What (confirmed live + via source + via an actual pytest run, ELITEA-2114, 2026-07-21)

1. **`BaseModal.jsx` aria wiring is broken app-wide.** The MUI `Dialog` sets
   `aria-labelledby="alert-dialog-title"` (`BaseModal.jsx:121`), but its own
   `DialogTitle` has `id="variables-dialog-title"` (`:134`) — a stale leftover
   from before the `EL-2863` "universal BaseModal" refactor (EliteaUI commit
   `459c1f8a`, 2026-06-22). **No element with `id="alert-dialog-title"` exists
   anywhere in the DOM**, for any dialog rendered through `BaseModal`/
   `DeleteEntityModal` — confirmed live via
   `document.getElementById('alert-dialog-title') === null` while the delete
   dialog was open, and via source (`BaseModal.jsx` and `DeleteEntityModal.jsx`
   never override the id). This breaks the accessible name for screen readers
   on every such dialog, not just chat's delete-conversation one.
   Filed as **bug #694**.

2. **This silently broke an already-merged test.** `automation/components/mui.py`'s
   `Dialog.get_title()` queries `#alert-dialog-title` and returns `""` when
   absent. `tests/ui/chat/test_conversation_management.py::TestConversationActions
   ::test_delete_conversation_with_confirmation` asserts
   `"Delete conversation" in title_text` — this is now a **deterministic
   failure** (verified by actually running it locally, not just reasoning about
   it): `AssertionError: Expected 'Delete conversation' in title, got:` (empty
   string). The test predates the regression (added 2026-06-19, three days
   before the breaking refactor) so it was presumably green before. **Any case
   touching a `BaseModal`-based dialog's title should assert the dialog BODY
   testid instead (works fine) until #694 is fixed** — don't reach for
   `#alert-dialog-title` or a title testid; neither is reliable right now.

3. **`conversation-menu-menu-button` (the chat sidebar's 3-dot button) is NOT
   unique per conversation.** `ConversationItem.jsx` passes the same static
   `id="conversation-menu"` to `DotMenu` for every list item, so once 2+
   conversations are on screen, an unscoped
   `page.get_by_test_id("conversation-menu-menu-button")` throws Playwright's
   strict-mode "resolved to 2 elements" error (reproduced live). Always scope
   through the parent: `page.get_by_test_id(f"chat-conversation-item-{id}")
   .get_by_test_id("conversation-menu-menu-button")`.

4. **No `data-active`/`data-selected` attribute on `chat-conversation-item-{id}`.**
   The only signal that a sidebar item is the currently-open/highlighted
   conversation is a non-deterministic MUI emotion CSS class hash
   (`css-ctq8e1`-style) — not a stable handle, don't use it. Until a
   `data-active` attribute is added (mirroring the project's existing
   `data-expanded` convention, testing.md § Locator policy), assert
   "conversation X is now active" via `page.url` containing `/chat/{id}` +
   main-panel content instead.

5. **All 7 chat conversation-menu items (Rename, Move to, Playback, Make public,
   Share, Pin on top/Unpin, Delete) carry zero testids** — confirmed live,
   `data-testid` is `null` on every `[role="menuitem"]`. Same root cause as the
   Toolkits/MCP Delete-menuitem gap documented in the sibling
   `shared_delete_entity_modal_and_toolkit_delete_menuitem_testid_gaps.md`
   entry: `ConversationItem.jsx`'s `menuItems` array objects have no `key`,
   and `DotMenu`'s `BasicMenuItem`/`ActionWithDialog` only emit
   `data-testid={testId}-menuitem` when `item.key` is set.

## Why this matters

Any case touching the chat sidebar's conversation delete/rename/pin/move
flow, OR any other `BaseModal` consumer's dialog title, will hit gap 1/2
first — check for bug #694's status before re-diagnosing the same "empty
title" symptom from scratch. Gaps 3–5 are chat-specific but the *pattern*
(shared DotMenu `id` reused across sibling instances; menu items missing
`key`) recurs anywhere `DotMenu`/`ConversationItem`-shaped components are
copied.

## Where

`EliteaUI/src/[fsd]/shared/ui/modal/BaseModal.jsx` (:121 vs :134),
`EliteaUI/src/[fsd]/shared/ui/modal/DeleteEntityModal.jsx`,
`EliteaUI/src/[fsd]/features/chat/conversation-list/ui/conversations/ConversationItem.jsx`
(`menuItems`, `id="conversation-menu"`),
`EliteaUI/src/components/DotMenu.jsx`,
`automation/components/mui.py` (`Dialog.get_title()`),
`automation/tests/ui/chat/test_conversation_management.py`
(`test_delete_conversation_with_confirmation` — currently RED because of #1/#2),
AFS: `test-specs/chat-interface/l2_conversation-deletion_ELITEA-2114.md`,
bug: EliteaAI/elitea-testing-public#694, clarification: #695.
