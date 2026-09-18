---
name: Toolkit credential select aria-invalid producer
description: aria-invalid on toolkit-credential-select-<type>-combobox and the credential-warning-banner share ONE producer (toolErrors)
type: reference
---

Verified at source 2026-09-18 (EliteaUI automation/testids @ dd99e48c, 0 behind main), reviewing #2349 / ELITEA-1183.

**Chain for the row-level "invalid credential" flag on the toolkit detail page:**

1. `ToolkitForm.jsx:447` — `next[key] = credentialMessage` writes the credential-validation
   message (e.g. "Authentication failed: …") into `toolErrors[<type>_configuration]`.
2. `ToolBaseProperty.jsx:95` — `toastError = isIntegerConstraintError || …`; the
   `isIntegerConstraintError` name is misleading: it is `typeof toolErrors[k] === 'string'`,
   so ANY string error (including the auth message) makes it truthy.
3. `<CredentialsSelect error={!!toastError} helperText={errorText}>` → `hasSelectError`
   (`error || showMismatchFooter`) → `SingleSelect` `<FormControl error>`.
4. MUI `SelectInput.js:481` renders `"aria-invalid": error ? 'true' : undefined` on the
   `role="combobox"` div — the SAME div that carries `SelectDisplayProps` `data-testid=
   "<dataTestId>-combobox"`. So `[data-testid="toolkit-credential-select-jira-combobox"]
   [aria-invalid="true"]` is a compliant, honestly-produced state filter.
5. The `credential-warning-banner` the tests read (Step 5) is `SingleSelect.jsx:684`, gated on
   the same `error && helperText` — the only BannerMessage on this surface.

**Consequences for review:** an `aria-invalid` assertion here is honest and can fail, but it is
NOT independent evidence of the case's "distinct icon" — it shares its producer with the banner.
The distinct icon (`credential-status-indicator`) renders since EL-6632 (EliteaAI/EliteaUI@f73c22f7)
only on the credential's DROPDOWN OPTION (`isInvalid && !isSelected`); the displayed value is
`cloneElement(label, { isSelected: true })`. A page-level `credential-status-indicator` locator on a
closed dropdown matches nothing → any absence assertion on it is vacuous.

**Playwright footgun that applies to `wait_for_credential_select_invalid_state(invalid=False)`:**
negated matchers (`not_to_have_attribute`) PASS when the locator resolves to no element. Safe only
when the next statement waits for the element positively (the repair's `open_credential_dropdown`
does). Prefer a positive visibility wait before a negated attribute assertion.
