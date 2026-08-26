---
name: Reviewer check — bare .is_visible() right after a click with no prior wait
description: Locator.is_visible() is a one-shot, non-polling read; flag it whenever it is the FIRST observation of a state transition (dialog/popover opening) triggered by an immediately-preceding click that itself contains no wait.
type: feedback
---

Companion angle to the implementer-side entry
`.agents/memory/test-automation-engineer/locator_is_visible_timeout_kwarg_does_not_poll.md`
("`Locator.is_visible(timeout=...)` does not poll — the kwarg is ignored") —
this note is the REVIEWER-side check: what to grep for and how to judge it.

## What to look for

A diff line shaped like:

```python
chat.some_menu_item_click(...)         # or any click() with no .wait_for() after it
assert chat.some_dialog.is_visible(), "..."
```

`is_visible()` snapshots the DOM at call time; it does not retry. If the
preceding action is a fire-and-forget click (menu item click, button click)
that itself has no wait baked in for the RESULTING UI (a dialog fade-in, a
popper open), the assertion is racing the animation and can false-fail
intermittently — exactly the failure mode the memory entry above documents
(hit live on ELITEA-2368, `answer_thought_accordion.is_visible(timeout=90_000)`
returned `False` almost instantly because `timeout=` on `is_visible()` is
silently ignored).

## How to judge it (not every is_visible() is wrong)

Established, repeatedly-used convention in this suite for "click → confirm
dialog opens" is either `expect(dialog).to_be_visible(timeout=...)` or an
explicit `dialog.wait_for(state="visible", timeout=...)` — see
`ChatPage.delete_confirm_dialog` / `ChatPage.add_users_dialog` callers
(`test_conversation_deletion_flow.py`, `test_delete_confirmation_modal_ui_validation.py`,
`test_invite_users_add_cancel_close.py`) — several of which pair a real wait
FIRST and only THEN add a redundant `assert dialog.is_visible()` as a
documentation-style reinforcement. That combination is fine (harmless
one-shot read-after-wait, per the implementer-side entry's own "when it's
still safe" section). What's not fine is a bare `is_visible()` standing in
for the wait itself, with nothing polling before it.

## Seen

- PR #1562/ELITEA-2188 (`test_public_conversation_green_icon.py`, step 3):
  `chat.click_conversation_menu_item("make-public", ...)` (no wait for the
  resulting dialog — `click_conversation_menu_item()`'s own implementation
  only waits for the MENU ITEM to be clickable, not for anything after)
  immediately followed by `assert chat.make_public_confirm_dialog.is_visible()`.
  MUI dialogs fade in over ~300ms (`.claude/rules/mui-patterns.md` § MUI
  Animation Waits) — this is a real, not theoretical, race. Flagged at
  review; fix is a one-line swap to
  `expect(chat.make_public_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)`
  matching the sibling dialogs' own established idiom.
