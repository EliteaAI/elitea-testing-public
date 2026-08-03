# Test Case: File Preview/Edit – Markdown File Raw Tab Enables Editing with Save and Discard Active

## Metadata
- **TMS ID**: ELITEA-1858
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium` — same mapping as sibling ELITEA-1856)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1857/1858/1862, 2026-08-03)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (auth_state, localhost).
- A fresh bucket with a Markdown file exists whose first line is a heading
  (see § Test Data — same pattern as ELITEA-1857, NOT a shared "bucket-1").
  **This case MUTATES the file's content** (edits the heading, saves) — must
  NOT share a bucket/file with ELITEA-1857's read-only verification if both
  run in the same CI session.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Fresh bucket via `artifact_bucket` fixture + `project-background.md`
  uploaded via `ArtifactAPI.upload_file()` — same content shape as
  ELITEA-1857's AFS (heading `# Project Overview` on line 1, plus Scope/
  Architecture/Key Components sections). Original heading:
  `# Project Overview`. Updated heading: `# Project Overview Updated`
  (verbatim match to the case's stated values).
- Success notification text: **confirmed live** = `"File saved successfully"`
  (exact match — matches the case's stated text, no drift here; same toast
  testid/mechanism as ELITEA-1852's AFS documents: `success_toast_message`,
  `data-testid="toast-message"`).

## Test Steps
1. Open `project-background.md` via the "View/Edit file" icon (reuses
   ELITEA-1857's open flow — editor opens in Preview mode by default)
2. Verify the "Raw" toggle button is present, not yet pressed
3. Click the "Raw" toggle button
   - **Verify**: "Raw" becomes pressed (`aria-pressed="true"`), "Preview"
     becomes unpressed
4. Verify the content now renders via CodeMirror with line numbers
   (`.cm-lineNumbers`, scoped under the existing `artifacts-preview-code-editor`
   testid — same #579-sanctioned pattern as ELITEA-1851)
5. Verify Save and Discard remain **DISABLED** immediately after switching to
   Raw (no edit made yet — switching tabs alone is not an edit)
6. Click directly on the CodeMirror line containing `# Project Overview`
   (via `.cm-line` filtered by that text — see Automation Hints for why this
   is the reliable targeting technique, not `Control+Home`/arrow-key nav) and
   append `" Updated"` at the end of that line
7. Verify Save and Discard both transition to **ENABLED** the moment content
   differs from the loaded content
8. Click Save
   - **Verify**: a `POST .../artifacts/artifacts/default/{project}/{bucket}`
     request resolves 200
9. Verify a success toast reading exactly `"File saved successfully"` appears
10. Verify the editor **remains open** (does NOT close) and the render-mode
    toggle **auto-switches back to "Preview" (pressed)** — confirmed live:
    `isHtmlFile || isMdxFile || isMarkdownFile` branch of `handleSaveChanges`
    sets `renderMode` back to `RENDERED` instead of calling `onClose()`. This
    differs from the case's stated step 11 ("Reopen ... and click Preview
    tab") — see Known Defects; the live behavior needs no reopen.
11. Verify the updated heading "Project Overview Updated" is rendered in the
    Preview content **in the same session**, without navigating away
12. Verify Save/Discard **re-disable** once the save completes (content is
    no longer "unsaved" relative to the newly-persisted baseline)
13. Navigate away (back to the bucket's file table) and reopen
    `project-background.md`
    - **Verify**: editor reopens in Preview mode (default), showing the
      persisted `"Project Overview Updated"` heading — proves the change
      round-tripped through the backend, not just local component/session state

## Expected Results
- Raw tab enables editing with line numbers; Save/Discard enable only once an
  actual edit is made (not merely on tab-switch).
- Save persists via `POST .../artifacts/artifacts/default/{project}/{bucket}`.
- Toast text is exactly `"File saved successfully"`.
- Editor stays open after save (markdown/html/mdx branch) and auto-shows the
  updated content in Preview mode — stronger and smoother than the case's
  literal "reopen" wording (case-text drift, filed as clarification, see
  Known Defects).
- Save/Discard re-disable post-save.
- A genuine navigate-away-and-reopen also shows the persisted update,
  confirming backend persistence independent of the auto-switch behavior.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open project-background.md via View/Edit icon | editor opens in Preview mode | step 1 | Preview toggle pressed on open (reuses ELITEA-1857 flow) | asserted |
| 2 Verify Preview active with rendered Markdown | Preview active, Markdown rendered | step 1 | reuses ELITEA-1857 assertions | asserted *(not re-derived — covered by the sibling spec, same open flow)* |
| 3 Click Raw tab | Raw becomes active | step 3 | `aria-pressed` flips | asserted |
| 4 Raw active/highlighted, Preview inactive | Raw highlighted, Preview inactive | step 3 | same, both buttons checked | asserted |
| 5 File content shown as raw text with line numbers | raw content + line numbers visible | step 4 | `.cm-lineNumbers` present | asserted |
| 6 Save/Discard become ACTIVE/enabled | both enabled | step 5 (disabled pre-edit) + step 7 (enabled post-edit) | `is_disabled()` False after edit — **clarification-adjacent**: case implies Save/Discard activate simply from switching to Raw; live behavior is they stay disabled until an actual EDIT is made (switching tabs alone doesn't dirty the content) — this is the SAME `hasUnsavedChanges`-gated contract ELITEA-1851's AFS already documents for the open state, now confirmed to also gate the tab-switch moment. Not filed as a separate clarification (same root fact, already ticketed under #1108) — AFS asserts the correct live contract at both checkpoints (disabled right after switching, enabled right after editing). | asserted *(adapted — two checkpoints instead of one)* |
| 7 Click into line 1, change heading to "# Project Overview Updated" | heading changed | step 6 | `.cm-line` filtered by heading text, click + End + type | asserted *(adapted — see Automation Hints for why `.cm-line` targeting replaces the existing `edit_file_preview_content()` helper's `Control+Home`-based nav for this specific case)* |
| 8 Change visible in Raw editor | updated text shown | step 6 | typed text appears in `.cm-line` content | asserted |
| 9 Click Save | save completes | step 8 | POST resolves 200 | asserted |
| 10 Success notification "File saved successfully" | notification appears | step 9 | toast text exact match | asserted *(confirmed live — matches case text exactly)* |
| 11 Reopen file, click Preview tab | file reopened in Preview | step 10 | **clarification** — live behavior: editor never closes; Save auto-switches `renderMode` to `RENDERED` (Preview) without any reopen action. Filed `EliteaAI/elitea-testing-public#1111`. AFS asserts the live (stronger) contract: editor stays open, auto-shows Preview. | asserted *(live contract, not the case's literal "reopen")* |
| 12 Updated heading "# Project Overview Updated" rendered in Preview | updated heading shown | step 11 | rendered content contains "Project Overview Updated" | asserted |

### Axis 2 — Analyst additions
- Assert Save/Discard **re-disable** after a successful save — added: this is
  the exact "coverage gap" ELITEA-1852's AFS explicitly flagged as
  out-of-scope for its `.py`-file case (editor closes on save for code files,
  so the re-disabled state was never observable there); this markdown case
  DOES keep the editor open post-save, so it can close that gap. Confirmed
  live: both buttons `is_disabled() == True` immediately after the toast.
- Assert a genuine navigate-away-and-reopen shows the persisted change — added:
  stronger signal than the auto-switch-to-Preview behavior alone (which could
  in principle be pure client-side state); confirms the backend round-trip,
  same reasoning as ELITEA-1852's own reopen-and-verify step.
- Assert **no console errors** during the edit+save+auto-switch+reopen flow —
  added: standard side-channel discipline; zero found live.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket (subject to the
   known `#636` 404-on-teardown flake, already handled gracefully).

## Concrete Handles (discovered during exploration)

Shared editor-surface handles per ELITEA-1851's AFS (header, Save/Discard,
close, code-content, line numbers) and ELITEA-1857's AFS (mode-toggle group,
markdown-content wrapper) — not re-derived here. This case's own:

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Targeting a SPECIFIC known line for editing | `page.locator(".cm-line").filter(has_text="<line text>").first` then `.click()` then `keyboard.press("End")` then `keyboard.type(text)` | **Do NOT reuse the existing `edit_file_preview_content(text, line_index=0)` helper for this case.** That helper's `Control+Home` → `ArrowDown`×N → `End` nav works for ELITEA-1852 because that case only needs to hit "any known content line" (its own AFS says so explicitly) — but live-testing here showed `Control+Home` does not reliably move the cursor to true document start in this CodeMirror instance (a plain `.click()` lands wherever the pointer's bounding-box center falls, and `Control+Home` did not correct it — confirmed by a live repro where the edit landed on paragraph 2 instead of the line-1 heading). Filtering `.cm-line` by the exact target text and clicking that specific line element is deterministic regardless of scroll position or click-target ambiguity. This is page-object-method scope, not a raw handle in the test file — implementer should add a new method (e.g. `edit_file_preview_line_containing(match_text, append_text)`) rather than inlining `.cm-line` in the spec. |
| Save network wait | `page.expect_response(lambda r: "/artifacts/artifacts/default/" in r.url and r.request.method == "POST")` | same mechanism as the existing `click_file_preview_save()` method (ELITEA-1852) — reuse as-is |
| Toast | `success_toast_message` (`data-testid="toast-message"`) — **EXISTS, reused**, same as ELITEA-1852's AFS documents | confirmed live, text = `"File saved successfully"` |

## Network Behavior
- Save fires `createArtifact` (RTK Query mutation, `POST .../artifacts/artifacts/default/{project}/{bucket}`) — implementer waits on this response, not a fixed sleep.
- Confirmed live: 200 response, no errors, saved bytes round-trip verified
  via a direct `ArtifactAPI.get_file()` read (ground-truth check, independent
  of the DOM).

## Known Defects Found During Exploration
- **[CLARIFICATION]** Case step 11 describes "reopen the file and click
  Preview tab" — live behavior is that the editor never closes after Save
  for a markdown file; it auto-switches its render-mode toggle to "Preview"
  in place. Filed `EliteaAI/elitea-testing-public#1111`. Case-text drift, not
  a functional defect — the live behavior is smoother (no reopen friction)
  and the AFS asserts it directly, plus adds a genuine navigate-away-and-back
  reopen as a stronger persistence check.

## Blocked Steps
None.

## Automation Hints
- Reuses ELITEA-1857's open-editor-in-Preview-mode flow and shares the
  mode-toggle-group / markdown-content-wrapper testids/locators that case's
  AFS specs — implement once, both specs consume the same page-object methods.
- New page-object method recommended: `edit_file_preview_line_containing(match_text, append_text)`
  using the `.cm-line` filter-and-click technique above, rather than reusing
  `edit_file_preview_content()`'s index-based nav for this line-specific case.
- Wait strategy throughout: network response waits (`expect_response`) for
  Save, no fixed sleeps, per `.agents/testing.md`'s no-sleep rule.
- Confirmed live via a direct `playwright.sync_api` scratch script (MCP
  server unreachable this session, same recurring gap as ELITEA-1851/1852/1856
  and ELITEA-1857 — see `_surface.md`) — API-seeded bucket/file via
  `ArtifactAPI`, full edit→save→verify→reopen cycle exercised twice (once
  with the flawed `Control+Home` nav which surfaced the targeting issue
  documented above, once corrected with `.cm-line` filtering, both runs'
  results cross-checked against a direct `ArtifactAPI.get_file()` read for
  ground truth). Screenshots:
  `automation/test-results/screenshots/FINAL-1858-post-save.png`,
  `automation/test-results/screenshots/FINAL-1858-reopened.png`.
