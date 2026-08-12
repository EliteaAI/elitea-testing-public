---
name: Verify your own delivery before handoff — exit code, stdout and "already done" all lie
description: The pre-handoff evidence rules — read allure-results per-step JSON (not the exit code) when the covering test is sanctioned-RED; keep extend-existing diffs additive via nested allure.step; never trust a prior session's "just needs a wait"; check the environment for orphaned data from killed runs; and run BOTH self-check greps, not one.
type: feedback
---

## Rule

Every claim in your Run Report needs its own evidence command. These are the
six that have shipped false without one.

1. **Sanctioned-RED covering test ⇒ the exit code tells you nothing about
   YOUR steps.** `expect.soft()` doesn't raise at the call site;
   `pytest_playwright.py:119 raise errors[0]` re-raises the FIRST collected
   soft failure after the test function already returned. Walk
   `reports/allure-results/<uuid>-result.json`'s step tree (recursively —
   nested steps too) and confirm your own steps read `passed`. Cross-check
   `statusDetails.message` names the EXPECTED pre-existing defect; a different
   message is a regression, not the known one. Run ≥2× and diff the message
   (modulo random names) — byte-identical is the deterministic signature the
   merge gate requires. Report "RED N/M — sanctioned, pre-existing (#N)",
   never "green".
2. **extend-existing traceability vs additive-only.** Editing an existing
   `allure.step()` label to append the case ID breaks
   `git diff <base> -- <spec> | grep -E '^-[^-]'`. Wrap the new insertion in
   its own **nested** `allure.step` instead — same report traceability, zero
   modified lines. Same trick for a docstring header carrying a count ("Two
   CLARIFICATIONs" → add a new paragraph, don't renumber). Re-run the
   additive grep AFTER the traceability edit, not just after the assertions.
3. **Run BOTH self-check greps.** Locator-*identity* (testid-only) and
   POM-*discipline* (no `page.locator()` constructed in a spec) are
   independent. A `page.locator(OtherPage.SOME_TESTID_TEMPLATE)` in a test
   body passes the identity grep and still blocks. Second grep:
   `grep -n "page\.locator\|\.locator(" automation/tests/**/*.py` — every hit
   must be a call to a page-object *method*. Fix by adding a thin
   Locator-returning wrapper on the owning page object.
4. **A prior session's "already sitting correct, just needs a wait" is
   unverified.** There is no monitor for a subagent's own background process —
   that turn is a dead end. Re-derive from scratch: `git show --stat <sha>` in
   the actual dependency repo, read the diff (don't skim the summary),
   `grep -n "def <method>"` every fixture/method the new test calls, then run
   the gate yourself, blocking, 3×. Same discipline for your own cleanup
   claims — a "zero leftovers verified" line needs a DOM/API check outside the
   `try/except`, or a fresh reviewer will find it false.
5. **Check the environment before assuming a clean slate.** A hard-killed run
   (backgrounded shell torn down, OOM) bypasses `finally:` entirely and leaves
   real entities under the test's fixed literal names. Any "find the Nth
   pre-existing X, not one of mine" lookup must exclude on **every axis the
   downstream check matches on** — id AND the test's naming pattern — or an
   orphan produces a false positive. Prefer foreground `cmd > log 2>&1; echo $?`
   over harness auto-backgrounding for anything that creates data.
6. **A delta-shaped assertion is not automatically safe.** `final > restored`
   survives a fetch-time truncation bug ONLY if the action between the two
   counts never re-triggers the truncating fetch — a checkable implementation
   fact. Verify it live against the real defective data; don't infer it from
   the assertion's shape.

## Seen 6×

- ELITEA-1835 / PR #675 — allure JSON step tree used to confirm new steps passed under #649's sanctioned RED; also the nested-step additive fix.
- ELITEA-1827 / PR #658 — same JSON technique, 46 pre-existing + 8 new steps confirmed `passed` behind one reported soft failure.
- ELITEA-1866 / PR #670 R2 — identity grep clean, POM grep found 3 inline `page.locator()` calls at the same span.
- …plus 3 earlier occurrence(s) — full per-case detail in the source entries below.

See also: verify_extend_existing_via_allure_json_not_exit_code.md ·
verifying_new_steps_pass_when_covering_test_is_sanctioned_red.md ·
nested_allure_step_for_additive_only_traceability.md ·
finish_landing_after_a_stalled_background_wait_claim.md ·
killed_background_run_orphans_test_data.md ·
gh607_delta_assertion_survives_truncation_mechanism.md ·
pom_discipline_is_a_separate_check_from_locator_identity.md ·
hover_the_fixed_header_subelement_not_the_expandable_container.md
