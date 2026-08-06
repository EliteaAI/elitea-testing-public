---
name: Max Context Tokens rejects non-numeric/negative via keystroke filtering (settings-memory)
description: Onchange strips non-digits AND minus sign before Formik ever sees them — not a submit-time rejection
type: project
---

`/settings/memory` → Context Management → Max Context Tokens (ELITEA-2391
session, 2026-08-06). The mechanism behind "does not accept non-numeric or
negative values" is a **keystroke-level filter**, not submit-time Yup
rejection of the raw string:

`handleConvertToNumberChange`
(`EliteaUI/src/[fsd]/widgets/context-budget/lib/validation.js:169-173`) runs
`value.replace(/[^0-9]/g, '')` on every keystroke before `setFieldValue`.
**This exact function is shared with the sibling Target Summary Tokens
field** (`MemorySummarization.jsx:34` calls the same helper) — same trap
applies to both.

- Typing `"abc"` → zero digits survive → field ends up **empty**, not
  showing "abc". `aria-invalid="true"`, helper text "This field is
  required" (required when `context_enabled` is true).
- Typing `"-100"` → the minus sign is stripped the same as a letter → field
  shows **`"100"`, not `"-100"`**. A literal negative number can never
  reach Formik state for either field. `100` then fails
  `VALIDATION_LIMITS.MAX_CONTEXT_TOKENS.MIN = 1000` → "Max tokens must be
  at least 1,000". There is no separate "negative rejected" message
  anywhere — a typed negative always surfaces as a min-boundary error on
  whatever digits survive.
- Neither invalid case fires an autosave PUT (same
  `validateForm()`-gates-`submitForm()` mechanism as Target Summary
  Tokens — see `settings_memory_target_summary_tokens_validation.md`).
- **Also contradicts #1129** the same way Target Summary Tokens does: a
  valid value (`64000`) autosaved successfully this session.

**Automation implication**: the pre-existing `set_max_context_tokens(value:
int)` setter cannot drive this case — it forces `str(int)` (can't type
"abc") and unconditionally calls `wait_for_autosave()` (best-effort,
doesn't prove PUT-vs-no-PUT). Needed a sibling method,
`type_max_context_tokens_raw(text: str)`, mirroring the
`set_target_summary_tokens()` shape added for ELITEA-2378 (types raw, no
wait baked in, caller wraps with `page.expect_response`/a bounded
absence-listener). Don't touch the existing setter — ELITEA-2374's test
still uses it unchanged.

Filed EliteaAI/elitea-testing-public#1247 — case steps 2/4's literal
Expected Result text implies the raw invalid string is accepted/displayed
as typed ("action completes", "field accepts and displays the entered
value"); live behaviour is the filter above. Title/Objective and steps 3/5
("verify rejected") are accurate.
