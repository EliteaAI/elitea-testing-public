---
name: Artifacts bulk-delete flow — navigate_to_bucket() file-table race + scoped-selector override
description: ELITEA-1847 — CORRECTED in R2 (PR #661) — the flake below was issue #638 recurring at a second call site, not an independent race; navigate_to_bucket() now carries the same retry guard as navigate_to_bucket_folder(); plus still-valid confirmation that a testid-on-wrapper click target needs no .locator("button") scoping when the wrapper's bounding box is pixel-identical to the inner button's, and why a bare id-selector read (even a stable a11y id) still needs its own testid per this project's scoped-sub-selector policy
type: feedback
---

## CORRECTION (R2, PR #661): this WAS the #638 race, not a different one

**The section immediately below this one, as originally written, was wrong.**
A fresh reviewer's independent 5-run re-run of the merged test got 40% flaky
(2/5), always at `wait_for_file_count()` with the row-count locator stuck at
0 for the full timeout — and the failure screenshot showed the app had
silently opened an unrelated bucket ("aa") instead of the seeded target: the
exact #638 symptom (project-id-resolution race stripping the `bucket` URL
param before the auto-select-bucket effect reads it), already root-caused
and guarded for `navigate_to_bucket_folder()`. The "different race, breadcrumb
text vs. S3-listing fetch" theory below doesn't actually fit a locator that
is *stably* stuck at 0 — it can only explain a *transient* empty read that
self-corrects, which is not what a wrong-bucket-loaded failure looks like.
Full corrected root cause + fix: see
`artifacts_direct_bucket_url_nav_project_id_race.md`'s own "UPDATE" section.
`navigate_to_bucket()` now carries the identical retry-on-URL-param-loss
guard as `navigate_to_bucket_folder()`, verified via the full shared-caller
regression protocol (4 existing callers + this test, all re-run clean).
`wait_for_file_count()` remains in place as a harmless, legitimate
condition-based settle-wait, but is NOT what fixes the race — kept for the
(unconfirmed, possibly nonexistent) residual render lag once the correct
bucket is loaded.

**Meta-lesson:** a companion memory entry
(`artifacts_direct_bucket_url_nav_project_id_race.md`) already had a
"for future artifacts cases" section predicting exactly this gap in
`navigate_to_bucket()` — it wasn't checked before writing the diagnosis
below. When a bucket-navigation symptom shows up, grep memory for
"bucket"/"project-id"/"638" before writing a NEW root-cause theory; a
matching prior entry is a strong prior, not just background reading.

## `navigate_to_bucket()` can return before the file table has data (ORIGINAL, INCORRECT diagnosis — kept for the record, see correction above)

`ArtifactsPage._wait_for_bucket_panel()` waits for the bucket NAME text to appear
in the main panel (the breadcrumb label, which renders synchronously from the
URL's `bucket` query param) — this is independent of the S3-listing fetch that
actually populates the file table. A bare `get_file_names()` call immediately
after `navigate_to_bucket()` can therefore transiently read `[]` for a
demonstrably non-empty bucket. Confirmed live: 3 failures in 8 local runs,
always at the very first post-navigation read, always resolving to the correct
data on retry.

~~This is a **different** race from the already-documented one on
`navigate_to_bucket_folder()` (issue #638, `selectedProjectId` resolving late
and stripping URL params) — that one is specific to the folder-deep-link path
and already has a live-URL-param-check-and-retry fix. The plain
`navigate_to_bucket()` (root path, no folder) has no equivalent guard.~~
**This paragraph was wrong — see the CORRECTION section above. It WAS #638.**

**Fix as originally shipped (additive-only, later superseded — see
correction above):** (`navigate_to_bucket()`/`_wait_for_bucket_panel()`
themselves untouched at this point — 3+ existing callers): a new
`ArtifactsPage.wait_for_file_count(expected_count, timeout)` using Playwright's
auto-retrying `expect(self._file_rows()).to_have_count(expected_count,
timeout=timeout)`. This masked the real #638 recurrence often enough (5/5
in the original small sample) to look like a fix, but did not address the
root cause — see correction above for what actually ships now.

## Testid-on-wrapper click target: check the bounding boxes before adding `.locator("button")` scoping

For a MUI `Tooltip`-wrapped icon button where the testid lands on the wrapping
`<Box component="span">` (not the inner button — see the ELITEA-1809/1847
tooltip-cloning pattern), don't assume a `.locator("button")` chain is needed
to reach the clickable target. Confirmed live via CDP
`getBoundingClientRect()` on both elements (ELITEA-1847,
`artifacts-delete-files-button`): the wrapper's box was pixel-identical to the
inner `IconButton`'s box, so Playwright's `.click()` on the wrapper locator
directly fires the button's own `onClick` (real browser hit-testing resolves
to the deepest element at that point, which bubbles the event correctly) —
simpler AND avoids a raw-tag-selector chain entirely. Check this before
reaching for the AFS's/anyone's suggested `.locator("button")` scoping
shortcut; it's often unnecessary.

## A stable HTML `id` is still not a compliant scoped selector — add a testid instead

The AFS for ELITEA-1847 suggested reading `DeleteEntityModal.jsx`'s message
via `dialog.querySelector('#alert-dialog-description')` (a hand-authored a11y
id, not a CSS class) as "acceptable" since it's scoped inside the already
testid'd `delete-confirm-dialog` root. This conflicts with the established
ELITEA-1840 precedent (`artifacts_zip_download_checkbox_and_dialog_testid_gaps_elitea1840.md`):
"this project's strict locator policy forbids a scoped raw-tag selector
(`dialog.locator("h2")`) even inside a real testid-anchored parent — scoped
sub-selectors must themselves be `[data-testid="…"]`-based." An id selector is
the same forbidden shape as a tag selector for this purpose — stability of the
attribute doesn't exempt it. Fixed by adding a THIRD generic (non-feature-scoped)
testid, `delete-confirm-message`, directly onto the same element the existing
`id="alert-dialog-description"` already targets (kept, unchanged, for a11y) —
same shape as this shared modal's pre-existing `delete-confirm-dialog`/
`delete-confirm-button` testids. When an AFS suggests reading via a bare id/
class/tag selector "because it's stable," override it with a new testid on
that exact element instead, and document the override in the AFS
(Phase 2 amend-in-PR rule) rather than shipping the raw selector.
