# Test Case: File Preview/Edit – Edit File Content and Save Changes Successfully

## Metadata
- **TMS ID**: ELITEA-1852
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1851/1852/1856, 2026-08-02)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (auth_state, localhost).
- A fresh bucket with a previewable text file exists (see § Test Data — same
  pattern as ELITEA-1851, NOT a shared "bucket-1").

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Fresh bucket via `artifact_bucket` fixture + `machine_learning.py` uploaded
  via `ArtifactAPI.upload_file()` — same seeding as ELITEA-1851. **This case
  MUTATES the file's content** (adds a line, saves) — it must NOT share a
  bucket/file with ELITEA-1851's read-only verification if both run in the
  same CI session; each gets its own `artifact_bucket` fixture instance.
- Edit line: any existing line in the uploaded content works — the case's
  "line 17" is a coordinate on the case-author's own file, not a fixed
  requirement; the implementer should target a **known, non-empty line**
  from the fixture's own uploaded content, or simply the first content line
  for wait-free targeting via keyboard nav (`Home` → arrow-down N times →
  `End` → type). Confirmed live: content need not be exactly 18.5 KB.
- Added text: `"# edited line"` (verbatim, matches case).
- Success notification text: **confirmed live** = `"File saved successfully"`
  (exact match — see Concrete Handles; this DOES match the case's stated text).

## Test Steps
1. Navigate to Artifacts, open `machine_learning.py` in the fixture bucket via
   the "View/Edit file" icon (reuses ELITEA-1851's open flow)
   - **Verify**: editor opens
2. Verify the editor is scrollable and content renders with line numbers
3. Click into the CodeMirror content area, navigate to a known content line
   - **Verify**: cursor lands in the editor (implicit — typing in the next step succeeds)
4. Type `"# edited line"` at the end of that line
5. Verify the edited text appears immediately in the editor
6. Verify the Save button transitions from disabled → **enabled/active** the
   moment the content differs from the loaded content (this is the "Save
   becomes active" behavior ELITEA-1851's case text describes prematurely —
   see that AFS's Coverage Map clarification; it correctly belongs here)
7. Click Save
8. Verify a success toast reading exactly `"File saved successfully"` appears
9. Verify the editor closes and the main panel returns to the bucket's file table
   (confirmed live: non-markdown/html/mdx files close the editor on save —
   `handleSaveChanges`'s `else { onClose(); }` branch, `FilePreviewCanvas/index.jsx:310-314`)
10. Verify the file row's "Last update" timestamp advanced (confirmed live:
    `03-08-2026, 02:17 AM` → `03-08-2026, 02:18 AM` across a real save)
11. Reopen `machine_learning.py` and verify `"# edited line"` is present in
    the reloaded content (persistence across a fresh fetch, not just in-memory state)

## Expected Results
- Edited text is visible immediately (client-side echo).
- Save persists via `POST` through `createArtifact` (`withOverwrite: true`) —
  confirmed live: file size changed 803 B → 816 B after save, consistent with
  the appended `# edited line` text.
- Toast text is exactly `"File saved successfully"`.
- Editor auto-closes after save (for a `.py`/code file — not markdown/html/mdx).
- File-row "Last update" timestamp reflects the save time.
- Reopening shows the persisted edit — proves the change round-tripped through
  the backend, not just local component state.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open machine_learning.py via View/Edit icon | editor opens | step 1 | editor UI renders | asserted |
| 2 Editor functional + scrollable, content+line numbers visible | fully functional | step 2 | `.cm-lineNumbers` present, content renders | asserted |
| 3 Click at line 17 | cursor at line 17 | step 3 | keyboard nav to a known content line (see Test Data — exact "line 17" not load-bearing) | asserted *(adapted)* |
| 4 Add "# edited line" | text appears | step 4 | typed text | asserted |
| 5 Edited text visible immediately | change visible in real time | step 5 | `get_by_text("# edited line")` count ≥ 1 | asserted |
| 6 Click Save | save completes | step 7 | POST fires, no error toast | asserted |
| 7 Green success notification "File saved successfully" | notification appears | step 8 | toast text exact match | asserted *(confirmed live — matches case text exactly, no drift here)* |
| 8 Editor closes, returns to file table | editor closes | step 9 | Save button no longer present; file table visible | asserted |
| 9 "Last update" timestamp updated | timestamp current | step 10 | row text date/time increases | asserted |
| 10 Reopen, verify saved change present | "# edited line" visible | step 11 | `get_by_text` on reopened content | asserted |

### Axis 2 — Analyst additions
- Assert the **file size on the row changes** after save (803 B → 816 B
  observed live) — added: a stronger persistence signal than the timestamp
  alone, catches a "toast lied, nothing actually saved" regression.
- Assert **no console errors** during the edit+save flow — added: standard
  side-channel discipline; zero found live.
- Assert Save/Discard **re-disable** after a successful save (since
  `editedContent` resets to `''` and `hasUnsavedChanges` becomes false again)
  — added: guards the same disabled-state contract ELITEA-1851 documents,
  now on the "after save" side of the cycle. Not directly observable here
  since the editor closes on save for code files — implementer should assert
  this via a markdown/html file variant if a future case exercises the
  render-mode branch that keeps the editor open post-save (`isHtmlFile ||
  isMdxFile || isMarkdownFile` branch, `FilePreviewCanvas/index.jsx:310-311`);
  out of scope for this `.py`-file case — noting as a coverage gap, not
  asserting here.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket (subject to the
   known `#636` 404-on-teardown flake, already handled gracefully).

## Concrete Handles (discovered during exploration)

Same editor-surface handles as ELITEA-1851's Concrete Handles table
(`test-specs/artifacts/l2_file-preview-open-editor-ui_ELITEA-1851.md`) — not
re-derived here to avoid duplication. This case additionally needs:

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| CodeMirror content (editable) | `contentTestId="artifacts-preview-code-content"` on `Field.CodeMirrorEditor` (see ELITEA-1851 AFS — same first-party mechanism, needed here for `.click()` + keyboard nav targeting instead of the untagged `.cm-content` class selector) | until added, `page.locator(".cm-content")` is the interim raw handle — **not** testid-compliant, implementer must add the prop before merging per locator policy |
| Save button | `artifacts-preview-save-button` (needed to assert disabled→enabled transition cleanly) | see ELITEA-1851 AFS |
| Success toast | **Implementer correction (Phase 2 — Explore):** the AFS's "no stable testid" claim was incomplete — `useToast`'s `toastInfo`/`toastSuccess` handlers all route through the SAME app-wide `<ToastComponent/>` mounted once at `src/[fsd]/app/root.jsx`, which renders `Toast.jsx`'s message `Box` with `data-testid="toast-message"` (confirmed live via source read). This is the EXACT SAME testid `artifacts_page.py`'s pre-existing `success_toast_message` `LocatorDescriptor` already uses for the upload-success toast (ELITEA-1826/1832) — reused as-is here, no new testid needed. `success_toast_message.text_content() == "File saved successfully"` replaces the AFS's proposed interim `get_by_text()` raw-text handle. | `success_toast_message` — EXISTS, reused |
| File row "Last update" cell | no per-cell testid (grid renders a generic `displayField` per `ARTIFACT_COLUMNS`, `ArtifactTable.jsx:53-64`) — read full row text via `artifacts-file-row` and match the date format `dd-MM-yyyy, hh:mm a` (confirmed live format) | acceptable: the row-level testid IS the stable anchor; parsing its text for the date substring is not a raw-selector violation (no new locator, just text parsing on an existing testid'd element) |

## Network Behavior
- Save fires `createArtifact` (RTK Query mutation) with `withOverwrite: true`
  — implementer should wait on this response (not a fixed sleep) before
  asserting the toast/editor-close, per `.agents/testing.md`'s no-sleep rule.
- Confirmed live: no error responses during a normal edit+save cycle.

## Known Defects Found During Exploration
None found for this case specifically (the Save-disabled clarification is
filed and asserted under ELITEA-1851, since that's the case whose text
mis-describes the pre-edit state).

## Blocked Steps
None.

## Automation Hints
- Reuses ELITEA-1851's open-editor flow — implementer should factor a shared
  `open_file_in_editor(bucket, filename)` page-object method both specs call,
  rather than duplicating the hover→click→verify sequence.
- Wait strategy: wait on the `createArtifact` response (network wait), not a
  timeout, before asserting the toast or the editor-closed state.
- Confirmed live via direct Playwright scratch script (MCP server unreachable
  this session, same as ELITEA-1851/1856 — see `_surface.md`). Screenshots:
  `automation/test-results/screenshots/ELITEA-1851-1852-1856-05..08-*.png`.
