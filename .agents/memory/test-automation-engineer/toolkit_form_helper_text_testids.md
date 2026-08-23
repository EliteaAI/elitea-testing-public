---
name: Toolkit form validation helper-text testids
description: Schema-driven toolkit fields get a free `<field>-input-helper-text` testid; the Name/Description fields do NOT — they render through a different component
type: reference
aliases: [helperTextTestId, Field is required, toolkit validation error, toolkit-field-url-input-helper-text, toolkit-form-name-input-helper-text]
tags: [area/toolkits, area/mcp, type/locator]
created: 2026-08-24
updated: 2026-08-24
---

## Two different renderers, only one wires the helper testid

Toolkit / MCP create + detail forms render their fields through **two** components:

| Field | Component | Helper-text testid |
|---|---|---|
| Every schema-driven field (`url`, `client_id`, `timeout`, …) | `ToolBaseProperty.jsx:610` | **free** — ``helperTextTestId={`toolkit-field-${k}-input-helper-text`}`` |
| Toolkit **Name** and **Description** | `NameDescriptionInput.jsx` | **none by default** — passes `helperText` but not `helperTextTestId` |

So `toolkit-field-<k>-input-helper-text` already exists for any schema field, but the
Name/Description equivalents must be added. Added `toolkit-form-name-input-helper-text`
for ELITEA-1924 (EliteaAI/EliteaUI@35440c78, `automation/testids`); Description still has
none — add it the same way if a case ever asserts it.

`helperTextTestId` is a first-class prop of the shared `InputBase`
(`InputBase.jsx:101,270`) — adding it is a **one-line, purely additive prop**, no new DOM
node, no hook, zero functional impact, so it sails through `add-data-testid` § Step 5.5.
Naming convention is `<input-testid>-helper-text` (also used by `SecretField.jsx:88`).

## Asserting the error

- Text is exactly `Field is required` — **assert equality, not visibility**: the Scopes
  field renders a permanent unrelated `Enter scopes separated by commas or spaces` helper
  in the same `.MuiFormHelperText-root` family, so a loose visibility check passes on it.
- The node is **unmounted** when the field becomes valid → `to_have_count(0)`, not
  `not_to_be_visible()`.
- Errors appear only **after** a Save click (`onClickSave` → `setShowValidation(true)`),
  never while a required field merely sits empty.

Related: [[save_button_gating_is_dirty_based]]
