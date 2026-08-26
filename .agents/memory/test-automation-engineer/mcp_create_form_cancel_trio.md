---
name: MCP create-form Cancel trio (two-step gesture)
description: Create-form Cancel != detail Discard — separate testids, both confirm buttons read "Discard"; naming split in McpFormPage
type: reference
aliases: [toolkit-form-cancel-button, cancel during creation, create form cancel dialog, ELITEA-1960]
tags: [area/mcp, type/page-object]
created: 2026-08-24
updated: 2026-08-24
---

## The trio

`McpFormPage` now binds BOTH cancel/discard flows, and they are different surfaces:

| Flow | Trigger field | Dialog field | Confirm field |
|---|---|---|---|
| CREATE form (`/mcps/create/mcp`) | `create_cancel_button` (`toolkit-form-cancel-button`) | `cancel_confirm_dialog` (`toolkit-form-cancel-confirm-dialog`) | `cancel_confirm_button` (`toolkit-form-cancel-confirm-button`) |
| DETAIL page (`/mcps/all/{id}`) | `detail_discard_button` | `discard_confirm_modal` | `discard_confirm_button` |

Both confirm buttons are labelled **`Discard`**; only the trigger differs
(`Cancel` vs `Discard`). Methods mirror each other: `click_cancel_creation()` /
`get_cancel_confirm_message()` / `confirm_cancel_creation()`.

## Behaviour traps

- **Cancel cancels nothing by itself** — the click only opens the dialog; the form
  stays mounted holding every value until Discard is confirmed.
- **Confirming does NOT change the URL.** The create form unmounts and the type
  picker re-renders, but the route stays `/mcps/create/mcp` (no `navigate()` exists
  in the cancel path). Assert unmount + `mcp-type-picker-heading`, never the URL —
  clarification #1747.
- Both confirm dialogs' testids land on the MUI `Dialog` **root**, so
  `text_content()` concatenates title + message + both button labels ⇒ assert `in`,
  never `==`. Unmount is `to_have_count(0)` (detached), not `not_to_be_visible()`.

## Console filter

A cancel flow mounts the MCP type picker TWICE, and the picker deterministically
logs React's `unique "key" prop` error (#656). Unlike the other MCP specs you
**cannot** dodge it by registering the listener late — returning to the picker IS
the observable. Filter by message (`'unique "key" prop' in msg.text`) plus the
standing `/socket.io/` + `@vite/client` dev-server noise, and keep the assertion.

Related: [[project_briefing]]
