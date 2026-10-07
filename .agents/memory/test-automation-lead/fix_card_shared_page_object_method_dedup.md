---
name: A new [FIX] intake card can be the same root cause as an already-worked sibling — check before triaging
description: ELITEA-2493 (#2407) hit the same shared ArtifactsPage.open_manage_permissions() flake already fixed in open PR #2404 for ELITEA-2494 (#2403); recognized from the diff + test source, no duplicate PR/question filed
type: feedback
---

## What happened (2026-10-07, #2407 ELITEA-2493)

The CI "Test Failure Intake" pipeline files one `[FIX]` issue per failing test,
even when several failing tests share the exact same underlying cause. #2407
(`test_no_access_permission_blocks_all_api_operations`) and #2403
(`test_read_only_permission_allows_get_blocks_write_operations`, worked
earlier the same day) are different TMS cases in the same file, but both call
the identical shared page-object method
`ArtifactsPage.open_manage_permissions()`. #2403's analyst had already
root-caused a Class-D timing flake there (bucket-row DotMenu hover-reveal
race) and opened a reviewer-APPROVED fix, PR #2404 — blocked only on a
sandbox env gap (`TEST_USER_B_EMAIL`/`_PASSWORD`/`ELITEA_TEAM_PROJECT_ID`),
tracked as question #2405.

Confirmed by reading, not re-deriving: #2407's own failing-step names ("Open
Manage Permissions modal", "Add permission exception") matched #2403's
diagnosed cascade; `gh pr diff 2404` showed the method-level fix carries no
bucket-name/test-specific branching, so it covers #2407's call to the same
method with zero extra code; `grep .env.test` confirmed the identical missing
credentials gate #2407's own execution too.

## Rule of thumb

Before dispatching a fresh analyst (or filing a fresh `question`) for a new
`[FIX]`/maintenance card: check whether its failing test calls a page-object
method another open PR already touches, or whether its symptom text matches
another open/recently-closed issue's diagnosis (`gh issue list --state all`
+ keyword/method-name match, same light-dedup discipline as bug filing). If it
matches: don't duplicate the PR or the question — comment on both issues
cross-linking them, point the "Waiting on #N" line at the ORIGINAL blocker
issue (not the sibling card), and let the one fix/one answer resolve both.
