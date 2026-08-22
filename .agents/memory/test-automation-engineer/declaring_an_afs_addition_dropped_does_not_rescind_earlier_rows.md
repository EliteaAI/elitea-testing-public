---
name: Declaring an AFS addition dropped does not rescind the earlier rows
description: A "DROPPED" note in Coverage Map Axis 2 leaves Test Steps + Axis 1 still claiming the assertion — sweep every table, and the spec's own prose too
type: feedback
aliases: [dropped assertion, AFS over-claim, coverage over-claim, doc-sync drop, axis-2 dropped]
tags: [area/doc-sync, type/review-finding]
created: 2026-08-22
updated: 2026-08-22
---

## What happened

ELITEA-1968 (PR #1670): an Axis-2 addition — assert the secret field stores
`{{secret.<name>}}` behind the displayed name — had no compliant handle (MUI's
`MuiSelect-nativeInput` gets no testid; `SingleSelect`'s `inputProps` do not
reach it) and was correctly dropped rather than shipped as a raw
`.locator("input")`. The drop was declared, in detail, in § Coverage Map
Axis 2.

It still failed review, because **the declaration was added and nothing else was
removed.** Three earlier places kept telling the reader it was asserted:

- § Test Steps row 5 — "the underlying field value is `{{secret.auth_token}}`"
- § Coverage Map Axis 1, Step 5 — "Asserted where: … value `{{secret.auth_token}}`"
- § Expected Results — "…while storing the `{{secret.<name>}}` template"

And the reviewer did not even see the worst copy: the **spec's own module
docstring** listed the stored template inside "Every asserted value … is
produced by the live product", and the Step-5 allure label repeated it. A
reader of the test — not the AFS — would have been misled hardest.

## The rule

Dropping an assertion is a **sweep**, not a note. Grep the dropped observable's
token across the AFS *and* the spec, and fix every hit: steps table, coverage
ledger, expected results, module docstring, step labels. The declaration is the
last edit, not the only one.

The asymmetry that makes this a repeat offender: adding an assertion touches one
place (the code); dropping one touches five, and only the code half is visible
in a diff review of the test.

## Pinning it

`automation/tests/unit/test_afs_1968_dropped_assertion_consistency.py` pins the
pair bidirectionally — while the AFS says DROPPED, no § Test Steps / § Coverage
Map row may present the token as asserted, and the spec's executable code may
not reference it either. Scoping matters: § Concrete Handles legitimately
carries `{{secret.<name>}}` inside the option's own **testid**
(`select-option-{{secret.<name>}}`), so the guard reads the coverage tables
only. Restoring the assertion for real means deleting the declaration, which
turns both halves of the guard off together.

Related: [[secret_field_vault_dropdown]]
