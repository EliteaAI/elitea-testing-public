---
name: Verifying new appended steps pass when the covering test already carries a sanctioned-RED defect
description: When extend-existing work appends steps to a covering test that already carries a pre-existing expect.soft() known-defect assertion (e.g. ELITEA-1824's #649), the overall pytest exit code/failure message only ever reports the FIRST collected soft failure via pytest_playwright.py's `raise errors[0]` — it tells you nothing about whether your own new steps, which run AFTER that soft-assert point, actually passed. Read reports/allure-results/*result.json's per-step `status` field instead of trusting stdout's single reported AssertionError.
type: feedback
---

## What happened (ELITEA-1827, PR #658, extending ELITEA-1824's covering test)

Appended Steps 47-54 to `test_upload_via_three_options_and_verify_selection`
(ELITEA-1824), which already carries a documented, merged, sanctioned-RED
`expect.soft()` assertion for known defect #649 (bucket-menu upload doesn't
reset Path to bucket root) at Steps 30-32 — well BEFORE my appended Steps
47-54 in execution order.

Running the extended test locally produced:
```
FAILED ... - AssertionError: Known defect: #649 — bucket-menu 'Upload files'
should default to the bucket root, not the currently-navigated subfolder
```
via `pytest_playwright.py:119: raise errors[0]`. At first glance this reads
like "the test failed" with no visibility into whether Steps 47-54 (mine)
ever ran, let alone passed.

## Why the traceback shape is actually good news, and how to prove it

`expect.soft()` does NOT raise at the call site — it appends to an internal
error list and lets the test function keep running to completion. Only
`pytest_playwright`'s own `pytest_runtest_call` hook, wrapping the ENTIRE
test call, re-raises the first collected soft failure **after the test
function has already returned normally**. So:

- If the traceback's `raise errors[0]` line is the ONLY reported failure,
  and it names a soft-assert failure whose source line is BEFORE your new
  steps, every plain `assert` statement anywhere in the test — including
  every one of your new steps AND the final side-channel checks —
  necessarily executed and passed. A hard `assert` failure anywhere would
  raise immediately at that point instead, and the traceback would point at
  your own assert line, not at `pytest_playwright.py:119`.
- Don't stop at that inference alone, though — verify it directly. This
  project's `pytest.ini` sets `--alluredir=reports/allure-results`, and each
  `allure.step()` block's pass/fail is recorded independently in the
  generated `*-result.json`'s `steps[].status` field, REGARDLESS of the
  test's overall status. Read the most recent result file:
  ```bash
  ls -t reports/allure-results/*result.json | head -1 | xargs -I{} python3 -c "
  import json
  d = json.load(open('{}'))
  print('status:', d.get('status'))
  for s in d.get('steps', []):
      print(s.get('status'), '-', s.get('name')[:90])
  "
  ```
  This showed all 46 pre-existing steps `passed`, all 8 new ELITEA-1827
  steps `passed`, the final console-error check `passed` — and even the
  Steps-30-32 block itself reads `passed` at the allure-step level (the
  step wrapper itself didn't raise; only the accumulated soft-assert
  surfaced later at the pytest-hook level). This is the authoritative,
  step-scoped confirmation — not an inference from the absence of a second
  error in stdout.

## Durable rule for future implementers

When extending a covering test that already ships a sanctioned-RED
`expect.soft()` defect (per `.agents/testing.md` § Merge gate):
1. Don't read "1 failed" + a single AssertionError as "I don't know what
   passed." Confirm from the allure JSON's per-step `status` list before
   writing the Run Report — this is exact, not inferred.
2. Report the Implementer-local verdict honestly as e.g. "RED N/M —
   sanctioned, pre-existing (#issue)" rather than "green" — the test is
   genuinely not green, and the merge gate's Sanctioned-RED exception (3/3
   IDENTICAL failures tied to the SAME open, linked defect) is what makes it
   mergeable, not a claim that it's secretly green.
3. Re-run at least twice and diff the reported known-defect line (bucket
   name/UUID aside) — identical failure text both times is what proves this
   is the pre-existing deterministic defect recurring, not a new flake or a
   regression your extension introduced.
