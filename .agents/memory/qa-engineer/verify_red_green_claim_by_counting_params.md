---
name: Verify a red-green claim by counting parametrized cases
description: A static reviewer CAN audit an implementer's "N failed / M passed" red demo — count the test matrix by hand
type: feedback
---

The reviewer slot is **static** — no execution — so an implementer's red-green
demonstration ("stripped the fix → 10 failed / 12 passed") normally has to be
taken on trust. It doesn't.

**Count the test matrix yourself and simulate the strip.** For each test
function, expand its `@pytest.mark.parametrize` cardinality, then ask per test:
*with the fix removed, does this one still pass?* Sum the two buckets and
compare with the claimed split.

Worked example — PR #2025 (#2023, `dismiss_banner_if_present` navigation-race
tolerance), `automation/tests/unit/test_banner_dismiss_navigation_race_tolerance.py`:

| Test | Cardinality | Without the try/except |
|---|---|---|
| classifier tests (5 fns, one ×4) | 8 | pass (classifier is a free function, untouched) |
| `test_navigation_race_is_tolerated_and_retried_once` ×4 | 4 | **fail** (raises) |
| `test_racing_twice_gives_up_quietly` ×4 | 4 | **fail** (raises) |
| `test_non_race_playwright_error_propagates` | 1 | pass (it raises either way) |
| `test_timeout_error_propagates` | 1 | pass |
| `test_non_race_error_on_the_retry_also_propagates` | 1 | **fail** (only 1 evaluate call; `"SyntaxError" in str` fails) |
| `test_settle_wait_timeout_does_not_abort_the_retry` | 1 | **fail** |
| happy paths ×2 | 2 | pass |

10 fail / 12 pass — exactly the claim. That match is strong evidence the suite
is **not vacuous**: it proves which assertions are load-bearing, and it proves
the propagation tests (`pytest.raises`) aren't the trivially-green kind that
pass with or without the fix.

The inverse is the real prize: if the arithmetic had come out 6/16, either the
claim was fabricated or four "tolerance" tests pass without the tolerance —
both `CHANGES_REQUESTED`, and both invisible to a diff read.
