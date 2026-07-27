---
name: Verifying a test-side race mitigation — read the retry body, live-reproduce the race, check the AFS got amended
description: PR #639/ELITEA-1839 reviewer-slot playbook for judging a test-side mitigation for a found-during-implementation product race, and the AFS-amendment gap that survived to CHANGES_REQUESTED
type: feedback
---

## Context

PR #639 implemented ELITEA-1839 (download a single file via the artifacts
actions dropdown). While implementing, the implementer found a real,
intermittent product bug: direct `/artifacts?bucket=X&folder=Y` navigation on
a cold page load can race Redux project-id resolution and silently land on an
unrelated bucket (no error shown). They filed it as issue #638 and shipped
`ArtifactsPage.navigate_to_bucket_folder()` — a new page-object method that
re-checks the live URL's `bucket` query param after navigating and retries
the navigation exactly once if it was stripped.

## How I verified it (don't just trust the PR description's numbers)

1. **Masking-vs-hardening judgment**: read where the retry sits. It's
   entirely inside navigation/setup (reaching the starting state), never
   touches any case-relevant assertion (dropdown content, download
   immediacy, no-ZIP-dialog, filename, content integrity all live in later,
   untouched methods). That locates it as Phase-5 "infrastructure/timing,"
   not defect-masking — the test of "is this masking" is whether the retry
   could ever cause a real failure of a case's own expected-result to read
   as a pass. It can't; it only affects whether the test *starts* from the
   right state.
2. **Read the retry body, not the docstring.** Confirmed by inspection:
   a `_retry: bool = True` param, the recursive call explicitly passes
   `_retry=False`, and the second-failure path does
   `if not _retry: raise AssertionError(...)` — exactly one retry, no loop,
   raises (never returns success) on a repeat miss, and `logger.warning()`s
   before retrying so CI history shows how often the race actually fires.
3. **Independently verify the root-cause claim against the actual source**,
   not the issue body's code excerpt: read `Artifacts.jsx` myself, matched
   the exact effect (`selectedProjectId !== queryParams.projectId` →
   `setSearchParams({})`) racing the auto-select-bucket effect's
   `bucketFromUrl` read — line numbers matched the issue almost exactly.
   Then `git diff origin/main origin/automation/testids -- Artifacts.jsx`
   (empty) to confirm the "both branches affected" claim wasn't assumed.
4. **Live-reproduce the race, don't just trust "8/8 green."** Ran the
   merged test 10 separate `pytest` processes (the project's own gate
   command, `HEADLESS=true ... -p no:cacheprovider`). 10/10 passed, AND run 2
   of the batch actually hit the race live: the warning fired, the retry
   engaged, the test still passed. That's real independent confirmation the
   race is genuine (not a fabricated/theoretical defect) and the mitigation
   actually recovers — not just single-sample luck from the implementer's
   own count.

## The gap that DID survive to CHANGES_REQUESTED

The AFS (written by the analyst pass, *before* implementation) still read
"Known Defects Found: None found... 2/2 identical runs" and neither
`§ Known Defects Found` nor `§ Automation Hints` mentioned #638 or the new
method's mitigation rationale. Confirmed via a two-commit diff
(`git diff <analyst-commit> <implementer-commit> -- <afs-path>` — empty)
that the implementer's commit never touches the AFS file at all.

**Lesson: a mid-implementation defect-find-and-mitigate needs a
`docs(afs):` amendment in the same PR, exactly like a selector drift does.**
This is easy to miss in review because the AFS "looks done" — it was
thorough and accurate *at the time the analyst wrote it*; the implementer
found something new during Phase 2/3 that the analyst pass genuinely
couldn't have anticipated. Check the AFS's `§ Known Defects Found` /
`§ Automation Hints` sections against the PR description's own "Defect
found during implementation" callout (if there is one) — if the PR body
mentions a defect-and-mitigation story that the AFS file doesn't, that's a
real, reportable gap, not a nit. The information isn't *lost* (PR
description + linked issue + method docstring all have it) but the AFS is
the durable spec-of-record and a future reader who only opens the AFS
misses the whole story.

## Reusable technique note

For any reviewer task that asks "does this retry/mitigation actually work
or just usually work" — don't settle for re-running the test N times and
counting green. Specifically try to catch the failure-mode-being-mitigated
firing live in your own re-runs. A green run that never exercises the retry
path proves nothing about the retry logic itself; a green run where the
retry visibly engaged (via its own logging) is real evidence.
