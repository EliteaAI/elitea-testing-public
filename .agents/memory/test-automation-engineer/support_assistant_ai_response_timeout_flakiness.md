---
name: Support Assistant AI-response 60s timeout flakiness
description: test_support_assistant_smoke.py's AI_RESPONSE_TIMEOUT=60_000 is tight enough that any test in the file waiting on a live AI response can intermittently time out — observed hitting 3 different tests across 2 full-file runs in one sitting (ELITEA-1798). Non-deterministic, different test each run — infrastructure flake, not a regression tied to any single PR.
type: feedback
---

## What happened (ELITEA-1798, PR #580)

A pure decorator-only, additive `extend-existing` change (adding a second
`@allure.issue` link to `test_send_message_and_receive_response`, zero test
logic touched) was run as the mandated full-covering-spec-file regression
check twice:

- Full-file run 1: the target test itself **FAILED** —
  `playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout
  60000ms exceeded` during the AI-response wait.
- Full-file run 2: the target test **PASSED**, but two *different*, unrelated
  tests in the same file failed with the identical timeout signature
  (`test_widget_state_persists_after_close_reopen`,
  `test_history_restore_and_continue`).

A decorator addition cannot affect runtime AI-response timing. The failure
location shifting between runs (never the same test twice, never tied to
the diff) confirms this is pre-existing, non-deterministic infrastructure
flakiness in the `AI_RESPONSE_TIMEOUT = 60_000` wait — not something any
single case's implementer introduced or can fix in scope.

## The pattern (matches test-automation-lead's merge-gate precedent)

Same shape as `test-automation-lead`'s
`isolated_flake_restarts_merge_gate_count.md`: a non-reproducing
`playwright._impl._errors.TimeoutError`, healthy environment around it,
different test hit each time. That entry's rule applies here too — don't
treat a single non-deterministic timeout as a regression requiring an
implementer fix, and don't silently re-run until green without recording
it. Do NOT touch the shared 60s constant or wait logic to "fix" this inside
an unrelated case's PR — that risks masking a genuine future regression and
is out of scope for anything but a dedicated flake-investigation task.

## Action for future implementers

If you're extending/touching `test_support_assistant_smoke.py` and the
mandated full-file regression run flakes on an AI-response wait:

1. Don't panic-fix the timeout constant inline.
2. Confirm your own target test is green in at least one full-file run (or
   isolation) — that's your actual regression evidence.
3. Document the flake honestly in the Run Report (which test failed, what
   error, that it's non-deterministic across runs) rather than only
   reporting a clean run.
4. Flag it to the orchestrator as a candidate for a dedicated
   flake-investigation task — this has now been observed hitting 3
   different tests across 2 runs in one sitting (2026-07-16), which is
   enough signal that the 60s ceiling itself may need raising or the wait
   strategy needs hardening, but that's a framework-scale call, not an
   implementer-scope fix.
