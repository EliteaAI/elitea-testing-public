# Test Case Family: File Preview/Edit – Markdown **Raw tab** Discard Warning modal exit paths (ELITEA-1859 / ELITEA-1860)

## Metadata
- **TMS IDs**: ELITEA-1859, ELITEA-1860 (**family AFS** — one flow, two exit variants)
- **Linked Story**: none
- **Priority**: l3 (both cases `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (analyst slot, cluster dispatch, batch `artifacts-w05`, 2026-08-23)
- **Status**: ready-for-automation
- **Clarification filed**: `EliteaAI/elitea-testing-public#1689` (ELITEA-1859 step 8 case-text drift)

## Why one family AFS

ELITEA-1859 and ELITEA-1860 are the two exit variants of a **single flow**:
open a **Markdown** file → switch to the **Raw** tab → replace line 1 → click
the header **Discard** button → the shared `DiscardButton`'s built-in
**Warning** modal opens. Everything up to and including the modal-open
assertion is byte-identical between the two cases; they diverge on exactly
one click (the modal's **Discard** vs its **Cancel**) and on the resulting
content / button state. Implement as ONE parameterized spec, one row per
case, each row asserting its OWN expected values.

## Relationship to the already-merged ELITEA-1853/1854 spec — READ THIS FIRST

`automation/tests/ui/artifacts/test_artifacts_file_preview_discard_warning.py`
(merged) already covers the **same two modal exit paths** — but for a
**`.py` file in the editor's default CODE branch**, which has **no
render-mode toggle at all** (`modeTogglerAvailable` is false for code files).

These two cases are **not** covered by it, and the difference is not
cosmetic: the whole point of ELITEA-1859/1860 is the **Markdown + Raw-tab**
dimension, i.e. that the render-mode toggle **stays on Raw** across the
discard/cancel round-trip rather than snapping back to Preview. That toggle
does not exist in the 1853/1854 flow, so it is asserted nowhere today.

**Verdict: `ready-for-automation`, NOT `extend-existing`.** Extending the
1853/1854 spec would mean parameterizing it over file type *and* exit path
(4 rows, two of which have no toggle to assert) — a near-rewrite of a merged
spec, which the analyst contract sends back to `ready-for-automation`. Write
a separate spec; **reuse the page objects wholesale** (every handle below
already exists — no new testid work at all).

## Preconditions
- User is logged in (auth_state, localhost).
- A fresh bucket (via the `artifact_bucket` fixture) containing
  `project-background.md` uploaded through `ArtifactAPI.upload_file()` with
  `content_type="text/markdown"`.
  **NOT a shared "bucket-1"** — no such fixture exists in this suite (the
  case's "bucket-1" is the case author's own environment). Both rows mutate
  in-editor state, so each row seeds its own bucket.

## Test Data
### generate-per-test (fixture-seeded, fixture-torn-down)
- Bucket: `artifact_bucket` fixture instance.
- File: `project-background.md`, seeded with the **same content constant the
  merged ELITEA-1857/1858 specs use** (headings + bold + bullet list) so line 1
  is the unique heading `# Project Overview`:
  ```python
  FILE_CONTENT = (
      b"# Project Overview\n\n"
      b"This is a **bold** statement about the project.\n\n"
      b"## Scope\n\n"
      b"Covers the automation of file preview features.\n\n"
      b"## Key Components\n\n"
      b"- Component A\n"
      b"- Component B\n"
  )
  ```
- Original heading: `# Project Overview` · Replacement heading: `# Modified Heading`
- Modal message (confirmed live, exact): `Are you sure you want to discard changes?`
  (from `ModalConstants.WARNING_MESSAGES.DISCARD_CHANGES`); title exactly `Warning`.

## Parameter table (one row per TMS case)

| Row (case) | Modal button clicked | Expected content after | Expected Save/Discard state after | Render-mode toggle after | Toast |
|---|---|---|---|---|---|
| **ELITEA-1859** | `artifacts-preview-discard-warning-confirm-button` ("Discard") | `# Modified Heading` **absent**, `# Project Overview` back; content **byte-equal to the original** | both **visible**, both **disabled** (`hasUnsavedChanges` back to false) — **NOT "still active" as the case text says**, see #1689 | **still Raw** (`rendered=false, code=true`) | **none** (count 0) |
| **ELITEA-1860** | `artifacts-preview-discard-warning-cancel-button` ("Cancel") | `# Modified Heading` **still present**; content **byte-equal to the post-edit baseline** | both visible, both **enabled** | **still Raw** (`rendered=false, code=true`) | n/a (not asserted by the case) |

## Test Steps (shared through step 7, then per-row)

1. Seed bucket + file via API; navigate to the bucket.
2. Open `project-background.md` via the "View/Edit file" icon.
   - **Verify**: editor opens; render-mode toggle reads `{"rendered": "true", "code": "false"}` (Preview default).
3. Click the **Raw** toggle (`click_file_preview_mode_toggle_code`).
   - **Verify**: toggle reads `{"rendered": "false", "code": "true"}`.
4. Capture the editor's original content text (`get_file_preview_content_text`) — the revert oracle for the 1859 row.
5. **Replace line 1**: click the `.cm-line` containing `# Project Overview`, press `End`, press `Shift+Home`, type `# Modified Heading`.
   - **Verify** (web-first): content contains `# Modified Heading` and **no longer** contains `# Project Overview`.
   - Capture the post-edit content text — the preservation oracle for the 1860 row.
6. **Verify**: Save and Discard both became **enabled**. *(Not decoration — `useCodeMirror` debounces `notifyChange` by 30 ms, so the parent's `hasUnsavedChanges` lags the typed DOM text. This is the correctness guard before anything dirty-state-dependent; see Automation Hints.)*
7. Click the header **Discard** button (`click_file_preview_discard`).
   - **Verify**: the Warning modal is visible; title is exactly `Warning`; the dialog contains `Are you sure you want to discard changes?`.
8. **Per row** — click this row's modal button (`confirm_file_preview_discard` / `cancel_file_preview_discard`).
   - **Verify**: the modal closes (`to_have_count(0)`).
9. **Per row** — verify the content per the parameter table, **web-first first, then byte-equality** (see Automation Hints — the revert lags the modal close).
10. **Verify (both rows)**: the editor is still open (`file_preview_file_path` visible) **and the render-mode toggle is still on Raw** — `{"rendered": "false", "code": "true"}`. *This is the assertion that makes these cases distinct from ELITEA-1853/1854; do not drop it.*
11. **Verify (both rows)**: Save and Discard are still **visible**, in this row's expected enabled state per the parameter table.
12. **ELITEA-1859 only**: verify **no success notification** — `success_toast_message.to_have_count(0)`. Discarding is a pure client-side state reset: no network request, no toast.
13. **Side channel (both rows)**: no console errors across the whole flow (observed clean live).

## Concrete Handles — all pre-existing, zero new testid work

| Element | Page-object field / method (`automation/pages/artifacts_page.py`) | testid | Provenance |
|---|---|---|---|
| Render-mode toggle group | `file_preview_mode_toggle_group` | `artifacts-preview-mode-toggle-group` | on `automation/testids` (ELITEA-1857) |
| "Preview" (rendered) toggle | `file_preview_mode_toggle_rendered` | `artifacts-preview-mode-toggle-rendered` | on `automation/testids` (ELITEA-1857) |
| "Raw" (code) toggle | `file_preview_mode_toggle_code` | `artifacts-preview-mode-toggle-code` | on `automation/testids` (ELITEA-1857) |
| Toggle state reader | `get_file_preview_mode_toggle_state()` → `{"rendered": .., "code": ..}` | (reads `aria-pressed` off the two testids) | pre-existing |
| Switch to Raw / Preview | `click_file_preview_mode_toggle_code()` / `click_file_preview_mode_toggle_rendered()` | — | pre-existing |
| CodeMirror content | `file_preview_code_content` | `artifacts-preview-code-content` | on `automation/testids` |
| Content text reader | `get_file_preview_content_text()` | — | pre-existing — **see newline gotcha below** |
| Header Discard button | `click_file_preview_discard()` | `artifacts-preview-discard-button` | on `automation/testids` (ELITEA-1853) |
| Warning dialog / title / icon / X / Cancel / Discard | `file_preview_discard_warning_dialog` · `_title` · `_icon` · `_close_button` · `_cancel_button` · `_confirm_button` | `artifacts-preview-discard-warning-*` | EliteaAI/EliteaUI@d0b8a0c2 on `automation/testids`, human cherry-pick pending |
| Modal exits | `confirm_file_preview_discard()` / `cancel_file_preview_discard()` | — | pre-existing (ELITEA-1853/1854) |
| Save/Discard enablement | `is_file_preview_save_enabled/_disabled()` · `is_file_preview_discard_enabled/_disabled()` | — | pre-existing |
| Editor file path (open-ness) | `file_preview_file_path` | `artifacts-preview-file-path` | on `automation/testids` |
| Success toast | `success_toast_message` | — | pre-existing |
| Line targeting | `ArtifactsPage.CM_LINE` (`.cm-line`, #579 sanctioned, scoped under the testid'd content parent) | — | pre-existing |

**No new testids are required for either case.** Every handle above was
exercised live in this analysis run.

## Automation Hints

- **Line REPLACEMENT needs a new helper — `edit_file_preview_line_containing()`
  only APPENDS.** These cases require *replacing* `# Project Overview` with
  `# Modified Heading`, not appending. Verified-live technique (this run):
  click the `.cm-line` filtered by the target text → `End` → **`Shift+Home`**
  → `type(new_text)`. Add it as a sibling page-object method (e.g.
  `replace_file_preview_line_containing(match_text, new_text)`) next to the
  existing appender, with the same `#579` docstring note — do **not** inline
  a raw `.cm-line` handle in the spec.
- **⚠ `get_file_preview_content_text()` returns the editor text with NO line
  separators** — CodeMirror's `.cm-content` `text_content()` concatenates
  lines. Live sample: `'# Project OverviewThis is a **bold** statement…'`.
  So `.splitlines()[0]` is **not** "line 1"; it is the whole document. Assert
  line-1 replacement via the `to_contain_text("# Modified Heading")` +
  `not_to_contain_text("# Project Overview")` pair (safe here — the original
  heading string occurs exactly once in the seeded content), and use the
  captured-baseline **byte-equality** comparisons for whole-content claims.
- **The discard revert LAGS the modal close.** `confirm_file_preview_discard()`
  returns as soon as the Warning modal hides, but CodeMirror's text is
  restored one React state round-trip later. A one-shot
  `get_file_preview_content_text()` at that moment still returns the EDITED
  text. Use a web-first auto-retrying assertion first
  (`expect(file_preview_code_content).not_to_contain_text("# Modified Heading")`),
  **then** read the text for byte-equality. Never a sleep.
- **Wait on Save/Discard becoming enabled after typing** (step 6) before
  clicking Discard — the 30 ms `notifyChange` debounce means the parent can
  still believe the editor is clean, and the header Discard would then be
  disabled/inert.
- Fresh bucket per row (both rows mutate in-editor state). `artifact_bucket`
  fixture teardown 404s are known/tracked (`#636`) and harmless.
- Markers: `ui`, `regression`, `p2` (matches l3 / `priority: medium`).

## Coverage Map

### Axis 1 — every case element accounted for

#### ELITEA-1859
| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` (localhost bypass) | fixture | covered |
| Precondition: bucket-1 / project-background.md with `# Project Overview` on line 1 | — | `artifact_bucket` + `ArtifactAPI.upload_file` seeding | Preconditions | **adapted** — "bucket-1" is the author's env; a fresh fixture bucket is the suite equivalent |
| Step 1 — open via "View/Edit file" icon | Editor opens | `open_file_in_editor` | step 2 | covered |
| Step 2 — click "Raw" tab | Raw tab is active | `click_file_preview_mode_toggle_code` + toggle-state read | step 3 | covered |
| Step 3 — change line 1 to `# Modified Heading` | Line 1 shows `# Modified Heading` | `Shift+Home` line replace + contain/not-contain pair | step 5 | covered |
| Step 4 — click "Discard" | Warning modal opens | `click_file_preview_discard` | step 7 | covered |
| Step 5 — modal shows `Are you sure you want to discard changes?` | Modal is visible | title + message assertions | step 7 | covered |
| Step 6 — click "Discard" in modal | Discard completes | `confirm_file_preview_discard` + modal count 0 | step 8 | covered |
| Step 7 — content reverts to `# Project Overview` | Original restored | web-first not-contain, then byte-equality vs captured original | step 9 | covered |
| Step 8 — editor remains open in Raw mode with Save/Discard **"still active"** | Editor in Raw with active buttons | editor-open + toggle-still-Raw asserted as written; **button state asserted as DISABLED (live contract)** | steps 10-11 | **clarification** — `#1689`; live product correctly re-disables both (`hasUnsavedChanges` reset). Asserting "active" would be reverse-masking. |
| Step 9 — no success notification | No notification | `success_toast_message.to_have_count(0)` | step 12 | covered |

#### ELITEA-1860
| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions | — | same fixture seeding | Preconditions | **adapted** (as above) |
| Step 1 — open via icon | Editor opens | `open_file_in_editor` | step 2 | covered |
| Step 2 — click "Raw" tab | Raw tab is active | toggle-state read | step 3 | covered |
| Step 3 — modify line 1 to `# Modified Heading` | Change visible | line replace + contain/not-contain pair | step 5 | covered |
| Step 4 — click "Discard" | Warning modal opens | `click_file_preview_discard` | step 7 | covered |
| Step 5 — Warning modal opens | Modal is visible | dialog visible + title `Warning` | step 7 | covered |
| Step 6 — click "Cancel" | Modal closes | `cancel_file_preview_discard` | step 8 | covered |
| Step 7 — modal closes | Modal no longer visible | `to_have_count(0)` | step 8 | covered |
| Step 8 — editor remains in Raw mode with `# Modified Heading` on line 1 | Unsaved change preserved | toggle-still-Raw + contain-text + byte-equality vs post-edit baseline | steps 9-10 | covered |
| Step 9 — change has not been lost | `# Modified Heading` visible | byte-equality vs post-edit baseline | step 9 | covered |

### Axis 2 — observables asserted BEYOND the case text

| Extra observable | Row | Why (grounded) |
|---|---|---|
| Preview is the toggle's default before the Raw click | both | Cheap guard that the file really is on the toggle-bearing Markdown branch; a regression to CODE-branch rendering would otherwise make "click Raw" silently meaningless. |
| Content byte-equality (vs original for 1859, vs post-edit baseline for 1860) | both | Stronger than "the marker is/isn't there" — catches a discard/cancel that drops or mangles unrelated lines. Same reasoning as the merged ELITEA-1853/1854 spec's Axis 2. |
| Save/Discard **enabled** immediately after the edit | both | The product's own signal that the dirty state propagated past the 30 ms debounce — a correctness guard, not a nicety. |
| Save/Discard **disabled** after confirm-discard | 1859 | The case says "active" (wrong, `#1689`); `hasUnsavedChanges → false` is the product's own statement that the revert really reset the edit state. |
| Render-mode toggle still on **Raw** after the exit | both | The case says "remains in Raw mode" in prose; asserting the toggle's `aria-pressed` pair is the only machine-checkable form of it — and it is the sole observable distinguishing these cases from the merged ELITEA-1853/1854 pair. |
| No console errors | both | Standard side-channel check; observed clean live. |

## Blocked Steps
None.

## Known Defects
None. One case-text clarification: `EliteaAI/elitea-testing-public#1689`
(ELITEA-1859 step 8). No product defect — the live behaviour is correct.
