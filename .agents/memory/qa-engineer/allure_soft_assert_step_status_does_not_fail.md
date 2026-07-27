---
name: Allure soft-assert step status does not fail
description: expect.soft() failures don't mark their own allure.step as failed — only the aggregated test status turns failed at teardown; check the raised AssertionError text, not the step tree, when verifying a sanctioned-RED classification
type: feedback
---

Found while reviewing PR #675/ELITEA-1835 (reviewer slot). When independently
verifying a sanctioned-RED classification (a known-defect `expect.soft()`
assertion is the ONLY intended source of a test's red status), don't expect
the allure-results step tree to show a `failed` status on the step containing
the soft assertion.

Playwright's `expect.soft()` records the failure without raising immediately;
`pytest-playwright`'s fixture teardown aggregates all soft failures and raises
them via `pytest_playwright.py`'s `raise errors[0]` at the very end of the
test. Allure's own step-status recording only reacts to a raised exception
*at that point in the call stack* — since the soft assertion never raises
inline, the `with allure.step(...):` block it lives inside completes normally
and reports `status: passed` in the result JSON, even though that assertion
is the actual (intended) cause of the test's overall `failed` status.

Practical check for a reviewer verifying "the only failure is the sanctioned
known-defect assertion, and the rest of the flow (including any newly-added
assertions) ran clean":

1. Run the test yourself (`HEADLESS=true pytest <node-id> -v -p no:cacheprovider`).
2. Read the raised `AssertionError` text from the terminal output/JUnit XML —
   confirm it names the expected sanctioned defect (e.g. `"Known defect: #649"`).
3. Separately, parse the allure-results JSON (`reports/allure-results/*-result.json`)
   and walk the `steps` tree recursively for status. **All** steps — including
   the one containing the soft-asserted known defect — will show `passed`;
   this is expected, not evidence the defect didn't fire. What you're actually
   checking here is that no OTHER step shows `failed` (which would mean a hard
   `assert` broke somewhere else in the flow) and that any newly-added nested
   steps (the PR's own gap-assertions) show up and show `passed`.

Don't conflate "the step shows passed" with "nothing failed there" — for a
soft-assert step specifically, both readings are consistent with the intended
sanctioned-RED behavior. The authoritative failure signal is the raised
`AssertionError` text captured separately, not the step's own status field.
