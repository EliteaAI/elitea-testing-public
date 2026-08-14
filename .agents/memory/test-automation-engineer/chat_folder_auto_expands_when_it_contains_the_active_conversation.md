---
name: Chat folder auto-expands when it contains the active conversation
description: FolderAccordion defaultExpanded=containsActiveConversation — seeding into a folder while that conv is still open breaks a "starts collapsed" precondition
type: feedback
---

`FolderItem.jsx` passes `defaultExpanded={containsActiveConversation}` to
`FolderAccordion.jsx` — a folder auto-expands the moment it contains the
currently-active/open conversation (`useEffect` flips `expanded` true on
`defaultExpanded` true, never flips it back false).

**Trap:** seeding a folder-based test by creating conv_a via the UI's own
`+Chat` flow (needed to get real message history — see defect #691),
then moving conv_a into the folder while its own `/chat/{id}` page is
still active, then `page.reload()` — the folder renders EXPANDED on
reload, breaking any case step asserting "folder starts collapsed"
(ELITEA-2098's own Step 1).

**Fix:** navigate away from conv_a to a conversation that will NEVER be
in the folder BEFORE moving conv_a into the folder. Don't reuse the
sibling-under-test (e.g. conv_b) for this if conv_b is also about to be
moved into the same folder — it just reproduces the same auto-expand.
Use a dedicated throwaway conversation
(`ChatPage.click_conversation_item(other_conv_id)`), created via API,
never moved anywhere, cleaned up alongside the rest.

Worked example: `automation/tests/ui/chat/test_open_conversation_from_folder.py`
(ELITEA-2098, fix round 1, PR #1510).
