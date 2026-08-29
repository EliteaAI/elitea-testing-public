---
name: Sanctioned-RED specs must not hard-assert the defect symptom
description: In a known-defect spec, assert the CORRECT behaviour softly; a hard assert pinning today's broken state flips to a false RED when the fix ships
type: feedback
aliases: [sanctioned-red hard assert, defect symptom assertion, known defect axis-2]
tags: [area/review, type/anti-pattern]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

A sanctioned-RED spec (`.agents/testing.md` § Merge gate → *Analysis-time entry*)
writes the case's own expectations as `expect.soft(...)` + `# Known defect: #N`,
so it flips green the day the product is fixed.

The trap is the *supporting* Axis-2 assertion an AFS often asks for alongside it —
"record that there is no inline validation either, so the fix can be judged
complete". Written as a HARD assertion it pins **today's defective state**:

```python
expect(form.field_helper_text("name")).to_have_count(0)   # no inline validation TODAY
```

The moment the defect is fixed, the soft asserts go green and this one goes RED —
a hard, uncaught failure that is not a member of the case's closed defect set, so
the merge gate blocks and the failure reads like a brand-new regression.

## What to do instead

- Assert only the correct expected behaviour, softly, with the defect link; OR
- log the supporting observation (`logger.info`) instead of asserting it; OR
- if it really must be an assertion, make it `expect.soft` too and name it as part
  of the SAME closed defect signature, so the gate's expected signature is one set.

At minimum the site carries an inline "revisit when #N closes" comment — that
mitigates but does not remove the mis-signal.

Seen: ELITEA-2408 (`test_llm_model_required_field_validation.py`, PR #1986),
where the AFS Axis-2 row authored the absence assertion and the implementer
shipped it hard between two correct soft asserts.

Related: [[credential_form_goto_pitfalls]]
