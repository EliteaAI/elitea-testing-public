---
name: conversation_item_testid_hidden_while_editing
description: chat-conversation-item-{id} testid does not exist in DOM while ConversationItem.jsx is in isEditing state
type: feedback
---

`ConversationItem.jsx` (`EliteaUI/src/[fsd]/features/chat/conversation-list/ui/conversations/ConversationItem.jsx`)
renders two mutually-exclusive trees:

```js
if (!isEditing) return renderConversationContent();  // carries data-testid="chat-conversation-item-{id}"
return <ClickAwayListener>...</ClickAwayListener>;    // the inline editor — NO chat-conversation-item-{id} anywhere
```

So while the inline rename editor is open (`isEditing === true` — including the
"disabled checkmark, click has no effect, editor stays open" state exercised by
ELITEA-2105–2108), `[data-testid="chat-conversation-item-{id}"]` is **absent from
the DOM entirely** — asserting against it fails with Playwright's
`element(s) not found`, not a text mismatch. This bit ELITEA-2105/2106/2107/2108's
first implementation run (4/4 failed) before the fix.

**Fix:** to verify "the conversation's name is unchanged" while the editor stays
open (no cancel/close action in the case's own steps), read the PERSISTED name via
`conversation_api.get_conversation(conv_target_id)["name"]` instead of the sidebar
DOM — it's the real backend record, not a substitution, and it's available
regardless of `isEditing` state. Only reach for the `chat-conversation-item-{id}`
locator once you've confirmed (or caused, e.g. via Cancel) the editor to be closed.

Same folder-rename component (`FolderItem.jsx`) likely has the identical shape —
verify before reusing this pattern there.
