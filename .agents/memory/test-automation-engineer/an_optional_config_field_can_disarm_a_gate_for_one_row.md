---
name: An optional per-row config field silently disarms the gate for rows that lack it
description: A parameterized suite's "optional" oracle field must be paired with a skip + a static invariant, or an unfilled row reports green on a broken subject
type: feedback
---

Pattern, found by a reviewer on ELITEA-1140/#1817 and worth checking on any
parameterized suite:

An oracle keyed off an **optional** `ToolkitConfig` field
(`tool_output_success_pattern: str = ""`) looks safe because the populated rows
are strict. It is not: a row that has neither the field **nor** a `skip_reason`
runs with the gate silently disarmed. Confluence sat in exactly that hole — wired
into three CI workflows — so a 401 passed Tier 1 (a frame exists, output
non-empty) and Tier 3 (the model narrates the failure using the very keywords the
test looks for). Net: GREEN on a broken toolkit — worse than the false-RED being
fixed.

`logger.warning` + assert-nothing is NOT the fix. **A warning in a CI log is not a
gate.** Two things are:

1. **Runtime:** `pytest.skip(...)` naming the missing capture, so the row reports
   "not verified" instead of "verified good". This is not defect masking — it
   masks no product defect and hides no red; it converts a silent false-green
   into a visible gap.
2. **Static:** a unit test asserting every row is classifiable —
   `[k for k, c in CONFIGS.items() if not c.skip_reason and not c.oracle_field] == []`
   — so a newly added row must choose *capture it* or *say why not* at authoring
   time, not discover the hole in production.

Generalises to: any optional field the pass/fail verdict depends on.
