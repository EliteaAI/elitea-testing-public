---
name: Covering test's Step 8 get_name() race — flaky, unrelated to what it's dedup'd against
description: test_import_agent_zip_nested_agent_dependencies.py flakes intermittently at Step 8 (post-import-navigation get_name() read before Name field populates) — pre-existing, doesn't affect the Steps 1-3 export/zip assertions ELITEA-1895 dedups against; filed #631
type: feedback
---

## What happened (PR #630/ELITEA-1895 traceability-extend review, 2026-07-19)

Reviewing a purely-additive `@allure.issue` decorator + docstring PR (zero test-body
changes, confirmed via `git diff | grep -E '^-[^-]'` empty and locator-touch grep
empty), the task's mandatory "independently re-run the covering test yourself, don't
trust the implementer's/analyst's prior green claims" check caught something both
the analyst (AFS: "1 passed in 139.56s") and the implementer (PR Run Report: "GREEN
1/1", "1 passed in 136.27s") had NOT: run 1 of my independent re-run was **RED**,
failing at `test_import_agent_zip_nested_agent_dependencies.py:351`
(`assert detail_page.get_name() == main_agent_name` → got `''`). Run 2, immediately
after in the same environment, passed clean in 129.31s.

**Root cause** (confirmed by reading the actual page-object code, not guessed):
Step 8 calls `detail_page.verify_on_detail_page(expected_agent_id=...)` — which
only asserts the URL (`agent_detail_page.py:455`) — then immediately reads
`get_name()` (`self.name_input.input_value()`, no auto-wait). It never calls
`wait_for_page_load()` (`agent_detail_page.py:432`), the method that specifically
waits for `input#name` to have non-empty content — needed because "The MUI form
loads the shell first and populates fields after the API call returns" (that
method's own docstring). The failure screenshot, captured automatically AFTER the
assertion raised, showed the Name field already correctly populated — proof this
is a pure timing race, not a product defect.

## Why this didn't block the PR

The flake lives in Step 8, which is ELITEA-1902's own import-round-trip-exclusive
scope — untouched by this PR's diff, and NOT part of what ELITEA-1895's dedup
argument rests on (Steps 1-3: export → `.zip` → content verification). Both my
runs got past Steps 1-3 clean before Run 1 hit the Step 8 race. Filed as a
separate flaky-test issue (#631, labelled `bug` since no dedicated flaky-test
label exists in this repo) rather than blocking the traceability PR — fixing an
unrelated pre-existing bug inside the same PR would have been scope creep per the
bugfix-workflow anti-patterns ("don't fix multiple unrelated bugs in one PR").

## Generalizes to

1. **Do the mandatory independent re-run even on a "trivial diff" PR, and expect
   it to sometimes surface something the diff didn't cause.** A green run
   claimed twice (analyst + implementer) is not proof of determinism — intermittent
   flakes can dodge two runs and hit a third.
2. **When a re-run fails, check WHERE in the test it failed before treating it as
   blocking.** If the failure is in a step the PR's own coverage claim doesn't
   depend on (here: Step 8 vs the Steps-1-3 being dedup'd), the correct response
   is "approve the PR, file the flake separately" — not "block the PR on an
   unrelated pre-existing bug."
3. **`verify_on_detail_page()` is a URL-only check on this page object family —
   it is NOT a substitute for `wait_for_page_load()`.** Any new test-writing
   pass that reads a form field (`get_name()`/`get_description()`/etc.)
   immediately after a fresh navigation should call `wait_for_page_load()`
   first; `verify_on_detail_page()` alone is insufficient and this is exactly
   the gap that produced the flake.
