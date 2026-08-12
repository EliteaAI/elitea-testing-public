---
name: ELITEA-1883 — variable row order correction + #524 fixture-vs-product nuance
description: Variable rows render alphabetically by name, not first-appearance order (corrects a coincidental claim in the ELITEA-1884 AFS); #524's product/UI fix is real but AgentAPI.create_agent() independently hardcodes an invalid llm_settings combo — filed separately as #563
type: feedback
---

## What happened

Analyzing ELITEA-1883 ("Add two variables and verify they persist after reload", issue #87),
typed `{{MY_VAR}} and {{API_URL}}` into a fresh agent's Instructions field. `MY_VAR` appears first
in the text, but the Variables section rendered `agent-variable-row-API_URL` before
`agent-variable-row-MY_VAR` — confirmed via `document.querySelectorAll('[data-testid^="agent-variable-row-"]')`
and cross-checked against the server response's `variables` array (same order). **Rows render
alphabetically by variable name, not in first-appearance-in-text order.**

The ELITEA-1884 AFS (`test-specs/agents/l3_remove-variable-verify-removal-persists_ELITEA-1884.md`)
claims the opposite ("Order of variable rows matches first-appearance order in the instructions
text") — but its own test data (`department`, `tone`) happens to also be alphabetically ordered,
so that claim was never actually distinguished from the alphabetical explanation. Corrected in the
ELITEA-1883 AFS's Axis 2. **If `test_agent_remove_variable.py` or any other implementation asserts
literal appearance-order, it happens to pass by coincidence — flag for review if touched again.**

## #524 vs #563 — read carefully before trusting "verified fixed" comments

This run was tasked with re-verifying live whether #524 (`temperature` + `reasoning_effort`
conflict on agent create) was actually fixed, per a same-morning "Verified fixed on dev" comment
on the ticket. Re-confirmed **two distinct things that must not be conflated**:

1. **Product/UI fix is real.** `/agents/create` with Name+Description only now sends
   `temperature: null` and gets `201`. This is a genuine, verified fix.
2. **The pytest `agent_id` fixture is still broken**, but for a *different* reason than "the
   backend regressed" — `AgentAPI.create_agent()` (`automation/api/client.py:366`) independently
   hardcodes `"temperature": 0.6, "reasoning_effort": "medium"`, an invalid combination the
   backend correctly rejects. This was never actually caused by the same backend defect as #524
   — it's our own test fixture sending bad data. Filed as a separate test-infra bug,
   [#563](https://github.com/EliteaAI/elitea-testing-public/issues/563), rather than reopening
   #524. Posted a clarifying comment on #524 distinguishing the two.

**Takeaway**: when a "verified fixed" comment on a defect ticket only exercised the UI form (not
the API-level test fixture that shares the same nominal root cause), don't assume the fixture path
is also fixed — the UI's default payload and the fixture's hardcoded payload can diverge even
though they hit the "same" validator error message. Always re-run the actual fixture, not just the
UI flow the fix was verified against.

## Established workaround (still valid, now proven a 4th time)

`AgentAPI.create_agent_full()` with an explicit payload setting `reasoning_effort: "none"` and
omitting `temperature` entirely — used successfully in ELITEA-1884, ELITEA-1888, ELITEA-1872, and
now ELITEA-1883's exploration (via direct UI create + manual cleanup, since this run predated
having a fixture wired up). Continue using this pattern for any case needing a fresh agent until
#563 is fixed (and until someone promotes the workaround into the shared `agent_id` fixture
itself, flagged again in this AFS as in prior ones).
