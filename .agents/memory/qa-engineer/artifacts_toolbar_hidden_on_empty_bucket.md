---
name: Artifacts toolbar is hidden entirely on an empty bucket
description: On EliteaUI main since 471b753c, artifacts-upload-files-button/-file-search-input/-download-files-* do not exist while a bucket is empty
type: reference
aliases: [artifacts-upload-files-button, isEmptyFiles, empty bucket toolbar, artifacts toolbar missing, EL-6687]
tags: [area/artifacts, type/surface-quirk]
created: 2026-09-29
updated: 2026-09-29
---

## The gate

`EliteaUI` `src/pages/Artifacts/component/ArtifactTable.jsx:295`
```js
const isEmptyFiles = rows.length === 0 && !isFetching;
```
passed to `ArtifactTableToolbar.jsx:93`
```jsx
{!isEmptyFiles && ( <Box sx={styles.rightSection}> ... )}
```
The whole right-hand toolbar group is inside it: `artifacts-file-search-input`,
`artifacts-upload-files-button`, `artifacts-download-files-tooltip` /
`artifacts-download-files-button`, delete. **None of them exist in the DOM while
the selected bucket is empty.** Introduced by `471b753c` "fix: [EL-6687] Fixed
Artifacts section UI issues", 2026-09-23 — before that the group rendered
unconditionally.

## Consequence for tests

An empty bucket has exactly ONE upload entry point: the centre button in
`ArtifactTableNoFiles.jsx`, `artifacts-upload-files-empty-state-button`
(`ArtifactsPage.upload_files_via_empty_state()`).

So `is_bucket_empty() == True` and `upload_files()` (toolbar) are **mutually
exclusive** — any test that asserts both is structurally impossible on DEV. To
drive the toolbar entry point, seed >=1 file via `artifact_api` first (the
pattern `tests/ui/artifacts/test_artifacts_upload_duplicate_skip.py:112` uses,
proven green on DEV).

## Same commit, other gate

`FilePreviewCanvas/PreviewHeader.jsx` gained `{canPreview && !isImageFileType && (`
— `artifacts-preview-save-button` is absent for IMAGE files, so the generic
`ArtifactsPage.open_file_in_editor()` (waits for that button, `artifacts_page.py:2906`)
cannot be used on an image.

Related: [[dev_ci_triage_check_eliteaui_main_first]]
