---
name: Paste over an already-full truncated field is a no-op — clear first
description: Pasting onto a slice(0,MAX)-truncated field at cursor-end doesn't change its value; clear before pasting to get a meaningful assertion
type: feedback
---

On any rename editor governed by an `onChange` handler that does
`event.target.value.slice(0, MAX)` (folder rename `FolderItem.jsx` and
conversation rename `ConversationItem.jsx` both do this, shared
`MAX_CONVERSATION_LENGTH = 50`, `EliteaUI/src/common/constants.js:74`):
pasting additional text at the end of an ALREADY-50-char field (cursor
naturally lands at the end after `press_sequentially` typing) is a **no-op**.
The browser computes the raw concatenated DOM value BEFORE `onChange` fires
(e.g. `"B"*50 + "C"*70` = 120 chars), then `.slice(0, 50)` returns exactly the
ORIGINAL first 50 characters — the field visibly does not change.

This technically still satisfies a case expectation like "no more than 50
characters after paste" (50 ≤ 50), but it's a weak, easily-misread test signal
— a reader can't tell "truncation is still active" from "the interaction did
nothing at all". `to_have_value(pasted_content_truncated)` will FAIL if you
assert the pasted content should now be showing.

**Fix**: call `clear_folder_name()`/`clear_conversation_name()` (or equivalent)
immediately before the paste, same as ELITEA-2104's own case text does
explicitly for the conversation entity. This produces the pasted content's OWN
first-50-chars in the field — a strong, unambiguous truncation proof. Confirmed
live both ways (ELITEA-2129 implementation, 2026-08-15) before picking this
shape.
