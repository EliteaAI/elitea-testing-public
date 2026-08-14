---
name: Conversation rename editor testids added; "Edit" case text is always "Rename" live
description: ConversationItem.jsx rename input/confirm/cancel had zero testids before ELITEA-2099; case text drift is the same pattern already filed for ELITEA-2114/#695
type: feedback
---

## Testids added (ELITEA-2099, `EliteaAI/EliteaUI@ff56e29d` on `automation/testids`)

`ConversationItem.jsx`'s inline rename editor (opened via the context menu's
"Rename" item) had **zero** testids before this pass. Added, mirroring
`FolderItem.jsx`'s pre-existing `chat-folder-name-*` shapes exactly (same
`Input.StyledInputEnhancer` component, same `inputProps` channel — ladder rung 1,
no new DOM/hooks):

- `chat-conversation-name-input`
- `chat-conversation-name-confirm-button` (+ `data-disabled="true"/"false"` off
  `isSaveEnabled = ConversationNameRegExp.test(name) && (isNew || name !== original)`)
- `chat-conversation-name-cancel-button`

Same a11y-snapshot-pruning gotcha as the folder confirm button (ELITEA-2458): in the
disabled/unchanged state the confirm button may not appear in a `browser_snapshot`
accessibility tree at all — assert via the testid locator directly, never via a
snapshot read. Cancel is unaffected (always `cursor:pointer`).

Clicking confirm on a conversation that ISN'T already the active one also navigates
into/selects it (URL `/chat` → `/chat/{id}?name=...`) — incidental `onSave`→`onEdit`
side effect, not a defect; expect it in any URL assertion right after a checkmark click.

## "Edit option" case text is stale — the live label is always "Rename"

Any TMS case describing the conversation three-dot menu's rename item as "Edit" (or
listing a menu content that includes "Export") is stale. `ConversationItem.jsx`'s
`menuItems` array literally labels it `'Rename'`; "Export" doesn't exist anywhere in
this menu. Confirmed identical to the already-accepted #695 (ELITEA-2114) pattern —
filed as sibling clarification **#1513** for ELITEA-2099 rather than a duplicate,
per profile.md's sibling rule (same object/pattern, different TMS case id). Full
live menu-item set for a non-personal/non-public project (id 471): Rename, Move to,
Playback, Duplicate, Make public, Share, Pin on top, Delete (8 items) — count/set is
project-dependent (#695 saw 5 in the personal project), don't hardcode.

If you hit this AGAIN on a third conversation-rename-family TMS case (e.g. one of
ELITEA-2100–2113), don't file a third clarification — the pattern is now
established across two sibling tickets (#695, #1513); comment the new occurrence on
#1513 instead, or ask the lead whether an umbrella clarification for the whole
ELITEA-2100–2113 family is warranted.
