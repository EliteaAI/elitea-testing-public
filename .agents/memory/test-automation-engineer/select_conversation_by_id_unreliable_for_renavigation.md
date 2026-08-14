---
name: select_conversation_by_id unreliable for re-navigation
description: ChatPage.select_conversation_by_id() (name/href-guessing, no testid) intermittently fails to find a just-renamed conversation
type: feedback
---

`ChatPage.select_conversation_by_id(conversation_id)` (`automation/pages/chat_page.py`)
is a legacy multi-strategy locator (data attributes → `a[href*="/chat/{id}"]` →
`page.evaluate()` scanning `[class*="conversation"]` for the id) — despite its
docstring claiming it's "more reliable than name-based selection", it raised
`AssertionError: Could not find conversation with ID {id} in the sidebar` when
used to re-select a conversation immediately after renaming it and navigating
away/back (ELITEA-2099, chat-remaining-w02).

**Don't reach for it.** For re-navigating to a conversation whose id you
already have, use the testid-scoped locator directly instead:

```python
item = chat.get_conversation_item(conversation_id)   # CONVERSATION_ITEM testid
expect(item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
item.click(force=True)   # force=True bypasses the MUI overlay divs
chat.wait_for_conversation_url(conversation_id, timeout=NAVIGATION_TIMEOUT)
```

This is both simpler and testid-based (no raw CSS/JS scanning), consistent
with the project's testid-only locator policy. `select_conversation_by_id()`
itself is untouched tracked tech debt — not worth fixing inline for one
caller, but don't copy its pattern into new code.
