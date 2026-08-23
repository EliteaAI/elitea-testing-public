# Test Case Family: File Preview/Edit – Discard Warning modal exit paths (ELITEA-1853 / ELITEA-1854)

## Metadata
- **TMS IDs**: ELITEA-1853, ELITEA-1854 (**family AFS** — one flow, two exit variants)
- **Linked Story**: none
- **Priority**: l3 (both cases `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, batch `artifacts-w05`, 2026-08-23)
- **Status**: ready-for-automation

## Why one family AFS

ELITEA-1853 and ELITEA-1854 are the two exit variants of a **single flow**:
open the editor → edit a line → click the header **Discard** button → the
shared `DiscardButton`'s built-in **Warning** modal opens. Everything up to
and including the modal-open assertion is byte-identical between the two
cases; they diverge on exactly one click (the modal's **Discard** vs its
**Cancel**) and on the resulting content/button state. Implemented as ONE
parameterized spec, one row per case, each row asserting its OWN expected
values.

## Preconditions
- User is logged in (auth_state, localhost).
- A fresh bucket (via the `artifact_bucket` fixture) containing
  `machine_learning.py` uploaded through `ArtifactAPI.upload_file()`.
  **NOT a shared "bucket-1"** — no such fixture exists in this suite, and
  both rows mutate in-editor state, so each row seeds its own bucket.

## Test Data
### generate-per-test (fixture-seeded, fixture-torn-down)
- Bucket: `artifact_bucket` fixture instance (case text's "bucket-1" is the
  case-author's own environment, not a suite fixture).
- File: `machine_learning.py`, seeded with **19 lines** so the case's
  "line 17" is a genuinely addressable coordinate. Line 17 content is the
  unique marker `    EPOCH_LIMIT = 250` — targeted via
  `edit_file_preview_line_containing("EPOCH_LIMIT = 250", …)`, the
  digest-mandated deterministic line-targeting technique (`Control+Home`
  nav is NOT reliable in this CodeMirror instance).
- Temporary change: `"  # temp change"` (the case's `# temp change`, appended
  at end-of-line).
- Modal message (confirmed live, exact): `Are you sure you want to discard changes?`
  — sourced from `ModalConstants.WARNING_MESSAGES.DISCARD_CHANGES`.

## Parameter table (one row per TMS case)

| Row (case) | Modal button clicked | Expected content after | Expected Save/Discard state after | Editor state after |
|---|---|---|---|---|
| **ELITEA-1853** | `artifacts-preview-discard-warning-confirm-button` ("Discard") | `# temp change` **absent**; content **byte-equal to the original** | both still **visible**, both **disabled** (`hasUnsavedChanges` back to false) | still open, CodeMirror content visible, **no toast** |
| **ELITEA-1854** | `artifacts-preview-discard-warning-cancel-button` ("Cancel") | `# temp change` **still present** | both still visible, both **enabled** ("active") | still open, changes preserved |

## Test Steps (shared up to step 6, then per-row)

1. Seed the bucket + file via API; navigate to the bucket.
2. Open `machine_learning.py` via the "View/Edit file" icon.
   - **Verify**: editor opens with CodeMirror content rendered.
3. Capture the editor's original content text (the revert oracle for row 1853).
4. Append `"  # temp change"` to line 17 (the `EPOCH_LIMIT = 250` line).
   - **Verify**: `# temp change` is visible in the editor immediately.
5. **Verify**: Save and Discard both became **enabled** (product state
   `hasUnsavedChanges` has propagated — this is also the deterministic
   guard that the Discard click will act on a dirty editor).
6. Click the header **Discard** button.
   - **Verify** (ELITEA-1853 step 6 element inventory, asserted for both rows
     since the modal is identical): the Warning modal is visible and carries
     the warning **icon**, the **title** `Warning`, the message
     `Are you sure you want to discard changes?`, an **X** close icon, a
     **Cancel** button, and a **Discard** button.
7. **Row-specific**: click the modal button named in the parameter table.
8. **Verify**: the modal closes (hidden).
9. **Verify**: the editor content matches the row's "Expected content after".
10. **Verify**: the editor is **still open** in edit mode — the CodeMirror
    content surface is still visible and the file table has NOT replaced it.
11. **Verify**: Save and Discard are still **visible**, in the row's expected
    enabled/disabled state.
12. **ELITEA-1853 only**: **verify no success notification** — the toast
    message element count is 0 across the discard (confirmed live: discard
    fires no toast, and no network request).

## Expected Results
- The header Discard button never discards directly — it always raises the
  Warning modal first (confirmed live).
- **ELITEA-1853**: confirming reverts the editor to the exact original
  content, keeps the editor open, leaves Save/Discard present but disabled,
  and shows no notification.
- **ELITEA-1854**: cancelling closes only the modal; the unsaved
  `# temp change` survives on line 17 and Save/Discard stay enabled.

## Coverage Map

### Axis 1 — Case coverage

#### ELITEA-1853

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open machine_learning.py via View/Edit icon | editor opens | step 2 | `open_file_in_editor` + content visible | asserted |
| 2 Note original content on line 17 | original noted | step 3 | original content captured as the revert oracle | asserted |
| 3 Type "# temp change" on line 17 | text appears | step 4 | `edit_file_preview_line_containing` on the `EPOCH_LIMIT = 250` line | asserted |
| 4 Modified text appears in the editor | change visible | step 4 verify | `to_contain_text("# temp change")` | asserted |
| 5 Click Discard in the top-right | Warning modal opens | step 6 | modal locator visible | asserted |
| 6 Modal has warning icon, title "Warning", message, X, Cancel, Discard | all elements present | step 6 verify | six testid'd assertions + exact title/message/button text | asserted |
| 7 Click Discard in the modal | discard completes | step 7 | click on confirm button | asserted |
| 8 Modal closes | modal not visible | step 8 | `to_have_count(0)` on the dialog | asserted |
| 9 Content reverts, "# temp change" removed | original restored at line 17 | step 9 | content == captured original **and** `# temp change` absent | asserted |
| 10 User remains in edit mode, editor open+active | editor still open | step 10 | CodeMirror content visible; file table not shown | asserted |
| 11 Save and Discard still visible top-right | both present | step 11 | both `to_be_visible()` (and disabled — see Axis 2) | asserted |
| 12 No success notification displayed | no notification | step 12 | toast-message count == 0 | asserted |

#### ELITEA-1854

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open machine_learning.py via View/Edit icon | editor opens | step 2 | same as above | asserted |
| 2 Type "# temp change" at line 17 | text appears | step 4 | same as above | asserted |
| 3 Click Discard top-right | Warning modal opens | step 6 | modal visible | asserted |
| 4 Modal message "Are you sure you want to discard changes?" | modal visible with that text | step 6 verify | exact message assertion | asserted |
| 5 Click Cancel in the modal | modal closes | step 7 | click on cancel button | asserted |
| 6 Modal closes immediately | not visible | step 8 | `to_have_count(0)` | asserted |
| 7 Editor open, "# temp change" still on line 17 | change present | step 9 | line-17 text still contains the marker | asserted |
| 8 Back in edit mode, all changes intact | edit mode + changes | step 10 | CodeMirror visible + full content equals the post-edit content | asserted |
| 9 Save and Discard remain **active** | both active | step 11 | both visible AND **enabled** | asserted |

### Axis 2 — Analyst additions
- **ELITEA-1853**: assert Save/Discard are not merely visible but **disabled**
  after the revert — the case only says "visible", but `hasUnsavedChanges`
  returning to false is the product's own statement that the revert really
  reset the edit state (a "content looks reverted but state is still dirty"
  regression would pass a visibility-only check).
- **ELITEA-1853**: assert content is **byte-equal to the captured original**,
  not merely that `# temp change` is gone — catches a revert that drops or
  mangles unrelated lines.
- **Both rows**: assert the modal's Cancel/Discard **button labels** exactly
  (`Cancel` / `Discard`), so a label regression on the shared `DiscardButton`
  surfaces here.
- **Both rows**: assert no console errors across the flow (standard
  side-channel discipline; zero found live).

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket (subject to the known
   `#636` 404-on-teardown flake, already handled gracefully).

## Concrete Handles (discovered during exploration)

Editor-surface handles are the ELITEA-1851/1852 set (see
`test-specs/artifacts/l2_file-preview-open-editor-ui_ELITEA-1851.md`). New for
this family — **all six added this run** to `EliteaAI/EliteaUI` on
`automation/testids` (commit `EliteaAI/EliteaUI@d0b8a0c2`):

| Element | Locator (testid) | Provenance | Notes |
|---|---|---|---|
| Discard Warning dialog | `artifacts-preview-discard-warning-dialog` | **added this run** — `automation/testids` only (human cherry-pick to `main` pending) | `DiscardButton`'s own `Modal.BaseModal`; wired through the pre-existing `modalDataTestId` prop |
| Modal title | `artifacts-preview-discard-warning-title` | added this run | text is exactly `Warning` |
| Warning icon | `artifacts-preview-discard-warning-icon` | added this run | `titleIconTestId` pass-through added to `DiscardButton.jsx` this run |
| Modal X (close) | `artifacts-preview-discard-warning-close-button` | added this run | `closeButtonTestId` pass-through added this run |
| Modal Cancel | `artifacts-preview-discard-warning-cancel-button` | added this run | `cancelButtonTestId` pass-through added this run |
| Modal Discard (confirm) | `artifacts-preview-discard-warning-confirm-button` | added this run | pre-existing `confirmButtonDataTestId` prop; label = `WARNING_BUTTONS.DISCARD` = `Discard` |
| Header Discard button | `artifacts-preview-discard-button` | pre-existing (ELITEA-1851) | `is_file_preview_discard_enabled/disabled` already exist |
| Toast message | `toast-message` | pre-existing | used for the **absence** assertion (count 0) |

**Testid mechanism note.** `DiscardButton` is a **shared** component
(`src/[fsd]/shared/ui/button/`), so it carries **no** feature-scoped testid —
it takes caller-supplied testId props and the Artifacts call site
(`PreviewHeader.jsx`) supplies the `artifacts-preview-*` values. The four
props added this run use the compliant `<part>TestId` naming
(`cancelButtonTestId`, `closeButtonTestId`, `modalTitleTestId`,
`modalTitleIconTestId`); the three that already existed
(`dataTestId`, `modalDataTestId`, `confirmButtonDataTestId`) keep their legacy
`data`-prefixed names — pre-existing, not extended.

## Network Behavior
- **Discard fires no network request at all** (confirmed live: `handleDiscard`
  is a pure `setEditedContent('')` state reset — `FilePreviewCanvas/index.jsx`).
  Nothing to wait on; the waits are all product-state condition waits.

## Known Defects Found During Exploration
None for either case — both match live product behaviour exactly, including
the modal's element inventory and its message text.

## Blocked Steps
None.

## Automation Hints
- **The Discard button is disabled until the edit propagates.** `useCodeMirror`
  debounces `notifyChange` by 30 ms, so the parent's `hasUnsavedChanges`
  lags the DOM. Wait on `is_file_preview_discard_enabled()` (a real product
  state, not a sleep) before clicking Discard — this is a correctness guard,
  not a nicety (see the ELITEA-1855 AFS for what the same race caused there).
- Both rows share the whole prefix; implement as ONE parameterized spec.
- Confirmed live 2026-08-23 via pytest scratch runs against
  `http://localhost:5173`.
