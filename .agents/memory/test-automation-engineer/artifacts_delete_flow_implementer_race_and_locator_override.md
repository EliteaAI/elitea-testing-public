---
name: Artifacts bulk-delete flow — navigate_to_bucket() file-table race + scoped-selector override
description: ELITEA-1847 — a new navigate_to_bucket() transient race distinct from #638 (breadcrumb text renders before the S3-listing fetch completes), fixed with wait_for_file_count(); plus confirmation that a testid-on-wrapper click target needs no .locator("button") scoping when the wrapper's bounding box is pixel-identical to the inner button's, and why a bare id-selector read (even a stable a11y id) still needs its own testid per this project's scoped-sub-selector policy
type: feedback
---

## `navigate_to_bucket()` can return before the file table has data (NOT the #638 race)

`ArtifactsPage._wait_for_bucket_panel()` waits for the bucket NAME text to appear
in the main panel (the breadcrumb label, which renders synchronously from the
URL's `bucket` query param) — this is independent of the S3-listing fetch that
actually populates the file table. A bare `get_file_names()` call immediately
after `navigate_to_bucket()` can therefore transiently read `[]` for a
demonstrably non-empty bucket. Confirmed live: 3 failures in 8 local runs,
always at the very first post-navigation read, always resolving to the correct
data on retry.

This is a **different** race from the already-documented one on
`navigate_to_bucket_folder()` (issue #638, `selectedProjectId` resolving late
and stripping URL params) — that one is specific to the folder-deep-link path
and already has a live-URL-param-check-and-retry fix. The plain
`navigate_to_bucket()` (root path, no folder) has no equivalent guard.

**Fix, additive-only** (`navigate_to_bucket()`/`_wait_for_bucket_panel()`
themselves untouched — 3+ existing callers): a new
`ArtifactsPage.wait_for_file_count(expected_count, timeout)` using Playwright's
auto-retrying `expect(self._file_rows()).to_have_count(expected_count,
timeout=timeout)`. Call it right after ANY `navigate_to_bucket()` (or after a
mutation whose invalidated-refetch could race the same way — e.g. right after
a delete/upload confirm, before reading `get_file_names()`) whenever the very
next read is a strict-equality assertion on the file list. 5/5 clean after
adding it. Any future artifacts test asserting file-table contents immediately
after a fresh `navigate_to_bucket()` should consider the same guard
proactively, not just after hitting the flake.

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
