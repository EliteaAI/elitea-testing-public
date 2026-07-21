---
name: Shared DeleteEntityModal and Toolkit/MCP delete-menuitem testid gaps
description: Modal.DeleteEntityModal (~15 call sites) has zero testids on its dialog/buttons; Toolkits+MCP's "Delete" menu item has none either (unlike Credentials' own inline copy); OneClickButton doesn't forward extra props
type: feedback
---

## What (confirmed live, ELITEA-1947, 2026-07-18)

Three-dot menu delete flow for Toolkits/MCP detail pages (`ToolkitsControls.jsx` →
`Controls.ControlsDropdown` → `DotMenu.jsx`, default `id="controls"`):

1. **`controls-menu-button` / `controls-menu` ARE on `origin/main` already** — this
   is the SAME generic testid `CredentialDetailPage.controls_menu_button` already
   uses (`.agents/testing.md`'s shared-component convention working as intended:
   one generic mechanism, reused across Toolkits/MCP/Credentials/Skill/AgentHub/
   SkillHub, all of which call `ControlsDropdown` with the default `id`).
2. **The "Delete" menu item has NO testid, on both `main` and `automation/testids`.**
   `DeleteToolkitButton.jsx`'s `useDeleteToolkitMenu()` builds its `menuItem` object
   (`{ label: 'Delete', icon, confirmText, alarm, disabled, entityName, onConfirm }`)
   with **no `key`** — `DotMenu.jsx` only sets `data-testid={testId}-menuitem` when
   `item.key` is set (`testId: item.key` in both `BasicMenuItem`/`ActionWithDialog`
   call sites). Confirmed live: `data-testid` attribute is literally `null`.
   **Do not confuse with Credentials' `delete-credentials-menuitem`** — Credentials
   writes its OWN inline menu item directly in `CredentialsControls.jsx` (`key:
   'delete-credentials'`), bypassing this shared hook entirely. Fixing Credentials
   did NOT fix Toolkits/MCP; they're different code paths that happen to render
   the same word "Delete".
   Fix: one-line `key: 'toolkit-actions-delete'` addition, same shape as the
   sibling Fork item's `key: FORK_MENU_ITEM_KEY_BY_ENTITY[entity_name] ??
   'entity-actions-fork'` in `ForkEntityButton.jsx` (confirmed live:
   `toolkit-actions-fork-menuitem` already renders correctly).
3. **`Modal.DeleteEntityModal` (`src/[fsd]/shared/ui/modal/DeleteEntityModal.jsx`,
   shared across ~15 call sites — Skills/Agents/Credentials/Pipelines/Artifacts/
   Users/…) has ZERO testids on its dialog container or Cancel/Delete buttons.**
   Only `delete-confirm-name-input` exists (hardcoded generic, confirmed on
   `main`) — and even that resolves to the TextField's WRAPPER `<div>`
   (`MuiFormControl-root`), not the real `<input>`. Click + `press_sequentially()`/
   `type()` on the wrapper DOES work (browser click-delegation focuses the inner
   input; verified `input.value` after), but `.input_value()` on it will throw.

   **UPDATE (2026-07-21, ELITEA-2114, live-reverified on `automation/testids`):**
   this has been partially fixed since — `delete-confirm-dialog` (outer container),
   `delete-confirm-message` (body `<Typography>`), and `delete-confirm-button`
   (the red confirm button) now all carry real testids. **Cancel still has none**
   (`DeleteEntityModal.jsx`'s `actionsNode` renders `Button.BaseBtn` for Cancel
   with no `data-testid` prop passed at all — unlike the confirm button, this
   isn't even an `OneClickButton`-forwarding problem, the call site just never
   wired one). The dialog TITLE also still has no testid, and separately: its
   `<h2>` carries a STALE `id="variables-dialog-title"` that doesn't match the
   `Dialog`'s own `aria-labelledby="alert-dialog-title"` — see the new
   `basemodal_aria_labelledby_id_mismatch_and_conversation_menu_gaps.md` entry
   for the full a11y/automation blast radius (filed as bug #694, EliteaUI
   commit `459c1f8a`, 2026-06-22 regression). Re-verify testid presence before
   trusting either version of this note on a future case — this file clearly
   drifts as the product evolves.
4. **`Button.OneClickButton` (used for `DeleteEntityModal`'s own Delete/confirm
   action, since it renders a custom `actionsNode` that bypasses `BaseModal`'s
   built-in `confirmButtonTestId` prop entirely) destructures only `{ disabled,
   disableRipple, color, onClick, title }` — it does NOT forward `data-testid` or
   any other extra prop.** A testid fix here needs TWO changes: add pass-through
   in `OneClickButton.jsx` itself, AND pass the value from `DeleteEntityModal.jsx`.
   By contrast `Button.BaseBtn` (used for Cancel) DOES spread `...restProps` — a
   Cancel testid would be a one-file fix, Delete's needs two.
5. **`[role="dialog"]` is genuinely ambiguous on an MCP detail page** — confirmed
   3 hidden "MCP Authorization" (OAuth) dialogs sit in the DOM alongside the real
   Delete-confirmation one; `document.querySelector('[role="dialog"]')` picks the
   WRONG one. This isn't just a locator-policy violation risk, it's a genuine
   correctness bug for any role-based selector attempt.

## Why this matters

Any case touching Toolkit/MCP delete (or any OTHER `DeleteEntityModal` consumer —
Skills/Agents/Pipelines/Artifacts/etc.) will hit gaps 2–4 above. Check this entry
before re-discovering the same gaps from scratch on the next delete-flow case.

## Where

`EliteaUI/src/pages/Toolkits/DeleteToolkitButton.jsx`,
`EliteaUI/src/[fsd]/shared/ui/modal/DeleteEntityModal.jsx`,
`EliteaUI/src/[fsd]/shared/ui/button/OneClickButton.jsx`,
`EliteaUI/src/components/Fork/ForkEntityButton.jsx` (the working sibling pattern),
`automation/pages/credential_detail_page.py` (existing `controls_menu_button`
precedent to port), AFS: `test-specs/mcp/l3_delete-remote-mcp_ELITEA-1947.md`.
