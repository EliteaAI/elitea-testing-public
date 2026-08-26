# Test Case: File Preview/Edit – Switching Between Preview and Raw Tabs (ELITEA-1861)

## Metadata
- **TMS ID**: ELITEA-1861
- **Linked Story**: none
- **Priority**: l3 (`priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (analyst slot, cluster dispatch, batch `artifacts-w05`, 2026-08-23)
- **Status**: ready-for-automation
- **Clarification filed**: `EliteaAI/elitea-testing-public#1690` (steps 3/4 case-text drift)

## What this case is, and why it is not already covered

This is the **round-trip** case: Preview → Raw → **Preview again**, with the
original content intact and the button states checked at every point. It is
read-only — no edit, no modal, no save.

Two merged specs touch adjacent ground and neither covers the round trip:

| Merged spec | Covers | Does NOT cover |
|---|---|---|
| `test_artifacts_file_preview_markdown_default_mode.py` (ELITEA-1857) | Preview is the default; rendered structure; Save/Discard disabled; no input accepted | any tab switching at all |
| `test_artifacts_file_preview_markdown_raw_edit_save.py` (ELITEA-1858) | Preview → **Raw** switch; line numbers; Save/Discard still disabled after the switch | the switch **back** to Preview; content preservation across a round trip |

The uncovered observable is **idempotence of tab switching** — that returning
to Preview restores the rendered branch, and that the content survives the
round trip byte-for-byte. Neither spec asserts it, so this is
`ready-for-automation` (a fresh spec), **not** `extend-existing`: there is no
single covering spec to extend, and folding a read-only round-trip assertion
into ELITEA-1858's edit-and-save flow would blur two different subjects.

**Reuse everything.** Every handle and page-object method this case needs
already exists — no new testid work. The steps that overlap ELITEA-1857/1858
(steps 1-3) are deliberately re-asserted here because they are this case's own
*baseline*, not because they are uncovered.

## Preconditions
- User is logged in (auth_state, localhost).
- A fresh bucket (via the `artifact_bucket` fixture) containing
  `project-background.md` uploaded through `ArtifactAPI.upload_file()` with
  `content_type="text/markdown"`. The case's "bucket-1" is the case author's
  own environment; no such fixture exists in this suite.
- **This case never mutates anything**, so it may safely share a bucket with
  other read-only cases if the implementer wants to economise — but the
  default `artifact_bucket` fixture per test is fine and simpler.

## Test Data
### generate-per-test (fixture-seeded, fixture-torn-down)
- Bucket: `artifact_bucket` fixture instance.
- File: `project-background.md`, same content constant as the merged
  ELITEA-1857/1858 specs (headings + bold + bullet list) — it exercises every
  rendered-Markdown element the Preview assertions check:
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

## Test Steps

1. Seed bucket + file via API; navigate to the bucket; open
   `project-background.md` via the "View/Edit file" icon.
   - **Verify**: the editor panel opens.
2. **Verify the Preview default** (case step 2):
   - Toggle state reads `{"rendered": "true", "code": "false"}`.
   - The rendered Markdown wrapper (`file_preview_markdown_content`) is visible.
   - The CodeMirror content is **not mounted** — `file_preview_code_content.to_have_count(0)`.
   - Save and Discard are both **disabled**.
3. Click the **Raw** toggle (`click_file_preview_mode_toggle_code`) — case step 3:
   - **Verify**: toggle state reads `{"rendered": "false", "code": "true"}`.
   - **Verify**: the line-number gutter is visible (`is_code_editor_line_numbers_visible`).
   - **Verify**: the rendered Markdown wrapper is **unmounted** — `file_preview_markdown_content.to_have_count(0)`.
   - **Capture** the raw content text (`get_file_preview_content_text`) — the round-trip oracle.
   - **Verify**: Save and Discard are **still disabled**. *(The case says they "become active" — they do not; see `#1690`. Assert the live contract.)*
4. Click the **Preview** toggle (`click_file_preview_mode_toggle_rendered`) — case step 4:
   - **Verify**: toggle state reads `{"rendered": "true", "code": "false"}`.
   - **Verify**: the CodeMirror content is **unmounted** — `file_preview_code_content.to_have_count(0)`.
   - **Verify**: real rendered Markdown structure is back — the wrapper's
     inner HTML contains `<h1`, `<h2`, a bold element, and `<ul`/`<li`
     (i.e. rendered elements, not raw `#`/`**`/`-` syntax).
   - **Verify**: Save and Discard are **still disabled**. *(Case says "become inactive again"; they were never active — `#1690`.)*
5. Click **Raw** once more and **verify the original content is intact** —
   `get_file_preview_content_text()` is **byte-equal** to the text captured in
   step 3 (case step 5).
6. **Side channel**: no console errors across the whole flow (observed clean live).

## Concrete Handles — all pre-existing, zero new testid work

| Element | Page-object field / method (`automation/pages/artifacts_page.py`) | testid | Provenance |
|---|---|---|---|
| Render-mode toggle group | `file_preview_mode_toggle_group` | `artifacts-preview-mode-toggle-group` | on `automation/testids` (ELITEA-1857) |
| "Preview" (rendered) toggle | `file_preview_mode_toggle_rendered` | `artifacts-preview-mode-toggle-rendered` | on `automation/testids` (ELITEA-1857) |
| "Raw" (code) toggle | `file_preview_mode_toggle_code` | `artifacts-preview-mode-toggle-code` | on `automation/testids` (ELITEA-1857) |
| Toggle state reader | `get_file_preview_mode_toggle_state()` | (reads `aria-pressed`) | pre-existing |
| Switch Raw / Preview | `click_file_preview_mode_toggle_code()` / `click_file_preview_mode_toggle_rendered()` | — | pre-existing (both already wait on `aria-pressed` becoming `true`) |
| Rendered Markdown wrapper | `file_preview_markdown_content` | `artifacts-preview-markdown-content` | on `automation/testids` (ELITEA-1857) |
| Rendered HTML / text readers | `get_file_preview_markdown_content_html()` / `_text()` | — | pre-existing |
| CodeMirror content | `file_preview_code_content` | `artifacts-preview-code-content` | on `automation/testids` |
| Raw content text reader | `get_file_preview_content_text()` | — | pre-existing — see newline gotcha |
| Line-number gutter | `is_code_editor_line_numbers_visible()` | `artifacts-preview-code-editor` parent + scoped `.cm-lineNumbers` (#579 sanctioned) | pre-existing |
| Save/Discard enablement | `is_file_preview_save_disabled()` / `is_file_preview_discard_disabled()` | — | pre-existing |

**No new testids are required.** Every handle above was exercised live in this
analysis run.

## Automation Hints

- **The two content branches are mutually exclusive MOUNTS, not
  show/hide.** Live-confirmed both ways: in Preview,
  `file_preview_code_content.count() == 0`; in Raw,
  `file_preview_markdown_content.count() == 0`. So the correct assertion for
  "the other view is gone" is `to_have_count(0)`, **not**
  `not_to_be_visible()` on a mounted-but-hidden node.
- **⚠ `get_file_preview_content_text()` returns the editor text with NO line
  separators** (CodeMirror `.cm-content` `text_content()` concatenation).
  Live sample: `'# Project OverviewThis is a **bold** statement…'`. Harmless
  for this case — the round-trip check is whole-content byte-equality, which
  is exactly the right shape — but do not try to index lines out of it.
- `click_file_preview_mode_toggle_code/rendered()` already wait on
  `aria-pressed == "true"`, so no extra wait is needed after a switch.
- This case makes **no network request** beyond the initial file load — the
  toggle is pure client-side render-branch switching. Don't wait on a response.
- Markers: `ui`, `regression`, `p2` (matches l3 / `priority: medium`).

## Coverage Map

### Axis 1 — every case element accounted for

| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` (localhost bypass) | fixture | covered |
| Precondition: bucket-1 / project-background.md | — | `artifact_bucket` + `ArtifactAPI.upload_file` seeding | Preconditions | **adapted** — "bucket-1" is the author's env |
| Step 1 — open via "View/Edit file" icon | Editor opens | `open_file_in_editor` | step 1 | covered |
| Step 2 — Preview active by default; Save/Discard inactive | Preview active; buttons inactive | toggle-state read + both-disabled assertions (+ rendered wrapper mounted, CodeMirror count 0) | step 2 | covered |
| Step 3 — click Raw: raw content with line numbers; **Save/Discard become active** | Raw active; line numbers; buttons active | toggle-state read + line-number gutter + Markdown wrapper count 0 asserted as written; **button state asserted as STILL DISABLED (live contract)** | step 3 | **clarification** — `#1690`; both buttons are gated on `hasUnsavedChanges`, not on render mode, and no edit is made in this case. Asserting "active" would be reverse-masking. |
| Step 4 — click Preview: formatted Markdown; **Save/Discard become inactive again** | Preview active; rendered Markdown; buttons inactive | toggle-state read + rendered `<h1>/<h2>/bold/<ul><li>` structure + CodeMirror count 0; buttons asserted disabled (correct outcome, incorrect premise) | step 4 | **clarification** — `#1690`; the buttons were never active, so they cannot "become inactive again". Final state asserted matches the case; the transition described does not occur. |
| Step 5 — switching tabs does not lose the original content | Original content intact after switching | byte-equality of the raw text before vs after the full Preview round trip | step 5 | covered |

### Axis 2 — observables asserted BEYOND the case text

| Extra observable | Why (grounded) |
|---|---|
| CodeMirror **unmounted** in Preview; Markdown wrapper **unmounted** in Raw | The case says the right view "is shown"; the stronger, machine-checkable form is that the other branch is gone. Live-confirmed as a real unmount (count 0), which also protects against a regression that renders both. |
| Rendered structure is real `<h1>/<h2>/<strong>/<ul><li>`, not raw syntax | "Formatted Markdown is shown" is otherwise satisfiable by a view that just prints the source text. Same assertion shape as the merged ELITEA-1857 spec. |
| Byte-equality (not substring) for the content round-trip | "Does not lose the original content" is only meaningfully checked whole — a substring check would pass even if the round trip dropped or duplicated lines. |
| No console errors | Standard side-channel check; observed clean live. |

## Blocked Steps
None.

## Known Defects
None. One case-text clarification: `EliteaAI/elitea-testing-public#1690`
(steps 3/4). No product defect — the live behaviour is correct.
