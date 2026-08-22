---
name: Review-finding meta-tests in tests/unit are doc-lint, not coverage
description: A unit test asserting an AFS's markdown prose reds the suite for non-product reasons; block it, keep the AFS edit alone
type: feedback
aliases: [meta test, AFS lint test, doc-sync test, tests/unit prose assertion]
tags: [area/review, type/anti-pattern]
created: 2026-08-22
updated: 2026-08-22
---

## The pattern

Fix rounds on the credentials batch started shipping *meta-tests* under
`automation/tests/unit/` that pin a review finding instead of a product
behaviour:

- `test_credentials_console_filters_scope.py` (ELITEA-1966/1973) — asserts a
  spec module no longer exposes `_is_known_518_warning` and that the surviving
  filter stays URL-scoped. Tests **executable code**; defensible.
- `test_afs_1968_dropped_assertion_consistency.py` (ELITEA-1968) — regexes an
  **AFS markdown document** for the phrase `**Dropped Axis-2 addition
  (declared).**` and scans its table rows for `{{secret.` claims. Tests
  **prose**; not defensible.

## Why the prose variant blocks

1. It reds the pytest suite for a documentation edit — reword the declaration,
   rename or move the AFS, and the run goes red with no product cause. The
   merge gate cannot classify that red: it is not sanctioned-RED (no open
   defect), so it just blocks.
2. Its inverse branch is a trap: delete the declaration and the test now
   *demands* a coverage row claiming the assertion.
3. It appears in no AFS Coverage Map — an undeclared artifact, which the
   reviewer contract's AFS↔implementation sync check catches.
4. Second use of an unshaped pattern is `CHANGES_REQUESTED` per
   `.agents/role-overrides.md` § declared-improvisation protocol (limit 3),
   not a precedent to extend.

## The rule

A round-1 finding of the form "the AFS over-claims an assertion" is closed by
**editing the AFS** (and the spec docstring / allure labels that repeat it).
Nothing else is owed. If the team genuinely wants AFS/spec doc-lint, it is a
canon `question` card and a lint step outside the product test suite — never a
`tests/unit` test.

Related: [[afs_claims_need_full_sweep_and_grep]]
