# Test Case: File Preview/Edit – Actions Dropdown in Editor Contains Copy Content, Download, Delete

## Metadata
- **TMS ID**: ELITEA-1856
- **Linked Story**: none
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1851/1852/1856, 2026-08-02)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (auth_state, localhost).
- A fresh bucket with a previewable text file exists (see § Test Data — same
  pattern as ELITEA-1851/1852, NOT a shared "bucket-1").
- Browser context needs clipboard permissions granted
  (`context.grant_permissions(["clipboard-read", "clipboard-write"])`) to
  assert the Copy Content result — confirmed necessary live.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Fresh bucket via `artifact_bucket` fixture + `machine_learning.py` uploaded
  via `ArtifactAPI.upload_file()` — same seeding pattern as ELITEA-1851/1852.
  **This case DELETES the file as its final step** — it must run with its
  own bucket/file, never sharing state with 1851/1852's specs.
- Delete confirmation message: **case text is stale — see Coverage Map
  clarification.** Confirmed live exact text:
  `"Are you sure to delete the machine_learning.py?"` (no "It can't be
  restored" clause). Filed: `EliteaAI/elitea-testing-public#1109`.
- Delete success notification: **case text does not match anything in the
  codebase.** Confirmed live exact text: `"File deleted successfully"`
  (`toastInfo('File deleted successfully')`, `FilePreviewCanvas/index.jsx:434`
  — the only artifact-deletion toast string in the entire EliteaUI source;
  grepped for "have been deleted" / "deleted successfully" across
  `src/pages/Artifacts` and `src/[fsd]/features/artifacts` — zero matches
  for the case's literal text anywhere in the app). See Coverage Map.

## Test Steps
1. Navigate to Artifacts, open `machine_learning.py` via the "View/Edit file" icon
   - **Verify**: editor opens
2. Verify the editor panel is open
3. Click the 3-dot (ellipsis) actions menu icon (`file-preview-overflow-menu-menu-button`)
   - **Verify**: dropdown opens
4. Verify the dropdown shows exactly three options, in this order: "Copy Content", "Download", "Delete"
5. Click "Copy Content"
6. Verify the clipboard contains the full file content (via `navigator.clipboard.readText()`)
7. Reopen the 3-dot menu, click "Download"
8. Verify a download starts, with the correct suggested filename and a
   non-zero, content-matching byte size
9. Reopen the 3-dot menu, click "Delete"
10. Verify the "Delete confirmation" modal opens with the **live** message
    text (see Test Data — differs from the case's stated text)
11. Click "Delete" in the modal
12. Verify a success toast with the **live** text `"File deleted successfully"`
    (see Test Data — differs from the case's stated text)
13. Verify the editor closes
14. Verify `machine_learning.py` is no longer listed in the bucket's file table

## Expected Results
- Dropdown always shows Copy Content / Download / Delete, in that order, for
  a previewable file (`canPreview` true) — confirmed via `PreviewHeader.jsx`'s
  `menuItems` array order and live screenshot.
- Copy Content copies the exact file content to the clipboard (confirmed:
  816-byte clipboard content, includes a known content marker string).
- Download produces a file with the correct suggested filename and matching size.
- Delete removes the file: editor closes, row disappears from the table, and
  the operation is confirmed via the `deleteArtifact` mutation (not just a UI
  optimistic update — implementer should assert against a fresh
  `list_bucket_files()` API read, not just the DOM, for the strongest signal).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open editor | editor opens | step 1 | Save/Discard render | asserted |
| 2 Editor panel open | visible | step 2 | same | asserted |
| 3 Click 3-dot menu | dropdown opens | step 3 | menu items render | asserted |
| 4 Dropdown has Copy Content/Download/Delete | all 3 present | step 4 | `get_by_role("menuitem")` count == 3, texts match, in order | asserted |
| 5 Click Copy Content | content copied | step 5 | clipboard write triggered | asserted |
| 6 Verify clipboard has full content | pasted content matches | step 6 | `navigator.clipboard.readText()` == uploaded content | asserted *(stronger than "paste into a text editor" — direct clipboard API read, same observable)* |
| 7 Click 3-dot → Download | download initiates | step 7 | `page.expect_download()` fires | asserted |
| 8 File downloads, not corrupted, correct name | download valid | step 8 | suggested filename == `machine_learning.py`; size == uploaded content's byte length | asserted |
| 9 Click 3-dot → Delete | confirm modal opens | step 9 | `delete-confirm-dialog` visible | asserted |
| 10 Modal message "Are you sure to delete machine_learning.py? It can't be restored." | message shown | step 10 | `delete-confirm-message` text | **clarification** — live text is `"Are you sure to delete the machine_learning.py?"` (no restore-warning clause; the row-level dot-menu's OWN delete DOES have that clause via a different `inlineExtraContent`, but the editor-panel delete doesn't pass one). Filed `EliteaAI/elitea-testing-public#1109`. AFS asserts the live text. |
| 11 Click Delete | deletion completes | step 11 | `deleteArtifact` mutation resolves | asserted |
| 12 Success notification "The artifacts have been deleted successfully" | notification shown | step 12 | toast text | **clarification** — that exact string does not exist anywhere in EliteaUI source (grepped both `src/pages/Artifacts` and `src/[fsd]/features/artifacts`). Live text is `"File deleted successfully"`. Filed `EliteaAI/elitea-testing-public#1109` (bundled with the modal-text finding — same root cause, same case, strict-per-bug still applies per-*bug*, and this is one ticket covering two closely related text mismatches in the same delete flow, consistent with "same object + same trigger" reasoning — see note below). AFS asserts the live text. |
| 13 Editor closes | editor closes | step 13 | Save button no longer present | asserted |
| 14 File removed from table | row gone | step 14 | `artifacts-file-row` filtered by filename → count 0 | asserted |

**Note on bundling the two ELITEA-1856 text clarifications into one ticket
(#1109):** both are the *same* trigger (the editor panel's Delete action) on
the *same* object (the delete confirmation UX for one file), just two
sequential strings in that one user-facing flow — this reads as one finding
with two observations, not two independent findings, so it was filed as a
single ticket rather than two. If a reviewer judges these as genuinely
separate findings under strict-per-bug, splitting is a one-comment fix, not
a re-exploration.

### Axis 2 — Analyst additions
- Assert the dropdown item **order** is exactly Copy Content → Download →
  Delete — added: confirmed live via screenshot; the order is a real UI
  contract (users learn muscle memory), worth locking down even though the
  case only says "contains" not "in this order".
- Assert **no console errors** across copy/download/delete — added: standard
  side-channel discipline.
- Assert deletion via a **fresh API read** (`ArtifactAPI.list_bucket_files()`)
  in addition to the DOM check — added: the DOM row disappearing could be an
  optimistic UI update; confirming server-side removal is a stronger
  persistence guarantee, same reasoning as ELITEA-1852's reopen-and-verify step.

## Cleanup
1. The test's own Delete action (step 11) removes the file — no separate
   file cleanup needed.
2. `artifact_bucket` fixture teardown deletes the (now-empty) bucket.
   **Known flake, reconfirmed live this session**: `DELETE .../buckets/.../p--{project}.{bucket}`
   returned 404 when cleaning up this session's own scratch bucket after the
   file had already been deleted via the UI — consistent with the existing
   tracked `#636` bucket-teardown-404 issue (bucket-vs-file delete-empty-bucket
   path), not a new defect.

## Concrete Handles (discovered during exploration)

Shared editor-surface handles per ELITEA-1851's Concrete Handles table
(open icon, header, Save/Discard, close). This case's own:

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| 3-dot actions menu trigger | `file-preview-overflow-menu-menu-button` — **EXISTS, confirmed live** (`DotMenu` id=`"file-preview-overflow-menu"` → `data-testid="file-preview-overflow-menu-menu-button"` per `DotMenu.jsx`'s own convention) | no work needed |
| Dropdown menu items (Copy Content / Download / Delete) | **testid needed** — currently `data-testid="None"` confirmed live (`PreviewHeader.jsx`'s `menuItems` array has no `key` field, so `DotMenu`'s `testId: item.key` → `undefined` → `BasicMenuItem`'s `data-testid={testId ? \`${testId}-menuitem\` : undefined}` never fires). Add `key: 'artifacts-preview-copy-content'` / `'artifacts-preview-download'` / `'artifacts-preview-delete'` to each item object in `PreviewHeader.jsx`'s `menuItems` `useMemo` → yields `data-testid="artifacts-preview-copy-content-menuitem"` etc. via the existing `DotMenu`/`BasicMenuItem` mechanism | interim (pre-testid) live exploration used `page.get_by_role("menuitem", name="Copy Content")` — **role+name is NOT the compliant final locator** per this project's testid-only policy; implementer must add the `key`s above before merging |
| Delete confirmation dialog | `delete-confirm-dialog` — **EXISTS**, reused as-is (`Modal.DeleteEntityModal`, same component the row-level delete and bucket delete already use) | confirmed live |
| Delete confirmation title | `delete-confirm-title` — **EXISTS**, text = `"Delete confirmation"` | confirmed live |
| Delete confirmation message | `delete-confirm-message` — **EXISTS**, text = `"Are you sure to delete the machine_learning.py?"` (live) | confirmed live; see Coverage Map clarification for the case-text mismatch |
| Delete confirm button | `delete-confirm-button` — **EXISTS** | confirmed live |
| Delete cancel button | `delete-confirm-cancel-button` — **EXISTS** (present, not exercised this run — not on this case's path) | exists per `DeleteEntityModal.jsx`, not asserted here (not part of this case's steps) |
| Success/delete toast | **Implementer correction (Phase 2 — Explore), same finding as the ELITEA-1852 AFS:** the toast DOES have a stable testid — `success_toast_message` (`data-testid="toast-message"`, app-wide `<ToastComponent/>`, pre-existing in `artifacts_page.py` since ELITEA-1826/1832). `success_toast_message.text_content() == "File deleted successfully"` replaces the AFS's proposed raw-text `get_by_text()` handle. | `success_toast_message` — EXISTS, reused |
| Download event | `page.expect_download()` around the Download menuitem click — Playwright's native download API, not a DOM locator | n/a |
| Clipboard content | `page.evaluate("navigator.clipboard.readText()")` after granting `clipboard-read`/`clipboard-write` context permissions | n/a — browser API, not a DOM locator |

## Network Behavior
- Delete fires `deleteArtifact` (RTK Query mutation) — wait on its resolution
  (not a timeout) before asserting the toast/table-update.
- Download uses the existing `downloadFileFromArtifact` util — same download
  mechanism already exercised by `download_file()` in `artifacts_page.py`
  (row-level download), confirmed to work identically from the editor panel.

## Known Defects Found During Exploration
- **[CLARIFICATION]** Delete confirmation modal text AND delete success toast
  text both differ from the case's stated text — filed
  `EliteaAI/elitea-testing-public#1109` (bundled, see Coverage Map note).
  Case-text drift, not a functional defect — delete works correctly; AFS
  asserts the live strings.

## Blocked Steps
None.

## Automation Hints
- Reuses the shared `open_file_in_editor(bucket, filename)` helper (see
  ELITEA-1852's Automation Hints) to reach the editor before exercising the
  3-dot menu.
- The row-level 3-dot menu (`ArtifactRowActions.jsx`, already covered by
  ELITEA-1839 / `test_artifacts_download_single_file_dropdown.py`) is a
  **different** DotMenu instance (`id="artifact-actions-{row.id}"`) with only
  Download/Delete — **not** the same surface as this case's editor-panel
  DotMenu (`id="file-preview-overflow-menu"`, has Copy Content too). Don't
  conflate the two when extending `artifacts_page.py` — they need distinct
  page-object methods despite the shared `DotMenu` component.
- Confirmed live via direct Playwright scratch script (MCP unreachable this
  session). Screenshots: `automation/test-results/screenshots/ELITEA-1856-*.png`.
