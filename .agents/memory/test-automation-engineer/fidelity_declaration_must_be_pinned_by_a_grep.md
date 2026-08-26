---
name: A Fidelity Declaration is prose until a unit test pins it
description: "Never asserted" clauses drift silently — pin them with an AST guard, the way ELITEA-2275 had to
type: feedback
aliases: [fidelity declaration drift, seeded text never asserted, SEED_CONTENT assertion, declaration grep]
tags: [area/fidelity, type/review-finding]
created: 2026-08-26
updated: 2026-08-26
---

## What happened

ELITEA-2275's spec docstring and its AFS § Fidelity Declaration both promised
*"the seeded TEXT is never asserted"* — while the spec's own final assertion was

```python
expect(context_page.editor_lines()).to_have_text([SEED_CONTENT])
```

reading the case's observable straight off the string the test wrote. The AFS
step 6 specified a third thing again ("the typed character is absent"). Three
artifacts, three different claims, everything green, two gates passed.

## Why it survived

A declaration is *prose*. Nothing executes it. The reviewer's mechanical
provenance grep (`page.route|route.fulfill|monkeypatch|\.evaluate\(`) does not
catch this shape at all — there is no substitution API in the diff, just a
module constant used as an assertion operand. So the honest-looking declaration
actually *lowered* scrutiny.

## The rule I now apply

**When a spec declares "X is never asserted", ship the grep that proves it in
the same PR.** The guard is cheap — parse the spec with `ast`, collect every
`Name` load of the constant, subtract the ones sitting inside the seeding call,
assert the remainder is empty. See
`automation/tests/unit/test_project_context_seed_text_never_asserted.py`.

Red-green it properly: re-introduce the offending assertion, watch the guard
fail on that exact line, restore. Otherwise the guard is prose too.

## The fix pattern itself

Read the baseline **off the product** before the edit and compare against that
(`get_editor_lines()` → `expect(...).to_have_text(baseline_lines)`), which is
what ELITEA-2274 already did in the same directory. Two guards keep the
comparison from going vacuous: the baseline is non-empty, and it does not
already contain the character the test is about to type.

Related: [[fixture_that_writes_two_fields_declares_only_one]] ·
[[repairing_a_neighbour_spec_leaves_its_afs_stale]]
