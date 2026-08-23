# Test Case: File Preview/Edit – Close Editor via X Button Without Saving Does Not Persist Changes

## Metadata
- **TMS ID**: ELITEA-1855
- **Linked Story**: none
- **Priority**: l3 (case `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, batch `artifacts-w05`, 2026-08-23)
- **Status**: ready-for-automation (with a declared case-text drift — see § Case-text drift)

## Preconditions
- User is logged in (auth_state, localhost).
- A fresh `artifact_bucket` fixture bucket containing `machine_learning.py`
  uploaded via `ArtifactAPI.upload_file()` (same seeding as the
  ELITEA-1853/1854 family — no shared "bucket-1" fixture exists).

## Test Data
### generate-per-test (fixture-seeded, fixture-torn-down)
- File: `machine_learning.py`, 19 lines, line 17 = `    EPOCH_LIMIT = 250`
  (unique marker for deterministic line targeting).
- Unsaved text: `"  # unsaved change"` (the case's `# unsaved change`).
- Baseline captured **before** the edit: the file row's full text (which
  carries the rendered `Last update` value in `dd-MM-yyyy, hh:mm a`) **and**
  the backend metadata `lastModified` + `size` (ms-precision ground truth).

## Case-text drift — the X-close Warning dialog (declared)

**The case's step 3 says "Click the X (close) icon to close the editor panel
→ Editor closes". Live, that is not the whole flow:** with unsaved changes,
`FilePreviewCanvas`'s `handleClose` raises a **Warning** dialog first —
title `Warning`, message
`You are editing now. Do you want to discard current changes and continue?`,
with `Cancel` and `Confirm` buttons — and the editor closes only after
`Confirm` (`src/[fsd]/features/artifacts/ui/FilePreviewCanvas/index.jsx`,
`handleClose` / `handleUnsavedChangesConfirm`).

Per the reverse-masking guard, this AFS specs the **live** contract (X →
Warning → Confirm → editor closes) rather than the stale case text, and adds
the dialog to the assertions instead of dropping a step. Every observable the
case actually cares about (change not persisted, `Last update` unchanged,
original content on reopen) is preserved and asserted. The case-text gap is
filed as a clarification — see § Known Defects Found During Exploration.

## Test Steps

1. Seed the bucket + file via API; navigate to the bucket.
2. Capture the baseline: the file row's rendered `Last update` timestamp and
   the backend `lastModified` + `size`.
3. Open `machine_learning.py` via the "View/Edit file" icon.
   - **Verify**: editor opens with CodeMirror content rendered.
4. Capture the editor's original content text (the reopen oracle).
5. Append `"  # unsaved change"` to line 17 (the `EPOCH_LIMIT = 250` line).
   - **Verify**: `# unsaved change` is visible in the editor.
6. **Verify**: Save/Discard became enabled — the product's own signal that
   `hasChanges` has propagated (deterministic guard, see § Automation Hints).
7. Click the editor's **X (close)** icon.
8. **Verify** *(live contract, beyond the case text)*: the unsaved-changes
   **Warning** dialog appears with the message
   `You are editing now. Do you want to discard current changes and continue?`.
9. Click the dialog's **Confirm** button.
10. **Verify**: the editor closes — the Save button is gone from the DOM —
    and the main panel is back on the bucket's file table with
    `machine_learning.py` listed.
11. **Verify**: the file row's rendered `Last update` timestamp is
    **identical** to the step-2 baseline.
12. **Verify** (independent ground truth): backend `lastModified` and `size`
    are both **unchanged** from the step-2 baseline — nothing was written.
13. Reopen `machine_learning.py`.
    - **Verify**: `# unsaved change` is **absent** and the content is
      **byte-equal** to the step-4 original.

## Expected Results
- Closing via X with unsaved changes raises the Warning dialog; confirming
  discards the edit and closes the editor.
- No write reaches the backend: `lastModified`, `size` and the UI-rendered
  `Last update` are all untouched.
- Reopening the file shows the original content, byte-for-byte.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open machine_learning.py via View/Edit icon | editor opens | step 3 | `open_file_in_editor` + content visible | asserted |
| 2 Type "# unsaved change" at line 17 | text appears in editor | step 5 | `edit_file_preview_line_containing` + `to_contain_text` | asserted |
| 3 Click X to close the editor panel | editor closes | steps 7–9 | X clicked; live product raises the Warning dialog first, Confirm then closes it | asserted *(adapted — see § Case-text drift; the extra dialog is asserted, not skipped)* |
| 4 Editor closes, main panel returns to the bucket file table | file table shown | step 10 | Save button count 0 + `file_exists(FILE_NAME)` | asserted |
| 5 "Last update" for machine_learning.py has NOT changed | timestamp identical | steps 11–12 | UI-rendered row timestamp equal to baseline **and** backend `lastModified`/`size` unchanged | asserted |
| 6 Reopen — "# unsaved change" not present, original content shown | change absent | step 13 | marker absent **and** content byte-equal to the captured original | asserted |
| Precondition: known "Last update" timestamp | baseline exists | step 2 | captured pre-edit from the row + API | asserted (precondition) |

### Axis 2 — Analyst additions
- **The X-close Warning dialog itself** (step 8) — the live product's real
  safety gate for this flow; asserting it prevents a silent-data-loss
  regression from passing as "editor closed, nothing persisted".
- **Backend `lastModified` + `size` unchanged** (step 12) — the case only
  names the UI-rendered `Last update`, whose display resolution is whole
  minutes and would happily pass a real write that landed inside the same
  minute. The ms-precision API values are the honest oracle.
- **Byte-equality on reopen** (step 13) rather than mere absence of the
  marker — catches a partial/garbled revert.
- **No console errors** across the flow (standard side-channel discipline).

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket (known `#636`
   404-on-teardown flake handled gracefully).

## Concrete Handles (discovered during exploration)

| Element | Locator | Provenance | Notes |
|---|---|---|---|
| Editor X (close) icon | `artifacts-preview-close-button` | pre-existing (ELITEA-1851) | already has `close_file_preview()`, but that helper waits for the button to hide — it does NOT expect the Warning dialog, so this case clicks the descriptor directly |
| Unsaved-changes dialog message | `alert-dialog-content` | **pre-existing, generic, shared** (`src/components/AlertDialog.jsx`) | already used as a `LocatorDescriptor` in `automation/pages/secrets_page.py` — a shared component correctly carrying a generic (not feature-scoped) testid; no new testid needed or permitted here |
| Unsaved-changes dialog Confirm | `alert-dialog-confirm-button` | pre-existing, generic, shared | label `Confirm` (AlertDialog default — `index.jsx` passes no `confirmButtonText`) |
| File row (for `Last update`) | `artifacts-file-row` via `get_file_row_text()` | pre-existing | no per-cell testid; the row testid is the anchor and its text is parsed, same approach as ELITEA-1852 |

## Network Behavior
- The whole flow is expected to be **write-free** — no `createArtifact` POST.
  The `lastModified`/`size` assertions in step 12 are the observable proof.

## Known Defects Found During Exploration
- **No product defect.** One **case-text clarification** filed: ELITEA-1855's
  step 3 omits the unsaved-changes Warning dialog that the live product
  raises before closing (see § Case-text drift). Issue:
  `EliteaAI/elitea-testing-public#1687`.

## Blocked Steps
None.

## Automation Hints
- **Wait for Save/Discard to become enabled before clicking X.** This is
  load-bearing, not cosmetic: `useCodeMirror` debounces `notifyChange` by
  30 ms, so `hasChanges` in `FilePreviewCanvas` lags the typed DOM text.
  During analysis, a run that clicked X without that guard closed the editor
  **without** the Warning dialog (the parent still believed the editor was
  clean); with the guard, the dialog appeared 3/3 across two separate live
  sessions, including immediately after a discard cycle. Never assert the
  dialog without first waiting on the enabled state.
- `close_file_preview()` (page object) is NOT reusable here — it waits for the
  close button to disappear, which never happens while the dialog is up.
- Confirmed live 2026-08-23 via pytest scratch runs against
  `http://localhost:5173`.
