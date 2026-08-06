---
name: Target Summary Tokens min/max validation (settings-memory)
description: Yup-validated 100-4096 range on /settings/memory's Target Summary Tokens; no Save button; #1129 may not reproduce for this field
type: project
---

`/settings/memory` → Automatic Summarization → Target Summary Tokens has real
client-side Yup validation, confirmed live (ELITEA-2378 session, 2026-08-06):
`VALIDATION_LIMITS.MAX_TOKENS = { MIN: 100, MAX: 4096 }`
(`EliteaUI/src/[fsd]/widgets/context-budget/lib/constants.js`), consumed by
`profileValidationSchema` in
`src/[fsd]/features/settings/lib/helpers/profile.helpers.js` — the schema that
actually governs this page (there's a *second*, differently-wired copy of the
same limits, `contextStrategyValidationSchema` in
`context-budget/lib/validation.js`, used by the unrelated chat-side Context
Budget widget — don't confuse the two when grepping).

- Out-of-range value (99, 4097) → `aria-invalid="true"` on the
  already-testid'd `target-summary-tokens-input` + a helper-text error
  message ("Target tokens must be at least 100" / "...cannot exceed 4,096").
  No autosave PUT fires — `useFormikAutoSaveOnBlur` gates `submitForm()` on
  `validateForm()` passing.
- In-range value → no error, PUT `/api/v2/social/author/` fires and echoes
  the new value in `default_summarization.target_summary_tokens`.
- The error `<p>` (MUI `FormHelperText`) has no testid. Assert the boundary
  via the input's `aria-invalid` attribute instead — that's a standard ARIA
  attribute on a stable testid'd element, compliant with the state-via-
  data-attribute rule (not a state-switched testid). Message-text assertion
  needs a new testid (`FormHelperTextProps={{ 'data-testid': ... }}` on the
  `StyledInputEnhancer` — plumbing confirmed via `InputBase.jsx`'s
  `{...leftProps}` spread onto `MuiTextField`).
- **This page has NO Save button anywhere** — full autosave-on-blur. A case
  whose text says "Save is enabled" is stale; the automated equivalent is
  "no validation error + the autosave PUT fires/persists". Filed
  EliteaAI/elitea-testing-public#1244 for this exact wording drift (distinct
  from #1238, which is about the route + grayed-out-vs-unmount drift).
- **Contradicts open bug #1129** ("typed numeric fields never autosave"):
  typing a VALID value into Target Summary Tokens specifically and blurring
  DID autosave successfully this session (confirmed via response-body value
  echo). Commented evidence on #1129 rather than closing it — could be
  field-specific (Max Context Tokens / Preserve Recent Messages untested
  this session) or a partial fix landed since #1129 was filed. Don't assume
  #1129 blocks a Target Summary Tokens autosave assertion without
  re-checking live first.
