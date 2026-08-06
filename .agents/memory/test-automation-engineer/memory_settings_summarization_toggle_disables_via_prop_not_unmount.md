---
name: Memory settings — Automatic Summarization toggle disables via disabled prop, not unmount
description: On /settings/memory, the Automatic Summarization toggle disables its OWN fields via `disabled` prop; only the PARENT Context Management toggle unmounts.
type: reference
---

`/settings/memory` → Context Management accordion has TWO toggles with
DIFFERENT disable mechanisms for their children — don't assume the whole
page uses one pattern:

- **Context Management toggle** (parent) → conditional UNMOUNT of everything
  below it (`{isEnabled && (...)}` in `MemoryContextManagement.jsx`). Assert
  absence (`to_have_count(0)`) when OFF. Documented in
  `test-specs/settings-user-profile/l3_context-management-toggle-enables-disables-fields_ELITEA-2374.md`.
- **Automatic Summarization toggle** (nested child, `MemorySummarization.jsx`)
  → real `disabled` PROP on its own two children (Summarization Instructions
  textarea, Target Summary Tokens input): `isSummarizationDisabled =
  !values.context_enabled || !values.enable_summarization`. Fields STAY
  MOUNTED, just `disabled`. Assert `to_be_disabled()` / `to_be_enabled()`,
  never `to_have_count(0)`, for this toggle's own children.

Confirmed live (ELITEA-2377 session, 2026-08-06) via DOM inspection after
clicking `automatic-summarization-toggle` — snapshot showed
`textbox [disabled]` for both fields, not absence. Both toggles share the
same `PUT /api/v2/social/author/` autosave endpoint though — that part IS
uniform across the page.

Testids added this session (on `automation/testids` only, not yet `main`):
`summarization-instructions-textarea`, `target-summary-tokens-input`
(`EliteaAI/EliteaUI@be73caea`). `target-summary-tokens-input` is distinct
from the differently-scoped `context-modal-target-summary-tokens-input` in
the unrelated chat-side Context Budget widget (`ContextStrategySummarization.jsx`)
— don't confuse the two when greeping for "target summary tokens".
