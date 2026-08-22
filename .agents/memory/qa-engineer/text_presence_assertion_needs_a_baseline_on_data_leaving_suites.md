---
name: Text-presence assertions need a baseline on suites that leave their data behind
description: to_have_count(1) on "my message is still there" is green on run 1 and red on run 2 — check for it in review, the implementer's single run cannot see it
type: feedback
aliases: [baseline delta text assertion, gate run 2 flake, has_text count 1, leftover test data assertion]
tags: [area/review, type/flake]
created: 2026-08-22
updated: 2026-08-22
---

## The shape

On any surface where the suite deliberately leaves its data behind (support-assistant
chat, any conversation the widget restores on open), an assertion of the form

```python
expect(item_with_text(MSG)).to_have_count(1)   # "my message is still rendered"
```

is **green on the implementer's first run and red from the second onward** — the previous
run's copy of `MSG` is already in the restored conversation. It survives the implementer's
gate (one run) and dies in the lead's 3× merge gate, which is the most expensive place to
find it.

## Review action

When a spec asserts that a *specific string* it sent is present, check whether the surface
has cleanup. No cleanup ⇒ the assertion must be a **delta**: take
`baseline = locator_with_text(MSG).count()` right after the surface is opened and assert
`baseline + 1`. Same strength, deterministic. Counts (items, buttons) usually get this
treatment already; the *text* assertion is the one that gets forgotten because it reads
like an identity check rather than a count.

Worked example done right: ELITEA-2422
(`automation/tests/ui/support_assistant/test_support_assistant_navigation_persistence.py`)
takes a third baseline `baseline_first_message` alongside items/copy-buttons.
Surface digest quirk 24 in `test-specs/support-assistant/_surface.md` records the rule.

Related: [[passing_assertion_may_prove_nothing]]
