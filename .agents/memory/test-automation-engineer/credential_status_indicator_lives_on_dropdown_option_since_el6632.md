---
name: credential-status-indicator lives on the dropdown OPTION since EL-6632
description: The selected credential value no longer renders the attention icon — scope the testid under the option; page-level match is vacuous
type: project
aliases: [credential-status-indicator, EL-6632, CredentialOptionLabel isSelected, credential warning banner tooltip overlap]
tags: [area/toolkits, area/credentials, type/ui-drift]
created: 2026-09-18
updated: 2026-09-18
---

## What changed (EliteaAI/EliteaUI@f73c22f7, PR #1036, hotfix/EL-6632/credential-select)

`CredentialOptionLabel.jsx` renders its attention icon (`data-testid="credential-status-indicator"`,
aria-label = Tooltip title = the validation message) only when `isInvalid && !isSelected`, and
`CredentialsSelect.jsx` `cloneElement`s the SELECTED value with `isSelected: true`. So on the
toolkit detail page the icon exists ONLY inside the open dropdown, on the credential's own option.
The selected row communicates the state via the combobox `aria-invalid="true"` + warning-orange
`Mui-error` underline; the `credential-warning-banner` (BannerMessage, variant `warning`) carries
an icon (no testid of its own) + tooltip = message.

Verified live 2026-09-18 on localhost:5173 (dd99e48c) and dev.elitea.ai. Repaired in
`ToolkitDetailPage` (`CREDENTIAL_STATUS_INDICATOR`, `get_saved_option_status_indicator` family,
`wait_for_credential_select_invalid_state`, `close_credential_dropdown`) — ELITEA-1183 / #2349.

## Traps

- **A page-level `credential-status-indicator` locator now matches nothing on a closed
  dropdown**, so `not_to_be_visible()` / `to_have_count(0)` on it passes vacuously. Scope it
  under `select-option-<json>` and wait for the option to be visible FIRST.
- **Hovering `credential-warning-banner` opens a top-placed MUI tooltip that covers the
  combobox** — a subsequent `click()` on the select times out with "subtree intercepts pointer
  events". Move the pointer elsewhere (or never hover the banner) before opening the dropdown.
- Reload / Open-in-new-tab buttons still render on the selected value (unchanged).

Related: [[testid_lands_on_mui_wrapper_not_input]] · [[mui_menu_stays_open_backdrop_intercepts_outside_clicks]]
