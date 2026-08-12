---
name: MUI Dialog needs its own testid, not get_by_role("dialog")
description: Asserting "a modal opened as an overlay" via page.get_by_role("dialog") is a locator-policy violation — add a data-testid to the dialog's visible panel instead.
type: feedback
---

Case text often confirms a modal live via its `role="dialog"` accessibility
attribute (that's exploration evidence an analyst records in the AFS). Do NOT
read that as license to implement the assertion with
`page.get_by_role("dialog")` — it's a role-based locator and fails the
project's testid-only policy (mechanical grep catches it: `get_by_role` is on
the forbidden list in `.agents/role-overrides.md`).

Fix: add `data-testid` to the Dialog's visible content panel (not the MUI
`<Dialog>` component itself — props there don't reliably forward to the
rendered Paper/backdrop; put it on the inner `Box`/panel that actually
contains the modal's content) and assert that instead. Precedent already on
disk before this was even a gotcha: `agent_form_page.py`'s
`agent-welcome-message-dialog` / `model-settings-dialog` testids, and
`admin_users_page.py`'s `users-edit-roles-dialog` — the pattern is "every
dialog gets its own testid," not "dialogs are exempt because role=dialog is
already semantic enough."

Caught this one via my own pre-commit mechanical self-check grep
(`git diff | grep -nE '^[+].*(get_by_role|...)'`) before it ever reached a
reviewer — worth running that grep BEFORE writing the "modal opens as an
overlay" style assertion, not just at the end, since it's an easy one to
reach for instinctively.

(First hit: ELITEA-2356, Agent Hub — open agent detail modal. New testid:
`catalog-agent-modal` on `AgentModal.jsx`'s main-panel `Box`.)
