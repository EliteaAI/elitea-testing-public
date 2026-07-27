---
name: Artifacts bucket-menu upload stale-currentPrefix defect + tree-item trailing-slash quirk
description: ELITEA-1824 found that the Artifacts bucket 3-dot-menu "Upload files" entry point silently inherits whatever folder the user is currently browsing instead of resetting to the clicked bucket's own root — filed as #649, invisible to ELITEA-1808's earlier pass because that case never navigated into a subfolder first. Also documents the artifacts-tree-item-{key} trailing-slash convention for folder vs file nodes.
type: feedback
---

## The defect pattern (#649) — why it stayed hidden through 1808

`EliteaUI/src/[fsd]/features/artifacts/lib/hooks/useFileUpload.hooks.js` handles
THREE upload entry points (bucket-menu, toolbar, table drag-drop) through one
shared hook. `onBucketUpload(bucketName)` — the handler wired to a specific
bucket's own 3-dot-menu "Upload files" item — only sets `pendingUploadBucket`.
It never touches or resets `currentPrefix`, the state that tracks whatever
folder the user currently has open in the RIGHT panel. The dialog's default
Path is always computed by `computeFullPath()`, which unconditionally calls
`PathValidationHelpers.computeSecurePath(folderPath, currentPrefix)` — the
SAME `currentPrefix` the toolbar/table upload path also uses.

Net effect: clicking bucket X's own dot-menu "Upload files" while browsing
bucket X's subfolder `a1` pre-fills the dialog with `X/a1/`, not `X/` — even
though `BucketItem.jsx`'s `handleUploadClick` only ever passes `bucket.name`
(implying bucket-ROOT intent) to the handler. If the user doesn't notice and
clicks Upload, the file lands in the wrong location.

**Why ELITEA-1808's earlier AFS never caught this**: 1808 tested the identical
bucket-menu entry point, but ONLY from the Artifacts landing page before any
bucket had ever been opened — `currentPrefix` was empty by coincidence, so the
bug never had a chance to manifest. ELITEA-1824 is the first case whose own
literal step sequence (upload via center button into `a1`, upload via toolbar
into `a1`, THEN exercise the bucket-menu entry point) actually exercises the
buggy state. **Lesson: a "same entry point, tested before" claim in an
existing AFS does NOT mean the entry point's behavior is fully characterized
— re-verify from whatever PRECONDITION STATE the new case's own flow actually
reaches, don't assume a prior pass's fresh-navigation context generalizes.**

**Isolation technique that made the report actionable**: don't file on a
single observation. Reproduce once from the buggy precondition (inside a
subfolder), then IMMEDIATELY re-test the identical entry point from a
freshly-reselected bucket root (`currentPrefix` empty again) in the same
session. If the second pass is correct, you've isolated the defect to
stale-state reuse specifically, not a general dialog breakage — this is what
let the bug report name the exact code path (`currentPrefix` reuse) instead
of a vague "path sometimes wrong."

**Classification call**: filed `defect-found` (real bug, confirmed, filed),
but explicitly recommended in Automation Hints that the implementer use this
project's own documented "Sanctioned-RED exception" merge-gate pattern
(`.agents/testing.md` § Merge gate — `expect.soft()` + `# Known defect: #N`)
rather than pausing the whole case, since the defect is isolated (1 of 46
case steps) and the rest of the flow was fully verified live using a
one-line workaround (clear the Path field before clicking Upload). The AFS
status vocabulary's literal "defect-found ... automation paused until fix"
wording is in tension with this project's own sanctioned-RED precedent for
isolated defects — when both apply, lean toward giving the implementer the
concrete soft-assert path rather than a blanket pause, and say so explicitly
in the AFS rather than leaving the tension unresolved.

## Tree-item testid trailing-slash convention

`FileTreeItem.jsx`'s dynamic `artifacts-tree-item-{key}` testid keys FOLDER
nodes with a TRAILING SLASH (`artifacts-tree-item-a1/`) but FILE nodes
without one (`artifacts-tree-item-sample.txt`) — confirmed live via DOM
query this run. Easy to get wrong when templating
`ARTIFACTS_TREE_ITEM.format(name)` in a page-object call site — always
append `/` when targeting a folder node, never for a file node.

## Other confirmed-missing handles from this run (specced, not self-fixed)

- Center empty-state "Upload files" button (`ArtifactTableNoFiles.jsx`'s
  `<Button.BaseBtn>`) — zero testid on either branch, confirmed via source.
  Different element from the toolbar's `artifacts-upload-files-button`.
- Main-panel breadcrumb header — both the bucket-name label and each
  folder-name crumb (`BreadcrumbNavigation.jsx`) render as bare
  `<Typography variant="headingSmall">` with no testid anywhere.
- Bucket-row / tree-item "selected/highlighted" state — no `data-*`
  attribute exists at all (confirmed via `getAttribute` scan); the only
  signal is an unstable emotion-hash CSS class background-color change,
  which violates this project's "state via data-* filter on the stable
  testid, never CSS-only" rule.
