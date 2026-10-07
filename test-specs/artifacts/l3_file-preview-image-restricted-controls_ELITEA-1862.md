# Test Case: File Preview/Edit – Image File Opens Directly as Image Preview with Inactive Edit Controls

## Metadata
- **TMS ID**: ELITEA-1862
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium` — same mapping as sibling ELITEA-1856)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1857/1858/1862, 2026-08-03)
- **Status**: ready-for-automation
- **Adjustment (2026-10-07, triage of EliteaAI/elitea-testing-public#2396,
  `[FIX][ELITEA-1862]`)**: Save/Discard are now structurally ABSENT for image
  files (not present-and-disabled). See § Adjustment below. Status stays
  `ready-for-automation` — triage class **A** (UI drift), not a defect.

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
2. Observe the `diagram (2).png` row (no hover required)
   - **Verify**: the "View/Edit file" icon is visible on the row
     unconditionally — it is **NOT** hover-gated (confirmed against source:
     `ArtifactRowActions.jsx` renders the Preview `IconButton` whenever
     `row.canPreview` is true, with no opacity/visibility/display CSS tied to
     a hover state — only a `background-color` hover highlight applies to
     the button itself. **Fix round 1 correction:** this AFS originally
     claimed a hover-gated False→True transition — the same drift already
     documented and left open in case-text-drift clarification
     EliteaAI/elitea-testing-public#994 for ELITEA-1851's row icon, and
     wrongly echoed here as "same pattern already confirmed for ELITEA-1857's
     markdown row" — that sibling AFS carried the identical incorrect claim,
     not independent confirmation)
3. Click the "View/Edit file" icon
   - **Verify**: the image opens directly in the main panel (no intermediate
     Raw/Preview choice — image files render immediately)
4. Verify the panel header shows the full path `<bucket-name>/diagram (2).png`
5. Verify the "Save" and "Discard" buttons are **structurally ABSENT** (0
   matches) — **changed 2026-10-07, see § Adjustment**; this AFS originally
   specced them as present-and-disabled, which was correct for the behaviour
   live at analysis time (2026-08-03) but is no longer current
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
- Save/Discard are **structurally ABSENT** for image files — `PreviewHeader.jsx`
  gates the whole Save/Discard/Divider block behind
  `canPreview && !isImageFileType` (confirmed on `origin/main`, 2026-10-07; see
  § Adjustment). **Superseded 2026-10-07**: this AFS originally specced
  "present, rendered whenever `canPreview` is true, independent of file type,
  but permanently disabled" — that was correct for the behaviour live at
  analysis time (2026-08-03); the product has since added the
  `!isImageFileType` gate, so the buttons no longer render at all for images.
- Actions dropdown is restricted to Download + Delete — Copy Content is
  structurally excluded for image files (`.filter(item => item.show)` drops
  it before render, not merely disabled).
- No console errors during open or menu interaction.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click bucket-1 | bucket selected | step 1 | file table visible | asserted *(fixture-generated bucket, not literal "bucket-1")* |
| 2 Hover file → icon appears on hover | icon visible unconditionally, NOT hover-gated | step 2 | `is_visible()` True BEFORE any hover AND after — see EliteaAI/elitea-testing-public#994 | asserted *(case text implies hover-gating; live/source behavior is "always visible" — corrected in fix round 1, not a product defect, same pattern as #994)* |
| 3 Icon visible | icon visible | step 2 | same | asserted |
| 4 Click file/icon → image preview opens | image preview opens | step 3 | `<img>` element renders | asserted |
| 5 File opens displaying image directly | image displayed | step 3 | same | asserted |
| 6 Header shows "bucket-1/diagram (2).png" | header shows correct path | step 4 | `artifacts-preview-file-path` text | asserted *(fixture bucket name, not literal "bucket-1"; filename itself IS literal, confirmed live incl. the space+parens)* |
| 7 Save/Discard INACTIVE/greyed out | **structurally ABSENT (0 matches)** — *changed 2026-10-07, was "both disabled"* | step 5 | `expect(artifacts_page.file_preview_save_button).to_have_count(0)` / same for `file_preview_discard_button` — same absence pattern as rows 8/9 | asserted *(drift — see § Adjustment; case text's "INACTIVE/greyed out" is itself stale against current `src/`, superseded by the live, structural-exclusion behaviour)* |
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
   live this session; the `Private` project showed 555 accumulated buckets
   from this recurring teardown failure as of 2026-08-03. **Update
   2026-10-07**: live count during this session's exploration was ~15–18
   buckets — the backlog has clearly been cleaned up since; the #636 flake
   itself still fires on every teardown (reconfirmed, same 404 body/URL
   shape), it just isn't accumulating unboundedly right now.)

## Concrete Handles (discovered during exploration)

Shared editor-surface handles per ELITEA-1851's AFS (header, Save/Discard,
close, 3-dot menu trigger, delete-confirmation modal) and ELITEA-1856's AFS
(menu-item testids, `get_file_preview_menu_item_labels()`) — reused as-is,
not re-derived here. This case's own (new, image-specific):

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Rendered image | `testid=artifacts-preview-image` — **superseded 2026-10-07: no longer "needed", it's live.** Confirmed present on DEV (`page.evaluate` DOM dump + `expect(...).to_be_visible()` both succeeded this session) and already declared at rung 1 in `ArtifactsPage.file_preview_image` (`pages/artifacts_page.py:766`); the implementer who merged ELITEA-1862's original PR evidently added the testid as part of that work, so this row's original "testid needed" framing was already stale before this adjustment — nothing left to do here | none needed — rung 1, already climbed |
| Save/Discard buttons (image files) | **Changed 2026-10-07** — was `testid=artifacts-preview-save-button`/`-discard-button`, asserted present+disabled; now assert **absence** (`to_have_count(0)`) on the SAME two testid declarations (`ArtifactsPage.file_preview_save_button`/`file_preview_discard_button`, already rung 1) — see § Adjustment | no new locator — reuse the existing declarations as an absence check, same pattern as the row below |
| "No Preview/Raw tabs" absence check | reuse `artifacts-preview-mode-toggle-group` (added by ELITEA-1857's implementation) — assert `.count() == 0` | absence assertion via an existing/soon-to-exist testid — no new locator needed here, this case just consumes it |
| "No language select" absence check | reuse existing `artifacts-preview-language-select` (already exists, ELITEA-1851) — assert `.count() == 0` | confirmed live: 0 matches for an image file |
| "No text editor" absence check | reuse existing `artifacts-preview-code-editor` (already exists, ELITEA-1851) — assert `.count() == 0` | confirmed live: 0 matches for an image file |

## Network Behavior
- Image content is fetched as a blob (`imageBlobUrl`, via `useArtifactContentFetch`)
  and rendered client-side — no explicit request/response assertion needed
  beyond waiting for the `<img>` element to become visible (condition-based,
  see Axis 2).

## Adjustment (2026-10-07)

**Triage**: EliteaAI/elitea-testing-public#2396 (`[FIX][ELITEA-1862]`, auto-filed
by the Test Failure Intake Pipeline from a CI run on `main`) — CI reported
`Locator.wait_for: Timeout 10000ms exceeded` at the "Open file in
preview/edit editor" step, 3/3 CI retries identical.

**Triage class: A — UI drift.** The intended flow (image opens directly as a
rendered `<img>`, no edit path) still works correctly; only the Save/Discard
presentation changed.

**Ground truth before diagnosis**: synced `automation/factory` ← `main` (done
by the orchestrator before dispatch); `git fetch origin` run in the read-only
`../EliteaUI` reference clone (confirmed `up to date with origin/main`) so the
source read below is current as DEV ships it.

**Local reproduction — two runs, two different failure signatures, resolved
by an environment-config gap (not product drift):**
1. First clean-process run (`cd automation && HEADLESS=true
   ../.venv/bin/pytest <node-id> -v -p no:cacheprovider`, 3/3 identical)
   failed at **Step 1** (`navigate_to_bucket` → `_wait_for_bucket_panel`,
   `Locator.wait_for: Timeout 15000ms exceeded` waiting for the bucket name
   text in `main`) — a step *before* the one CI reported. Root cause: this
   analysis sandbox has no `automation/.env.test` file (only
   `.env.test.example`) and `APP_PREFIX` is not exported in the shell either,
   so `settings.app_base_url` resolved to `https://dev.elitea.ai` with no
   `/app` segment — every page-object `navigate()` call 404'd before the
   bucket panel could ever render. This is a **sandbox config gap, not a
   product or test defect** — flagging for the record, not filing (nothing to
   file: the fix is `.agents/profile.md`'s own documented env — this sandbox
   is just missing the file this one time).
2. Re-run with `APP_PREFIX=/app` exported explicitly: 3/3 identical failures,
   **matching the CI signature exactly** — `Locator.wait_for: Timeout
   10000ms exceeded` waiting for `get_by_test_id("artifacts-preview-save-button")`
   to be visible, at `artifacts_page.py:3121` inside
   `open_file_in_editor()`'s `self.file_preview_save_button.wait_for(...)` call
   (the step before the content-ready wait). This is the real reproduction.
3. The CI run's bucket-teardown 404s are the pre-existing, already-documented
   `#636` flake (`.agents/testing.md` § Unconfirmed) — reconfirmed present in
   both local runs, including the ones with the unrelated sandbox-config
   failure. **Noise, not the cause**, exactly as flagged in the dispatch.

**Handle pre-check (Step 1.4)** — Playwright snapshot of the open editor panel
on DEV (bucket seeded via `ArtifactAPI`, image opened via the real UI click,
not synthesized):
- `artifacts-preview-image` — present, `<img>` renders with the correct
  `blob:` src and `alt="diagram (2).png"`. **Element present, image rendering
  unaffected.**
- `artifacts-preview-file-path`, `artifacts-preview-close-button`,
  `file-preview-overflow-menu-menu-button` — all present, unchanged.
- `artifacts-preview-save-button`, `artifacts-preview-discard-button` — a full
  dump of every `[data-testid]` on the page after opening the image (`page.evaluate`
  over `document.querySelectorAll('[data-testid]')`) shows **neither present at
  all** — not hidden/disabled, structurally absent from the DOM. Confirmed with
  an extended 20s wait (vs the method's 10s) to rule out a slow-render false
  negative: still absent. ⇒ this is case **E's sibling for an attribute, not a
  testid, going away** — handled the same way the ladder handles any
  absence-check (rows 8/9 already do this for mode-toggle-group/language-select),
  so it folds into class **A**, not **E** (no replacement handle is needed; the
  *existing* testid-rung declarations for Save/Discard are reused as absence
  checks, same objects, same rung).
- `artifacts-preview-mode-toggle-group`, `artifacts-preview-language-select`,
  `artifacts-preview-code-editor` — absent, as already specced. **Unchanged.**
- Overflow menu (clicked live): exactly `["Download", "Delete"]`, same order.
  **Unchanged** — "Rename" exists as a menu-item definition in current
  `src/` (`show: !isChatPage && !!onRename`) but does not appear live, so
  `onRename` isn't wired for this call site. No drift.
- Zero console errors across open + menu-open. **Unchanged.**
- Path text: `"<bucket>/diagram (2).png"`, exact match. **Unchanged.**

**Source confirmation** (`../EliteaUI`, `git show
origin/main:"src/[fsd]/features/artifacts/ui/file-preview-canvas/PreviewHeader.jsx"`,
read-only reference, not built/run):
```jsx
<Box sx={styles.canvasControlsWrapper}>
  {canPreview && !isImageFileType && (
    <>
      <Button.BaseBtn ... data-testid="artifacts-preview-save-button">Save</Button.BaseBtn>
      <Button.DiscardButton ... dataTestId="artifacts-preview-discard-button" />
      <Divider orientation="vertical" sx={styles.divider} />
    </>
  )}
  ...
```
(`PreviewHeader.jsx` lines ~219–243.) The whole Save/Discard/Divider block is
now gated on `!isImageFileType` in addition to `canPreview` — this is new
relative to the AFS's original analysis (2026-08-03), which found Save/Discard
rendered "whenever `canPreview` is true, independent of file type." The
product intentionally hides the controls instead of showing-then-disabling
them when there is no edit path (images). This is a deliberate, reasonable UI
simplification, not a bug — reverse-masking guard does not apply here because
there's no case-text/live-product conflict to misclassify; this is a genuine,
confirmed behaviour **change** since the case was last automated.

**Expected-result changes**: yes — one.
- OLD: "Save and Discard buttons are present and both DISABLED."
- NEW: "Save and Discard buttons are structurally ABSENT (0 matches)" — same
  shape as the existing mode-toggle-group/language-select/code-editor absence
  checks (Steps 6–8), so the implementer can follow an existing pattern in the
  same test rather than invent a new assertion idiom.

**Implementer impact (code, out of this slot's scope — flagging so Step 7
doesn't need to re-explore):**
- The test's own Step 6 assertions (lines 161–175 of
  `test_artifacts_file_preview_image_restricted_controls.py`) need to flip
  from `to_be_visible()` + `is_file_preview_save_disabled()`/
  `is_file_preview_discard_disabled()` to `to_have_count(0)` on
  `file_preview_save_button`/`file_preview_discard_button` — identical idiom
  to Steps 7–8's `to_have_count(0, timeout=...)`. `is_file_preview_save_disabled()`
  /`is_file_preview_discard_disabled()` become dead code for this test only if
  no other test still uses them for a non-image file — check before deleting
  (sibling specs ELITEA-1851/1852/1856 open code/markdown files, where
  `isImageFileType` is false and Save/Discard still render-and-disable
  pre-edit, so those methods stay live there; **do not delete them**, just
  stop calling them from this test).
- **Shared helper is now broken for every image-file caller, not just this
  test**: `ArtifactsPage.open_file_in_editor()` (`artifacts_page.py:3100–3145`)
  unconditionally does
  `self.file_preview_save_button.wait_for(state="visible", timeout=timeout)`
  before its own `content_ready` wait (which already correctly branches on
  `file_preview_code_content | file_preview_image | file_preview_markdown_content`).
  Since Save never renders for images, this call now always times out before
  reaching the `content_ready` wait, for *any* caller opening an image file —
  this is why the whole test times out at "Open file in preview/edit editor"
  rather than failing later at the (now-removed) Save-visibility assertion.
  The fix is in the shared method: drop the unconditional
  `file_preview_save_button.wait_for` and rely on `content_ready` alone (it
  already waits for *some* content surface to render, which is a strictly
  weaker and still-correct "editor is open" signal for every file type,
  image included) — or gate the Save-button wait the same way the component
  does (`image file ⇒ skip it`). This is a one-method fix with no behavioural
  loss for the code/markdown callers (ELITEA-1851/1852/1856): their Save
  button still renders, `content_ready` still waits for their content surface
  either way.
- No TMS case-text change needed beyond what's already reflected in this AFS
  (`automation_test_id` unchanged — same test, same dotted path).

**Evidence** (repo-relative, `test-case-analysis` evidence-paths convention):
- `automation/test-results/screenshots/ELITEA-1862-adjust-image-preview-open.png`
  — editor panel open on DEV, image rendered, no Save/Discard/Divider visible.
- `automation/test-results/screenshots/ELITEA-1862-adjust-overflow-menu.png`
  — overflow menu open, exactly Download + Delete.

## Known Defects Found During Exploration
None — see § Adjustment above for the one confirmed drift (Save/Discard
structurally absent for images, 2026-10-07). Everything else case text
specced at analysis time (2026-08-03) still matches live behavior: no tabs,
no language select, no text editor, dropdown restricted to Download + Delete
in that order, path text format, zero console errors. All reconfirmed live
via direct DOM probing this session, not just source reading.

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
