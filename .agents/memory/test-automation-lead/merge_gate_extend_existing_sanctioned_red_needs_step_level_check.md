---
name: Merge gate on extend-existing sanctioned-RED PRs needs a step-level check, not just the overall result
description: when the covering test of an extend-existing PR already carries a sanctioned-RED known defect, the orchestrator's 3x independent live-run gate must additionally read the Allure step-level JSON to confirm the newly-appended steps pass — the overall pytest result stays "failed" (soft-assert aggregation) even when every new step is 100% green
type: feedback
---

Discovered during ELITEA-1827 (issue #240, PR #658) — an `extend-existing` AFS
that appended 8 new steps to the already-merged ELITEA-1824 test
(`test_upload_via_three_options_and_verify_selection`). That covering test
already carries a sanctioned-RED known defect (#649, `expect.soft()`-asserted
at pre-existing Steps 30-32). The new steps 47-54 don't touch that code path at
all, but the test's overall pytest status is still `failed` on every run
because `expect.soft()` failures get aggregated and re-raised at the end of the
test body, regardless of what ran cleanly afterward.

**What this means for the gate, concretely:** running `pytest <node-id>` 3x and
seeing `1 failed` 3/3 with an identical error message is necessary but NOT
sufficient to confirm the new steps are actually green — that overall RED
could theoretically be masking a real regression in the appended steps if one
happened to also fail (both would show as one aggregated `failed` result;
pytest's own output doesn't distinguish "old failure only" from "old failure +
new failure" at the summary line).

**The check that actually distinguishes them:** read
`automation/reports/allure-results/*result.json` for the just-run test and
verify each new step's own `status` field is `passed` individually —
```python
import json
d = json.load(open(<latest-result.json>))
for step in d['steps']:
    print(step['status'], step['name'])
```
Only the pre-existing/known-defect step(s) should show anything other than
`passed`; every one of the newly-appended steps must show `passed` by name, in
EVERY one of the 3 gate runs — not just the implementer's or reviewer's report
of it. This is a new item for the orchestrator's own 3x gate checklist
specifically for `extend-existing` PRs landing on an already sanctioned-RED
covering test — the generic "3/3 identical failure = sanctioned" check from
`.agents/testing.md` § Merge gate is still correct, but on an extension it
needs this per-step corroboration too, done by the orchestrator independently,
not inherited from the implementer/reviewer's own runs.
