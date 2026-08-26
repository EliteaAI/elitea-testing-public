# Test Case: Upload file icon allows importing content into the Project Background editor

## Metadata
- **TMS ID**: ELITEA-2271
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2271.md`
  (snapshot; TMS module `settings-project-params`; TMS file under
  `settings/project-params/`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter). **pytest marker: `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Classification note — declared divergence (reverse-masking guard)

The case calls the target the **"Project Background editor"**; no section of that name
exists — it is the Project Context editor at `/settings/project-context/edit`. Filed
module-wide as clarification **#1792** (ELITEA-2266 analysis); not re-filed.

Case step 1 says "Navigate to Settings → Project Context" and step 2 "Click the upload
file icon button **next to the editor**" — the icon lives in the *editor's* toolbar, so
the editor must be opened first (empty state → **Create**). The test walks that real
user path.

The control's accessible tooltip is `Import from markdown file` and its `<input>`
declares `accept=".md,text/markdown"` — "a supported text or markdown file"
(case step 4) means a `.md` file here.

## Preconditions
- User is logged in (localhost dev-token auth).
- Non-Public project (`${ELITEA_PROJECT_ID}` = 399 "Private").
- **No Project Context exists**, so **Create** opens an empty editor and the imported
  content is unambiguously the file's. `clean_project_context` establishes and tears
  this down, tolerating the API's 404.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399` ("Private").

### static fixture (committed with this case)
- `test-data/project-context/elitea-2271-import.md` — a small markdown file with a
  heading, two bullets and a plain paragraph:

  ```markdown
  # Imported Project Background

  - Imported bullet one
  - Imported bullet two

  Imported plain text line.
  ```

  Committed rather than generated per run so the expected content is a literal file the
  reviewer can read, and so the assertion compares the editor against the file's own
  bytes read from disk (not against a duplicated string constant).

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Nothing | — | The file is handed to the product's own `<input type="file">` through Playwright's file-chooser (the same gesture a user's OS picker performs). The product's `FileReader` parses it; every asserted value — the editor lines, the char counter, the dirty state — is produced by the product. |

`expect_file_chooser` is **not** a substitution: it intercepts the browser's native OS
picker (which Playwright cannot drive), leaving the application's `handleImportClick` /
`handleFileUpload` path completely intact. No `page.route`, `route.fulfill`,
`monkeypatch` or `page.evaluate`.

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Empty-state **Create** | `project-context-create-button` | on-main ✓ |
| **Import from markdown file** icon | `project-context-import-button` | on `automation/testids` (EliteaAI/EliteaUI@b05bbc9a) |
| File picker | Playwright `page.expect_file_chooser()` | native browser event — no DOM handle needed (the `<input>` is `hidden` and has no testid; adding one would be an unreferenced testid, #511) |
| Editor (CodeMirror) | `project-context-editor-content` | on-main ✓ |
| Editor wrapper (scope for `.cm-line`) | `project-context-editor-wrapper` | on `automation/testids` only |
| Character counter | `project-context-char-counter` | on-main ✓ |
| Save | `project-context-save-button` | on-main ✓ |

## Test Steps

1. **Setup** — `clean_project_context` deletes any existing context (tolerating 404).
2. Navigate to `${BASE_URL}/settings/project-context` and click **Create**
   (case step 1).
   - **Verify**: URL is `${BASE_URL}/settings/project-context/edit`, the editor is
     visible and **empty**.
   - **Verify**: Save is **disabled** (nothing dirty).
3. **Click the upload file icon** and **a file picker opens** (case steps 2–3).
   - Click `project-context-import-button` inside a `page.expect_file_chooser()` block.
   - **Verify**: the file-chooser event fired — the control responded by opening a
     picker. **Verify**: the chooser is single-file (`is_multiple()` is `False`),
     matching the product's `files?.[0]` handling.
4. **Select a supported markdown file** (case step 4).
   - `set_files(test-data/project-context/elitea-2271-import.md)`.
   - **Verify**: the action completes without error (no toast error; the product's
     only error path here is the >2500-char guard, which this file does not trip).
5. **The file contents are imported into the editor** (case step 5).
   - **Verify**: the editor's rendered `.cm-line` list equals the file's own text read
     from disk, split on `\n` — heading, blank line, both bullets, blank line,
     paragraph, trailing empty line — i.e. the content was imported **verbatim**,
     markdown syntax characters included.
   - **Verify**: the character counter now reads `2500 - len(file_text)` characters left
     (whitespace-normalised) — the product counted the imported text, so the import
     reached the editor's real state and not just its DOM.
   - **Verify**: Save is now **enabled** — the import set the dirty flag
     (`setIsDirty(true)` in `handleFileUpload`).
6. **The imported content is editable** (case step 6 / expected final state).
   - Type one extra character at the end.
   - **Verify**: the editor's last line now carries that character (the cursor lands at
     the end of the imported text — confirmed live).
   - **Verify**: the character counter dropped by exactly one.
7. **No console errors** across the whole flow (Axis 2 addition, project convention).

## Coverage Map

### Axis 1 — the case's own elements

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: user logged in | setup | `auth_state` |
| Step 1 — Navigate to Settings → Project Context | asserted | Step 2 — page loads, Create opens the editor at the expected route |
| Step 2 — Click the upload file icon next to the editor | asserted | Step 3 — the click fires the file-chooser event |
| Step 3 — a file picker opens | asserted | Step 3 — `expect_file_chooser` resolved; single-file chooser |
| Step 4 — Select a supported text or markdown file | asserted | Step 4 — `.md` file set on the chooser, no error surfaced |
| Step 5 — File contents imported into the editor | asserted | Step 5 — editor lines == the file's bytes; char counter reflects the imported length |
| Step 6 — imported content is editable | asserted | Step 6 — extra character lands, counter drops |
| Expected final state — imported content is editable | asserted | Step 6 (same) |

### Axis 2 — additions beyond the case

| Addition | Why it is grounded |
|---|---|
| Editor empty and Save disabled before the import | without a known-empty baseline, "the contents are imported" cannot distinguish an import from pre-existing content |
| Character counter equals `2500 - len(file)` | reads the product's own computed content length, so the assertion cannot pass on a DOM-only render |
| Save becomes enabled after import | the import's dirty-state side effect; makes "imported into the editor" mean the editor's state, not just its text nodes |
| Chooser is single-file | the product handles `files?.[0]` only; pins that contract |
| No console errors | project convention on this surface |

## Automation Hints
- `page.expect_file_chooser()` must wrap the **click**; the input is `hidden` and
  clicked programmatically by `handleImportClick`, which still produces the chooser
  event.
- The product normalises CRLF/CR to `\n` before setting content. The committed fixture
  is LF-only, so the comparison is direct; keep it that way (a `.gitattributes`-driven
  CRLF checkout would otherwise shift the assertion).
- The file's trailing newline yields a final **empty** `.cm-line` — expected; compare
  against `file_text.split("\n")`, which produces the same trailing `""`.
- Import **replaces** the editor's content outright (`setContent(text)`), it does not
  append — confirmed live against a non-empty editor.

## Blocked Steps
None.
