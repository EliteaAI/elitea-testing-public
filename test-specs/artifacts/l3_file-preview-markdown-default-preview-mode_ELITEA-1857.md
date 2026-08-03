# Test Case: File Preview/Edit – Markdown File Opens in Preview Mode by Default with Save/Discard Inactive

## Metadata
- **TMS ID**: ELITEA-1857
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium` — same mapping as sibling ELITEA-1856)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1857/1858/1862, 2026-08-03)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (auth_state, localhost).
- A bucket exists containing a Markdown file with headings/bullets/bold text
  (`.md` extension — `AvailableFormatsEnum.MARKDOWN`). **Not** a shared literal
  "bucket-1" — see § Test Data (same reasoning as ELITEA-1851's AFS: no such
  fixture/bucket exists in the suite).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Fresh bucket via `artifact_bucket` fixture (`automation/fixtures/data_fixtures.py:453`)
  — unique name `autotest-<test-name>-<ts>`, deleted in fixture teardown
  (subject to the known `#636` teardown-404 flake — see Cleanup).
- `project-background.md` uploaded via `ArtifactAPI.upload_file()`
  (`automation/api/client.py:1292`) with content covering all four headings
  the case's Test Data table names, plus a bold span and a bullet list (the
  case's step 7 also requires verifying "bullet points, bold text"):
  ```markdown
  # Project Overview

  This is a **bold** statement about the project.

  ## Scope

  Covers the automation of file preview features.

  ## Architecture

  Uses a layered design.

  ## Key Components

  - Component A
  - Component B
  ```
- Detected language: confirmed live = `Markdown (detected)` for a `.md` file
  (`getLanguageFromFilename`, `EliteaUI/src/utils/filePreview.js`).

## Test Steps
1. Navigate to `${BASE_URL}/artifacts`, click the fixture bucket
   - **Verify**: file table shows `project-background.md`
2. Observe the `project-background.md` row (no hover required)
   - **Verify**: the "View/Edit file" icon is visible on the row
     unconditionally — it is **NOT** hover-gated (confirmed against source:
     `ArtifactRowActions.jsx` renders the Preview `IconButton` whenever
     `row.canPreview` is true, with no opacity/visibility/display CSS tied to
     a hover state — only a `background-color` hover highlight applies to
     the button itself. **Fix round 1 correction:** this AFS originally
     repeated the same "hidden before hover, visible after" drift already
     documented and left open in case-text-drift clarification
     EliteaAI/elitea-testing-public#994 for ELITEA-1851's row icon — that
     issue is still OPEN, i.e. the drift was never a defect to begin with,
     just stale case-text framing this AFS should not have re-asserted as
     "confirmed live")
3. Click the "View/Edit file" icon
   - **Verify**: editor panel opens
4. Verify the panel header shows the full path `<bucket-name>/project-background.md`
5. Verify the language label shows `Markdown (detected)`
6. Verify a render-mode toggle group is present with two buttons: "Preview"
   (pressed/active) and "Raw" (not pressed) — confirmed live via
   `aria-pressed="true"`/`"false"` on the two `ToggleButton`s
7. Verify the rendered Markdown content shows all four headings ("Project
   Overview", "Scope", "Architecture", "Key Components"), the bold span, and
   the bullet list — confirmed live via `<strong>`/`<b>` and `<ul><li>`
   elements present within the rendered content
8. Verify Save and Discard buttons are present **and both DISABLED**
9. Click inside the rendered content area and type text
   - **Verify**: the typed text never appears anywhere on the page (no input
     accepted — confirmed live: 0 matches for a distinctive typed marker string)
10. Verify the 3-dot (ellipsis) actions menu icon is present and clickable

## Expected Results
- Editor opens with the render-mode toggle defaulting to "Preview" (pressed)
  for a `.md` file — confirmed by `FilePreviewCanvas/index.jsx`'s open-effect:
  `setRenderMode(isMarkdownFile || ... ? RENDERED : CODE)`.
- Rendered Markdown shows the actual heading/bold/bullet structure, not raw text.
- Save/Discard both disabled pre-edit (same `disabled={isSaving || !hasUnsavedChanges}`
  gate documented in ELITEA-1851's AFS — reconfirmed here for a markdown file).
- No text can be typed into the rendered Preview — `canEdit` is
  `renderMode === CODE && !isImageFileType && fileContent`, false while in
  Preview (rendered) mode; the Markdown branch doesn't even mount an editable
  CodeMirror instance, it's a static `<Markdown>` render.
- 3-dot menu remains present and clickable in Preview mode.
- No console errors during open.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Artifacts, click bucket-1 | bucket selected | step 1 | file table visible | asserted *(fixture-generated bucket, not literal "bucket-1" — see Test Data)* |
| 2 Hover row → View/Edit icon appears | icon visible unconditionally, NOT hover-gated | step 2 | `is_visible()` True BEFORE any hover AND after — see EliteaAI/elitea-testing-public#994 | asserted *(case text implies hover-gating; live/source behavior is "always visible" — corrected in fix round 1, not a product defect, same pattern as #994)* |
| 3 Click icon → editor opens | editor panel opens | step 3 | Save/Discard render | asserted |
| 4 Header shows "bucket-1/project-background.md" | header shows correct path | step 4 | `artifacts-preview-file-path` text | asserted *(fixture bucket name, not literal "bucket-1")* |
| 5 Language label "Markdown (detected)" with dropdown | label present | step 5 | `artifacts-preview-language-select` text | asserted |
| 6 Two tabs "Preview"(active)/"Raw" present | both visible, Preview active | step 6 | toggle group `aria-pressed` state | asserted |
| 7 Preview tab highlighted/active | Preview highlighted | step 6 | same (`aria-pressed="true"` on the rendered-mode button) | asserted |
| 8 File content rendered as formatted Markdown (headings, bullets, bold) | rendered Markdown displayed | step 7 | four headings + `<strong>` + `<ul><li>` all present | asserted |
| 9 Save/Discard INACTIVE/greyed out in Preview | both disabled | step 8 | `is_disabled()` True for both | asserted |
| 10 Click + type in preview area → no cursor/no input | editing blocked | step 9 | typed marker string 0 occurrences anywhere on page | asserted |
| 11 No text cursor appears, no edits possible | editing blocked | step 9 | same | asserted |
| 12 3-dot menu still present/accessible | menu accessible | step 10 | `file-preview-overflow-menu-menu-button` visible + enabled | asserted |

### Axis 2 — Analyst additions
- Assert **no console errors** across the open flow — added: silent errors
  are the worst bugs (skill discipline); zero found live.
- Assert the render-mode toggle group's OTHER button ("Raw") is present but
  NOT pressed — added: strengthens step 6/7's "Preview active by default"
  claim into a genuine two-state check rather than only confirming the
  positive case.
- Assert the "View/Edit file" icon's visibility **both before and after**
  hover, not just "clickable after hovering" — added, but as a REGRESSION
  guard for the opposite of what the case text implies: **fix round 1
  correction**, the icon is visible unconditionally (not a hover-reveal state
  transition — see EliteaAI/elitea-testing-public#994). Asserting the
  pre-hover state too means a future accidental hover-gating regression would
  be caught, instead of only re-confirming the (never-doubted) post-hover
  state.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket automatically.
   **Known flake, reconfirmed live this session (3/3 buckets in this cluster,
   plus the shared project now shows 555 accumulated buckets)**: teardown 404s
   (tracked `#636`,
   `.agents/memory/qa-engineer/artifact_bucket_fixture_delete_silently_fails_404.md`)
   — already wrapped in try/except by the fixture, doesn't fail the test. The
   accumulation is now large enough (555 buckets in the `Private` project as of
   this session) that it may be worth a dedicated cleanup sweep outside this
   case's scope — flagged, not actioned here.

## Concrete Handles (discovered during exploration)

Shared editor-surface handles per ELITEA-1851's Concrete Handles table
(`test-specs/artifacts/l2_file-preview-open-editor-ui_ELITEA-1851.md`) — header,
language select, Save/Discard, close, 3-dot menu — reused as-is, not
re-derived here. This case's own (new, markdown-specific):

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Render-mode toggle group | **testid needed**: `artifacts-preview-mode-toggle-group` on the `ToggleButtonGroup` (`PreviewHeader.jsx`, currently only `aria-label="Render Mode Toggle"`, no `data-testid`) | scope both toggle buttons under this container |
| "Preview" toggle button (rendered mode) | **testid needed**: `artifacts-preview-mode-toggle-rendered` — on the `ToggleButton value="rendered"`. **Name it by the stable `value` prop, not the visible label** — the label text varies by file type (`Preview` for markdown/html/mdx, `Table` for CSV/TSV, `Diagram` for Mermaid), so a label-derived testid would be a state-conditional identity, which the locator policy forbids; the underlying mode (`rendered` vs `code`) is the stable identity. | state (`aria-pressed`) read directly off this testid'd element — same acceptable pattern as the project's existing `aria-invalid`/`Mui-checked` state reads chained off testid'd elements |
| "Raw" toggle button (code mode) | **testid needed**: `artifacts-preview-mode-toggle-code` — on the `ToggleButton value="code"` (always labeled "Raw" for every file type that has a toggler) | same `aria-pressed` state-read pattern |
| Rendered Markdown content wrapper | **testid needed**: `artifacts-preview-markdown-content` on `PreviewContent.jsx`'s `<Box sx={styles.markdownWrapper}><Markdown>{fileContent}</Markdown></Box>` (currently untagged) | verify headings/bold/bullets by `.text_content()` / `.inner_html()` scoped under this testid — text-parsing an existing testid'd element, not a new raw selector (same precedent as the "Last update" row-text-parsing pattern in ELITEA-1852's AFS); also the click target for the "attempt to type" negative-input check |

## Network Behavior
- No explicit network capture needed beyond the page's own file-content fetch
  (`useArtifactContentFetch`) — read-only view case, same as ELITEA-1851.

## Known Defects Found During Exploration
None for this case. Case text fully matches live behavior (default Preview
tab, Save/Discard disabled, no editing possible in Preview mode, rendered
headings/bold/bullets all confirmed live).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Extends `ArtifactsPage` (`automation/pages/artifacts_page.py`) — reuse
  `open_file_in_editor()` (already exists from ELITEA-1851/1852/1856) to
  reach the editor; add new methods/locators for the mode-toggle group and
  the markdown content wrapper listed above.
- Testids to add (this case's scope): `artifacts-preview-mode-toggle-group`,
  `artifacts-preview-mode-toggle-rendered`, `artifacts-preview-mode-toggle-code`,
  `artifacts-preview-markdown-content`. All four are shared surface with
  ELITEA-1858 (same toggle group, same markdown content wrapper) — implement
  once, both specs consume the same page-object methods/locators.
- MCP Playwright server was unreachable via `ToolSearch` this session (same
  recurring gap noted in `_surface.md`, now 4th consecutive session) — explored
  via a direct `playwright.sync_api` scratch script driving the live app
  (API-seeded bucket/file, `ArtifactAPI`). Screenshots:
  `automation/test-results/screenshots/FINAL-1857-preview.png`.
- Live-confirmed via direct DOM/API probing (not just source reading):
  headings/bold/bullets render correctly, toggle defaults to Preview/pressed,
  Save/Discard both disabled, typed input has zero effect, zero console errors.
