---
name: Reviewer must verify, not trust
description: A Run Report, PR description or fix summary is an observation, not evidence — re-run the spec live, run the sibling test yourself, read the retry body, check "predates this PR" against file history. Then triage what you find rather than auto-blocking.
type: feedback
---

## Rule

Every claim a PR makes about its own behaviour is unverified until the
reviewer reproduces it. Static checks catch policy violations; only a live
re-run catches races. And a red rerun is triage input, not an automatic
`CHANGES_REQUESTED`.

## Remedy

- **Re-run live, several times, even on a "trivial diff" PR.** ~60 s/run is
  cheap against merging a flaky test. Implementer "GREEN 3/3 ×2" is a local
  observation; the workflow's Run Report has a separate independent-gate row
  for exactly this reason.
- **Shared component touched? Run the already-merged sibling test yourself**,
  against the exact commit the PR cites. A diff-read proves compatibility is
  possible, not that it holds.
- **Mitigation/retry claims: read the method BODY** — exactly one retry? does
  it raise rather than swallow? does it log? Re-derive the root cause against
  live source, not the issue body's excerpt. Then try to catch the mitigated
  failure firing live: a green run that never exercises the retry proves
  nothing about the retry.
- **"Predates this PR" / "pre-existing":** `git log --follow -- <file>`. If
  the file's oldest commit is inside the PR's own range, the claim is
  categorically false. The checkable claim is "not introduced by THIS commit"
  (`git show <commit> -- <file>`). Then run the same checker (`ruff`, …)
  across ALL touched files, not just the named line.
- **Triage a red rerun before writing the verdict:** where did it fail (a step
  the PR's coverage claim doesn't rest on ⇒ approve + file separately)? Is the
  duration an outlier (>2× ⇒ environment, not logic)? Does it recur under
  targeted re-runs with instrumentation? The bar is "did I genuinely
  investigate", not "did I block on any red".
- **When a test's own comment names a race class and guards ONE transition,
  check every structurally identical transition** for the same guard.

## Seen 6×

- PR #693/ELITEA-2095 R2 — 4 claimed-green sessions; 5 fresh runs gave 2 FAILED/3 PASSED: unpolled Context Budget read + missing `wait_for_generation_complete()` at one of two identical transitions.
- PR #693/ELITEA-2095 R3 — 15 runs: 14 GREEN/1 RED; the red was an unattributable console 500 with a 123 s vs ~55 s duration outlier that never recurred across 8 instrumented follow-ups ⇒ APPROVED, non-blocking note.
- PR #657/ELITEA-1868 — "sibling test still passes" after a shared `DiscardButton.jsx` fix; actually ran `test_credential_discard_changes.py` against the cited commit — PASSED, 10/10 steps, 12 seconds.
- PR #639/ELITEA-1839 — retry mitigation judged by reading its body, re-reading `Artifacts.jsx`, and 10 runs in which the race fired live once; the surviving finding was the un-amended AFS (#638 never reached it).
- PR #670/ELITEA-1866 R3 — "the nit predates this PR" false (file created by the PR, 2 commits, both in-PR); re-running `ruff` over all touched files surfaced 2 more undisclosed-but-genuinely-pre-existing nits.
- PR #630/ELITEA-1895 — mandatory rerun on a decorator-only diff caught an intermittent flake (Step 8 `get_name()` after a URL-only `verify_on_detail_page()`); out of the dedup claim's scope ⇒ approved, filed #631. Durable: `verify_on_detail_page()` is URL-only and is NOT a substitute for `wait_for_page_load()`.

See also: reviewer_must_independently_rerun_not_trust_run_report_green.md ·
independent_rerun_failure_needs_triage_not_auto_block.md ·
reviewer_verify_shared_component_fix_by_running_the_sibling_test.md ·
verifying_race_mitigation_and_afs_amendment_gap.md ·
verify_predates_this_pr_claims_against_file_history.md ·
covering_test_get_name_race_step8_flaky_1902.md
