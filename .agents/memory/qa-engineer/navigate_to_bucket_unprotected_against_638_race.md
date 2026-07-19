---
name: navigate_to_bucket() unprotected against the #638 wrong-bucket race
description: The plain ArtifactsPage.navigate_to_bucket() has no retry-on-URL-param-loss guard against the #638 race, unlike its sibling navigate_to_bucket_folder() — independently reproduced at 40% (2/5) during ELITEA-1847/PR #661 review, contradicting the PR's claimed "different, fixed" race
type: feedback
---

## What happened

PR #661 (ELITEA-1847, artifacts subfolder-checkbox delete flow) shipped a new
`ArtifactsPage.wait_for_file_count()` helper + Run Report claiming "3/8 exploratory
runs failed before the fix, 5/5 clean after" and characterized the failure as a
**new, different** race from issue #638 — specifically: "the breadcrumb bucket-name
label renders synchronously from the URL, independent of the S3-listing fetch that
populates the file table."

Reviewing the PR (fresh session, adversarial), I re-ran the merged test 5× in an
isolated git worktree (`HEADLESS=true pytest ... -p no:cacheprovider`, clean process
each time): **3 passed, 2 failed identically** — both at `wait_for_file_count(4, ...)`
timing out at the full 15000ms with the file-row locator stuck at 0 matches.

The failure screenshot showed the app had silently opened bucket **"aa"** (unrelated,
pre-existing, empty) instead of the freshly-seeded target bucket. That is the *exact*
symptom already root-caused and filed as **#638** ("app silently selects... aa, the
project's most-recently-used bucket") — `Artifacts.jsx`'s `selectedProjectId` vs
`queryParams.projectId` effect race, which strips the `bucket` URL query param before
the auto-select-bucket effect ever reads it, with zero error shown.

## Root cause of the misdiagnosis

`navigate_to_bucket_folder()` (added for ELITEA-1839, the case that originally
found+filed #638) already carries a bounded one-retry guard: after navigating, it
re-reads the LIVE URL's `bucket` query param and retries once if it was stripped.

The plain `navigate_to_bucket()` — used by ELITEA-1847's test and likely most other
artifacts tests that don't need a subfolder deep-link — has **no such guard**. It
only calls `_wait_for_bucket_panel()`, which loose-matches the target bucket's name
**anywhere** in `main` — including the bucket's own entry still sitting in the
left-panel bucket list — so it reports success even when the WRONG bucket is open in
the right panel. `wait_for_file_count()` then polls a **stably** empty locator (the
wrong bucket genuinely has 0 files, it's not a transient fetch-in-flight state) and
times out rather than converges. A longer/smarter wait cannot fix this — the
underlying navigation landed on the wrong entity.

## Why this matters going forward

- **Blast radius is broader than previously scoped.** #638 was filed against
  `navigate_to_bucket_folder()` only; `navigate_to_bucket()` is the far more commonly
  used method across the artifacts test suite, so this race likely affects many
  existing/future artifacts tests intermittently, not just ELITEA-1847's.
- **The right fix is the same retry-on-param-loss guard**, ported from
  `navigate_to_bucket_folder()` to `navigate_to_bucket()` (or hoisted into a shared
  helper both call) — not a longer polling timeout on a downstream assertion.
- **Verification technique:** when a Run Report claims "N/N clean after a timing fix"
  for a bucket/entity-navigation flake in this app, take a screenshot on failure and
  check the ACTUAL selected entity, not just the assertion's timeout message — a
  "stuck at 0" failure that never converges even at 15s is a strong tell that the
  wrong entity loaded, not that the right one is merely slow to populate. Don't take
  a claimed root-cause narrative at face value; independently re-run (I used 5×,
  clean process, isolated worktree) before trusting a "different race, now fixed"
  claim on a shared, already-once-buggy navigation helper.

## Disposition

Filed as CHANGES_REQUESTED on PR #661 (comment posted, not a formal `gh pr review`
approval per the gh-identity-blocks-self-approval entry). Recommended: port the
retry guard to `navigate_to_bucket()`, link the failure to #638 explicitly, and
correct the AFS's Implementer Amendments §3 + the Known Defects Found section
(currently "None") before merge.
