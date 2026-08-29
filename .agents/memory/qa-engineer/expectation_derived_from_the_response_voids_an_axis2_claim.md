---
name: An expectation derived from the product's own response can void the Axis-2 claim it is supposed to prove
description: Response-derived expected values assert DOM/API agreement only — they cannot fail on the behaviour the AFS says they pin.
type: feedback
aliases: [derived expectation, response-derived assertion, axis-2 tautology, oracle-derived expected value]
tags: [area/review, type/assertion-strength]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

`.agents/testing.md` § Fidelity policy rightly pushes analysts and implementers to
**capture the real response and assert the UI against it** instead of hand-writing
payloads. That is correct for *carry-through* checks. It quietly stops being correct
the moment the derived value IS the behaviour being claimed.

Worked example — `automation/tests/ui/settings/test_vector_storage_create.py`
(ELITEA-2399, PR #1989). The AFS § Implementation amendment states the live contract
"creating a Vector Storage configuration ASSIGNS it as the section default" and says
step 9 asserts `aria-selected="true"` on the new option. The code instead computes:

```python
expect(option).to_have_attribute("aria-selected", "true" if persisted_default == new_title else "false")
expect(combobox).to_have_text(persisted_default)      # persisted_default read from the POST-create GET
```

Both branches pass. If the product stopped reassigning the default, the spec goes
green on the `"false"` branch — the exact Axis-2 claim the AFS says it pins can never
fail. What it *does* prove is DOM ⟷ API agreement, which is a real (weaker) check.

## The review check

When an expected value comes from the product's own response, ask which of the two it
is, and hold the AFS to the same answer:

- **Carry-through** ("the UI rendered what the API returned") — derived is right, and
  the AFS should say *agreement*, not a behaviour.
- **Behaviour** ("creating one makes it the default", "the default is exclusive") —
  the expectation must be a **constant** in the test, or a separate assertion on the
  response itself (`assert body["default_model_name"] == new_title`). Deriving it makes
  the claim unfalsifiable.

A conditional expectation (`"true" if X else "false"`) is the tell — grep added diffs
for `to_have_attribute(..., ... if ... else ...)` and for expected values that are
locals read out of a captured response.

Related: [[afs_axis2_claim_needs_grep_not_just_row_presence]] ·
[[conditional_assertion_that_never_fires]] · [[vacuous_api_oracle_toolkit_listing]]
