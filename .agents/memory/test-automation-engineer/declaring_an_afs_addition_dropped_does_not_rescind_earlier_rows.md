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

## Do NOT pin it with a unit test (round-2 blocker)

The obvious follow-up — a `tests/unit/` guard pinning the AFS and the spec to
each other — was written in round 1 and **blocked in round 2**: it regexed the
AFS markdown for the literal phrase `**Dropped Axis-2 addition (declared).**`
and scanned its table rows. That is **doc-lint, not coverage**:

- a reword, rename or move of the AFS reds the pytest suite with no product
  cause, and the merge gate cannot classify that red (not sanctioned-RED — no
  open defect — so it simply blocks);
- the inverse branch is a trap: delete the declaration and the test starts
  *demanding* a coverage row claiming the assertion;
- it appears in no AFS Coverage Map, so it is an undeclared artifact.

**The finding "the AFS over-claims an assertion" is closed by editing the AFS**
(plus the spec docstring / allure labels that repeat it). Nothing else is owed.
Real AFS/spec doc-lint, if the team wants it, is a canon `question` card and a
lint step outside the product test suite — never a `tests/unit` test.

Related: [[secret_field_vault_dropdown]]
