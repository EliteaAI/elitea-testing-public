---
name: Asserting a refused interaction on a disabled field
description: How to prove "no input is accepted" honestly — short-budget pytest.raises on click, plus the unchanged value; type()/press() do not raise
type: feedback
aliases: [refused click, disabled input assertion, read-only field test, is_editable, is_disabled]
tags: [area/playwright, type/technique]
created: 2026-08-23
updated: 2026-08-23
---

## The shape

A case step like *"attempt to click into the field and type — no cursor appears, no input
is accepted"* (ELITEA-1816, artifacts bucket Edit form) has three separate observables,
and only one of them actually proves the claim:

```python
with pytest.raises(PlaywrightTimeoutError):
    page_obj.field.click(timeout=3_000)      # actionability check refuses a disabled el
# keystrokes anyway — wrapped, because the outcome is NOT the assertion
try:
    page_obj.field.type("XYZ", timeout=3_000)
except PlaywrightTimeoutError:
    pass
assert page_obj.field.input_value() == expected   # <- THIS is the proof
```

- **Short budget (2-3 s) is load-bearing.** The refusal is observed AS a timeout; a 30 s
  budget makes a passing test look hung and costs a minute per run.
- **`Locator.type()` / `press()` on a disabled input do NOT raise** — confirmed live
  2026-08-23 on Elitea's bucket Edit form. They silently do nothing, so their outcome
  cannot be the assertion. The unchanged `input_value()` is.
- **Assert BOTH `is_editable() is False` and `is_disabled() is True`**, and take an
  ENABLED reading of the same field in the create/edit-off state first. Without that
  control, "disabled in edit mode" also passes on a field that is always disabled.
- Products commonly implement "read-only" as `disabled`, not `readOnly` — do not hunt a
  `readonly` attribute the DOM does not have; assert the state, not the attribute name.

Related: [[afs_issue_tms_link_filename_verify_before_commit]]
