# Test Case: File Preview/Edit – Image File Opens Directly as Image Preview with Inactive Edit Controls

## Metadata
- **TMS ID**: ELITEA-1862
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium` — same mapping as sibling ELITEA-1856)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1857/1858/1862, 2026-08-03)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (auth_state, localhost).
- A bucket exists containing an image file (`.png` — `AvailableLanguagesEnum.IMAGE`
  detection). **Not** a shared literal "bucket-1" — see § Test Data.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Fresh bucket via `artifact_bucket` fixture + a minimal valid PNG (any
  non-corrupt PNG bytes; a 1x1 transparent pixel is sufficient — the case
  doesn't require the image to have specific visual content, only that it
  IS an image) uploaded via `ArtifactAPI.upload_file()` as
  `"diagram (2).png"` (verbatim filename incl. the space+parens — confirmed
  live this does not break routing/URL handling; file key is URL-encoded
  transparently by the existing upload/preview flow).

## Test Steps
1. Navigate to Artifacts, click the fixture bucket
   - **Verify**: file table shows `diagram (2).png`
2. Hover the `diagram (2).png` row
   - **Verify**: the "View/Edit file" icon is hidden before hover, visible
     after hover (confirmed live: `is_visible()` False → True across the
     hover — same pattern already confirmed for ELITEA-1857's markdown row)
3. Click the "View/Edit file" icon
   - **Verify**: the image opens directly in the main panel (no intermediate
     Raw/Preview choice — image files render immediately)
4. Verify the panel header shows the full path `<bucket-name>/diagram (2).png`
5. Verify the "Save" and "Discard" buttons are present **and both DISABLED**
6. Verify **no** render-mode toggle group (Preview/Raw tabs) is present —
   confirmed live: `modeTogglerAvailable` explicitly excludes
   `isImageFileType` in `PreviewHeader.jsx`
7. Verify **no** language-select dropdown is present — confirmed live:
   `shouldDetectLanguage` excludes `isImageFileType`
8. Verify **no** CodeMirror text editor / content-editing area is present —
   only the `<img>` element renders (confirmed via the existing
   `artifacts-preview-code-editor` testid resolving to 0 matches)
9. Verify the 3-dot (ellipsis) actions menu is present
10. Click the 3-dot menu
    - **Verify**: the dropdown contains **exactly two** items, in this
      order: "Download", "Delete" — **no "Copy Content" option** (confirmed
      live: `PreviewHeader.jsx`'s `menuItems` filters out the Copy Content
      entry via `show: canPreview && fileContent && !isImageFileType`)

## Expected Results
- Image renders directly as a visible `<img>` element — no Preview/Raw
  choice, no code editor, ever, for an image file (`canEdit` is
  unconditionally false when `isImageFileType`).
- Save/Discard are present (rendered whenever `canPreview` is true,
  independent of file type) but permanently disabled for images, since
  `hasUnsavedChanges` can never become true (no edit path exists).
- Actions dropdown is restricted to Download + Delete — Copy Content is
  structurally excluded for image files (`.filter(item => item.show)` drops
  it before render, not merely disabled).
- No console errors during open or menu interaction.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click bucket-1 | bucket selected | step 1 | file table visible | asserted *(fixture-generated bucket, not literal "bucket-1")* |
| 2 Hover file → icon appears on hover | icon appears | step 2 | `is_visible()` False→True across `hover()` | asserted |
| 3 Icon visible | icon visible | step 2 | same | asserted |
| 4 Click file/icon → image preview opens | image preview opens | step 3 | `<img>` element renders | asserted |
| 5 File opens displaying image directly | image displayed | step 3 | same | asserted |
| 6 Header shows "bucket-1/diagram (2).png" | header shows correct path | step 4 | `artifacts-preview-file-path` text | asserted *(fixture bucket name, not literal "bucket-1"; filename itself IS literal, confirmed live incl. the space+parens)* |
| 7 Save/Discard INACTIVE/greyed out | both disabled | step 5 | `is_disabled()` True for both | asserted |
| 8 No Preview/Raw tabs shown | no tabs | step 6 | mode-toggle-group testid resolves to 0 (once added — see ELITEA-1857's AFS) / live confirmed via `[aria-label="Render Mode Toggle"]` absence | asserted |
| 9 No text editor/content-editing area present, only image | no editor, only image | step 8 | `artifacts-preview-code-editor` testid resolves to 0 matches | asserted |
| 10 3-dot menu present | menu present | step 9 | `file-preview-overflow-menu-menu-button` visible | asserted |
| 11 Dropdown contains only Download + Delete, no Copy Content | exactly 2 items | step 10 | `get_file_preview_menu_item_labels()` (existing method, ELITEA-1856) `== ["Download", "Delete"]` | asserted |

### Axis 2 — Analyst additions
- Assert **no language-select dropdown** is present for images either — added:
  the case doesn't explicitly ask for this, but it's the same
  `shouldDetectLanguage` gate as the tabs, and it's free to check with the
  same reused testid-absence pattern; a regression here (language select
  incorrectly appearing for images) would be a real UI bug this closes off.
- Assert the dropdown item **order** is exactly Download → Delete — added:
  same reasoning as ELITEA-1856's AFS (real UI contract, muscle memory).
- Assert **no console errors** across open + menu-open — added: standard
  side-channel discipline; zero found live.
- Assert the image load conditions on a real element becoming visible
  (`expect(img).to_be_visible()` with a generous timeout), not a fixed sleep
  — added: confirmed live the image blob fetch can take longer than a 1s
  fixed wait on a busy shared DEV backend (a `networkidle` wait + 1s sleep
  intermittently caught the panel still showing "Loading file content...");
  a condition-based wait on the `<img>` element's visibility is the correct,
  non-flaky replacement.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket (subject to the
   known `#636` 404-on-teardown flake, already handled gracefully — reconfirmed
   live this session; the `Private` project now shows 555 accumulated buckets
   from this recurring teardown failure across many sessions).

## Concrete Handles (discovered during exploration)

Shared editor-surface handles per ELITEA-1851's AFS (header, Save/Discard,
close, 3-dot menu trigger, delete-confirmation modal) and ELITEA-1856's AFS
(menu-item testids, `get_file_preview_menu_item_labels()`) — reused as-is,
not re-derived here. This case's own (new, image-specific):

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Rendered image | **testid needed**: `artifacts-preview-image` on `PreviewContent.jsx`'s `<Box component="img" src={imageBlobUrl} alt={file.name} .../>` (currently only has `alt={file.name}`, no `data-testid`) | until added, `page.locator(f"img[alt='{filename}']")` is an acceptable interim per project precedent (a dynamic-value CSS attribute selector chained off no testid'd parent is technically a raw handle — implementer must add the testid before merging, same discipline as ELITEA-1852's AFS flagged for its interim `.cm-content` selector) |
| "No Preview/Raw tabs" absence check | reuse `artifacts-preview-mode-toggle-group` (added by ELITEA-1857's implementation) — assert `.count() == 0` | absence assertion via an existing/soon-to-exist testid — no new locator needed here, this case just consumes it |
| "No language select" absence check | reuse existing `artifacts-preview-language-select` (already exists, ELITEA-1851) — assert `.count() == 0` | confirmed live: 0 matches for an image file |
| "No text editor" absence check | reuse existing `artifacts-preview-code-editor` (already exists, ELITEA-1851) — assert `.count() == 0` | confirmed live: 0 matches for an image file |

## Network Behavior
- Image content is fetched as a blob (`imageBlobUrl`, via `useArtifactContentFetch`)
  and rendered client-side — no explicit request/response assertion needed
  beyond waiting for the `<img>` element to become visible (condition-based,
  see Axis 2).

## Known Defects Found During Exploration
None. Case text fully matches live behavior — Save/Discard present-but-disabled,
no tabs, no language select, no text editor, dropdown restricted to
Download + Delete in that order. All confirmed live via direct DOM probing,
not just source reading.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Extends `ArtifactsPage` — reuse `open_file_in_editor()`,
  `open_file_preview_actions_menu()`, `get_file_preview_menu_item_labels()`
  (all pre-existing from ELITEA-1851/1856) as-is; add
  `artifacts_preview_image` locator + an `is_file_preview_image_visible()`
  helper.
- Testid to add (this case's scope): `artifacts-preview-image`. The
  mode-toggle-group / language-select / code-editor ABSENCE checks reuse
  testids that are either already merged (`artifacts-preview-language-select`,
  `artifacts-preview-code-editor`) or land as part of ELITEA-1857's
  implementation (`artifacts-preview-mode-toggle-group`) — no duplicate work.
- MCP Playwright server was unreachable via `ToolSearch` this session (same
  recurring gap, see `_surface.md`) — explored via a direct
  `playwright.sync_api` scratch script driving the live app (API-seeded
  bucket/image via `ArtifactAPI`). Screenshots:
  `automation/test-results/screenshots/FINAL-1862-open.png`.
- Live-confirmed: image renders correctly once given enough time to load
  (see Axis 2's flakiness note on `networkidle`-based waits being
  insufficient here); zero console errors; menu contents exactly
  `["Download", "Delete"]`, no "Copy Content".
