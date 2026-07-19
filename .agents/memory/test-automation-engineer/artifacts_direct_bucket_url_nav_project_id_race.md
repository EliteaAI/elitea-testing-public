---
name: Artifacts direct bucket+folder URL navigation can race on project-id resolution
description: A cold-load direct navigation to /artifacts?bucket=X(&folder=Y) can silently land on an unrelated bucket; root cause + the retry mitigation, now ported to BOTH navigate_to_bucket() and navigate_to_bucket_folder(); filed #638
type: feedback
---

## Symptom

`ArtifactsPage.navigate_to_bucket_folder(bucket_name, folder)` (or any direct
`{BASE_URL}/artifacts?bucket=X&folder=Y` navigation done as the FIRST
navigation in a fresh browser context/page — i.e. a cold load, not a click
from within the already-hydrated app) intermittently lands on a totally
unrelated bucket (observed: "aa", the project's most-recently-used bucket),
with the target bucket showing 0 files. No error/dialog is shown — not even
the app's own "Bucket not found" alert.

Reproduced 2/5 local runs (ELITEA-1839 exploration) with the exact same
screenshot signature both times: left-panel highlights "aa", right panel
shows "aa" + "No files in this bucket", target bucket's files never checked.

## Root cause (confirmed by reading `EliteaUI/src/pages/Artifacts/Artifacts.jsx`)

Two `useEffect`s race on a cold page load:

1. `Artifacts`'s local `queryParams.projectId` is seeded from
   `useSelectedProjectId()` **at mount** (`useState({projectId:
   selectedProjectId, ...})`). That hook reads Redux (`state.settings.project`
   / `state.user.personal_project_id`), which can still be hydrating —
   resolving a render or two *after* mount on a cold load.
2. `if (selectedProjectId !== queryParams.projectId) { ...
   setSearchParams({}); ... }` (~line 616) fires once Redux's value differs
   from the mount-time snapshot — **wiping the `bucket`/`folder` URL params**.
3. The "auto-select bucket on initial load" effect (~line 489) only consults
   `searchParams.get('bucket')` once buckets have loaded. If step 2 already
   cleared the URL by then, `bucketFromUrl` is empty, so the explicit
   "bucket not found" dialog path (`if (!bucketToSelect) { ...
   setBucketNotFoundOpen(true); return; }`) is never reached — the code
   falls straight to `sortBucketsByRecent(allBuckets)[0]`, silently picking
   an unrelated bucket.

`ArtifactsPage._wait_for_bucket_panel()` does NOT catch this: it loose-matches
`bucket_name` text ANYWHERE inside `main`, including the target bucket's own
(untruncated) name still present in the left-panel LIST even while a
DIFFERENT bucket is the one actually SELECTED/rendered. So the navigation
"succeeds" (no timeout) even when it landed on the wrong bucket — the bug
only surfaces on the FIRST subsequent assertion that reads file content
(`file_exists()` etc.), which is why it looks like a random downstream
flake if you don't trace it back to the navigation step.

## Mitigation shipped (ELITEA-1839, `automation/pages/artifacts_page.py`)

`navigate_to_bucket_folder()` re-checks the LIVE URL's `bucket` query param
(`urllib.parse.urlparse(self.page.url).query`) right after
`_wait_for_bucket_panel()` returns, and retries the whole navigation ONCE if
it doesn't match the requested bucket — by the second attempt the project id
is already resolved from the first, so the race window is gone. Logs a
WARNING when it fires (visible in test output), raises a real
`AssertionError` if it fires twice in a row (never silently swallows a
persistent failure). Validated: 8/8 green across two batches after the fix
landed (one run's longer duration, ~22s vs ~13-15s baseline, is the retry
firing and self-healing transparently).

**UPDATE (ELITEA-1847, PR #661, R2 fix-only round): now ported to
`navigate_to_bucket()` too.** This note's own prediction ("if a future case
hits the same race via `navigate_to_bucket()`... check for it before
assuming it's race-free") came true and was NOT checked at implementation
time — see the new "Process lesson 2" section below. `navigate_to_bucket()`
now carries the identical retry-on-URL-param-loss guard (same shape:
`_retry` kwarg, one retry, `AssertionError` if it fires twice). The
regression protocol (4 pre-existing callers + the new test, all re-run
clean-process) confirmed the change is purely defensive with zero impact on
any existing caller's happy path. **Both `navigate_to_bucket()` and
`navigate_to_bucket_folder()` are now race-guarded** — no known unprotected
direct-URL-navigation call site remains in `ArtifactsPage`.

## Filed

https://github.com/EliteaAI/elitea-testing-public/issues/638 (bug) — the
underlying app behavior is still real and unfixed; the mitigation above is
test-side only.

## Process lesson (PR #639 round 2)

Filing #638 + writing the mitigation's own docstring + noting it in the PR
description was NOT enough — the reviewer (fresh `qa-engineer` session,
triangulating TMS case ↔ AFS ↔ implementation) correctly flagged that the
AFS's own `## Known Defects Found During Exploration` section still read
"None found" (written at the analyst pass, before this was discovered) as a
blocking `CHANGES_REQUESTED`. The AFS is the durable spec-of-record; a defect
discovered mid-implementation (Phase 4/5, not Phase 1-2) still needs a
same-PR AFS docs amendment, even when it's fully documented everywhere else
(issue, PR body, method docstring). Fixed in a follow-up `docs(afs):` commit
(`9de3e191`). **Takeaway: any implementer-discovered defect gets written back
into the AFS's Known Defects section in the SAME PR as the defect's own fix
handling — don't defer it to "it's in the PR description."**

## For future artifacts cases

- Any case doing a COLD direct-URL navigation into a bucket (not preceded by
  another in-app navigation in the same test) is a candidate for this race.
  Both `navigate_to_bucket()` and `navigate_to_bucket_folder()` are now
  guarded — prefer either over rolling your own `super().navigate()` call
  with bucket/folder params.
- If you see a `file_exists()` / file-table / row-count assertion fail
  immediately after a bucket navigation with NO other explanation, check the
  failure screenshot for a bucket-name mismatch (left-panel highlight vs. the
  bucket you expected) before assuming it's your test's own bug, a slow
  fetch, or reaching for a bigger timeout — a stably-wrong-bucket empty
  locator never converges no matter how long you wait.

## Process lesson 2 (ELITEA-1847, PR #661 R2 round)

This memory entry's own "For future artifacts cases" section already said,
verbatim, to check for exactly this race before assuming `navigate_to_bucket()`
was safe — and the first implementation pass (this same PR's original
commit) still misdiagnosed a `navigate_to_bucket()`-caused flake as an
unrelated "S3-listing-fetch lag" and shipped `wait_for_file_count()` as a
timeout-based workaround instead. The memory index pointed straight at the
answer and wasn't consulted at Phase 1/2 (Absorb/Explore) time. **Takeaway:
when a symptom involves a bucket navigation + an empty/stuck locator in this
codebase, grep this memory directory for "bucket" / "project-id" / "638"
BEFORE writing a new diagnosis** — a matching entry with a "for future
cases" section is a strong prior, not just background reading. A fresh
reviewer session (not the implementer) is what actually caught the gap here;
don't rely on review to catch what memory already told you.
