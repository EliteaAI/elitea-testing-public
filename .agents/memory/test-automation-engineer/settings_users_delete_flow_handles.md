---
name: Settings Users delete-flow handles and helpers
description: The delete-confirmation dialog is the shared DeleteEntityModal — every testid pre-exists; invite_users needs the dialog open first
type: project
aliases: [delete-confirm-dialog, DeleteEntityModal, users delete testids, invite_users]
tags: [area/settings-users, type/handles]
created: 2026-08-29
updated: 2026-08-29
---

## Handles

`DeleteUserButton` (row AND header) renders the shared
`Modal.DeleteEntityModal`, so every handle already exists product-wide:
`delete-confirm-dialog` / `-title` (`Delete confirmation`) / `-message` /
`-entity-name` / `-button` / `-cancel-button` / `-close-button`. **No testid
work is ever needed for a delete case on this surface.**

Message text is selection-size dependent: `Are you sure to delete the selected
user <name>?` (the name is the EMPTY string for a never-logged-in invitee, so
it renders `… user ?`) vs `Are you sure to delete the selected users?` for 2+.
Match the stem for the singular form.

## Helpers (AdminUsersPage)

- `invite_users()` **requires `open_invite_dialog()` first** — the name suggests
  otherwise and it fails silently.
- `delete_user_row()` is the one-shot cleanup helper (four merged callers,
  leave it alone). For assertions between the moments use
  `open_delete_dialog_for_row()` / `open_batch_delete_dialog()` /
  `confirm_delete()` / `cancel_delete()`.
- `reload_and_wait()` reloads and waits on the users-list GET — never
  `networkidle` (`#1847`).

## Proving a negative

To prove "nothing was deleted", count DELETEs with a passive
`page.on("request", …)` listener registered before the first click. A table
read cannot distinguish "nothing happened" from "a delete in flight".

Related: [[users_batch_delete_render_loop]]
