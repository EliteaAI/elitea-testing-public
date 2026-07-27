---
name: Templated promotability row can mask a wrong literal testid
description: A "${k}"-templated promotability summary row is not a verification of every field's actual literal testid — check each LocatorDescriptor's exact string individually
type: feedback
---

## What happened (issue #68, ELITEA-1975, PR #527)

The closure record's promotability table summarized a whole family of
dynamic testids as one row:

```
toolkit-field-${k}-input          main:no  testids:YES
```

This is true for `k=label`, `k=base_url`, `k=username`. But the actual
`LocatorDescriptor` coded for `api_key_input` used a DIFFERENT literal
string that doesn't fit the template at all:

```python
api_key_input = LocatorDescriptor(testid="toolkit-field-api_key-input-field", ...)
```

`toolkit-field-api_key-input-field` (with a trailing `-field`) does not
exist anywhere in EliteaUI, on `main` or `automation/testids`. Tracing the
real component wiring (`SecretManagementInput.jsx`'s `inputProps={{
'data-testid': testId }}`, fed by `ToolBaseProperty.jsx`'s
`testId={`toolkit-field-${k}-input`}`) showed the real rendered testid is
`toolkit-field-api_key-input` — no `-field` suffix. That suffix pattern
belongs to an unrelated Skill-form convention
(`skill-name-input-field`, `skill-description-input-field`, etc.) the
implementer or analyst apparently cross-pollinated from.

## Why the collapsed-row check missed it

Checking "does `toolkit-field-${k}-input` exist for k in {this test's
fields}" as ONE grep/row implicitly assumes every field actually uses that
exact template. It doesn't verify each field's own `LocatorDescriptor`
literal against the template — a single typo'd/mismatched field hides
inside a row that's mostly-true for its siblings.

## Rule going forward

When re-deriving (or trusting) a promotability table for a dynamic/templated
testid family:
1. Pull the LITERAL string coded in each `LocatorDescriptor`/class constant
   the test actually uses — not the template shape.
2. Grep ground truth (`main` + `automation/testids`, fresh-fetched) for
   each literal string individually, even if they "obviously" belong to
   the same template family as a sibling that already checked out.
3. A collapsed one-row summary is fine for the CLOSURE RECORD's
   presentation, but the verification that produced it must have checked
   every literal, not just the template pattern.

This is a distinct failure mode from `promotability_grep_false_negative.md`
(which is about grep TECHNIQUE missing a real match) — here the grep
technique was fine, the underlying claim ("this field uses the template")
was simply false and never individually checked.
