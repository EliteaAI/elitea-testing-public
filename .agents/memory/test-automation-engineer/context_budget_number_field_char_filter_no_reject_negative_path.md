---
name: Context budget number fields strip invalid keystrokes, never reject them
description: handleConvertToNumberChange filters non-digits+minus before Formik state — no literal negative ever exists to "reject"
type: feedback
---

Surface: `/settings/memory` numeric fields (Max Context Tokens, Target Summary
Tokens) — both consume the SAME onChange handler,
`handleConvertToNumberChange` (`src/[fsd]/widgets/context-budget/lib/validation.js:169-173`),
which runs `value.replace(/[^0-9]/g, '')` on EVERY keystroke before
`setFieldValue`. This has one durable consequence any AFS/case-text framed
as "rejects non-numeric/negative input" will get wrong if read literally:

- Typing `"abc"` never lands in the field as typed — it reduces to `""`
  (zero digits), which then fails the `required` rule.
- Typing `"-100"` never lands as `-100` — the minus sign is stripped
  identically to a letter, leaving `"100"`, which then fails the schema's
  `min()` boundary (1000 for Max Context Tokens, 100 for Target Summary
  Tokens).

**There is no separate "reject negative" error message anywhere in this
schema** — a literal negative number structurally cannot exist in Formik
state for either field, only its unsigned digits can. Don't go looking for
a negative-specific validation message; the correct assertion is always the
min-boundary error, plus the field's ACTUAL DISPLAYED VALUE (empty / stripped
digits) — that's the concrete, checkable proof of "does not accept", not
just "shows an error".

Test pattern: `expect(field).to_have_value("")` / `to_have_value("100")` +
`aria-invalid="true"` + the `asserting_absence_of_autosave_put_on_client_validation_failure.md`
no-PUT-fires check. Page-object method needed: a raw-`str` typing method
(sibling of `set_max_context_tokens`/`set_target_summary_tokens`, NOT a
modification to either — their `int`-typed signatures can't type `"abc"`)
that does NOT bake in `wait_for_autosave()`.

Cases confirmed against: ELITEA-2378 (Target Summary Tokens range),
ELITEA-2391 (Max Context Tokens non-numeric/negative). Likely applies to
any future case on Preserve Recent Messages too (same field family, not yet
verified live).
