---
name: Bucket-menu upload prefix — two cases assert opposite expectations
description: ELITEA-1834 and ELITEA-1824 assert opposite values at the same upload-dialog Path node; #1629 pending
type: project
aliases: [currentPrefix, upload path prefix, bucket actions upload, "#649", "#1629"]
tags: [area/artifacts, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## The contradiction

Artifacts' bucket 3-dot menu → "Upload files" opens the "Upload files to ..."
dialog whose Path prefix renders `{bucket}/{currentPrefix}`
(`Artifacts.jsx`'s single `currentPrefix`, never reset by `BucketItem.jsx`'s
`handleUploadClick`, rendered by `UploadPathDialog.jsx:94`).

- **ELITEA-1834** (`test_artifacts_upload_to_selected_subfolder.py`) says that
  inheriting the selected subfolder is CORRECT → hard assert `{bucket}/a1/`.
- **ELITEA-1824** (`test_artifacts_upload_three_options_verify_selection.py`)
  says it should reset to the bucket root → `expect.soft()` failing on purpose
  as KNOWN DEFECT #649.

Same DOM node, same machine state, opposite expectations. Filed for a human
ruling as CLARIFICATION #1629. **Do not "align" one spec to the other** before
that ruling — a fix to #649 flips 1834's steps 12-18 and is a re-analysis, not
a weakening.

## Implementation facts (verified 2026-08-21, localhost:5173)

- The flow needs NO page-object changes — `artifacts_page.py` already covers it.
- `artifacts` is not a registered pytest marker; artifacts specs use
  `ui, regression, p<pri>, new`.
- Seeding `a1/` for a case whose subject file is `sample.txt`: name the seed
  file something else (`seed.txt`) or the second upload hits the
  "Resolve duplicates" dialog.
- CLARIFICATION #651 (bucket-row click TOGGLES the tree when already selected)
  is real — guard every bucket-row click with a post-condition check plus a
  conditional second click.

Related: [[artifacts_surface_digest]]
