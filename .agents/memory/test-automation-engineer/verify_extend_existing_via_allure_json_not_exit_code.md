---
name: Verify extend-existing insertions via allure-results JSON per-step status, not the overall pytest exit code
description: When a covering test carries an existing sanctioned-RED expect.soft() known defect, the overall test result is FAILED regardless of whether your new inserted assertions passed. Don't conflate "test exited red" with "my new assertions are broken" — read reports/allure-results/<uuid>-result.json's own step tree (walk every step's `status`, including nested ones) to confirm your specific insertions passed.
type: feedback
---

## The situation

`test_upload_via_three_options_and_verify_selection` (ELITEA-1824) carries
an already-shipped, already-open, sanctioned-RED known defect (`#649`),
asserted via `expect.soft(...)` per this project's no-masking policy. My
ELITEA-1835 extension added two NEW hard `assert` insertions elsewhere in
the same test. Running the full test after the extension: `pytest` exit
code non-zero, overall allure `status: "failed"`.

This is EXPECTED and does not mean the new insertions are broken —
`expect.soft()` doesn't raise at the point of failure; pytest-playwright's
own plugin accumulates soft-assert failures and re-raises the first one at
teardown (`pytest_playwright.py:119: raise errors[0]`), which is what
makes the WHOLE TEST show as failed even though every individual
`allure.step` — including the one containing the soft-assert itself —
shows `status: "passed"` in the per-step JSON (because no exception
propagated out of that step's `with` block).

## How to verify your OWN new assertions actually passed

Don't infer from the pytest exit code or the top-level `status` field
alone. Read the actual result JSON and walk the step tree:

```python
import json
d = json.load(open("reports/allure-results/<uuid>-result.json"))
print("overall status:", d["status"])          # may be "failed" — expected if sanctioned-RED exists
def walk(steps, indent=0):
    for s in steps:
        print(" " * indent, s["status"], "-", s["name"][:100])
        if "steps" in s:
            walk(s["steps"], indent + 2)
walk(d.get("steps", []))
```

Find your new step(s) by name/ELITEA-ID in the printed tree and confirm
`passed`. Cross-check `statusDetails.message` names the EXACT pre-existing
defect ID you expect (not a new/different failure) — if the message names
a different assertion, THAT'S a real regression, not the known sanctioned
one.

## Determinism check across reruns

Run the test 2x (or per the project's N for the merge gate). If both runs'
`statusDetails.message` are byte-identical modulo the randomized bucket
name, that's the deterministic signature `.agents/testing.md` § Merge gate
requires for the sanctioned-RED exception — record it in the Run Report /
PR body as evidence, not just an assertion that it's "the known defect."

From ELITEA-1835 (PR #675): 2/2 runs, both failed ONLY on `#649`'s
soft-assert with the same message shape; both runs' nested
`ELITEA-1835 Steps 2-3` / `ELITEA-1835 Step 11` steps showed `passed`.
