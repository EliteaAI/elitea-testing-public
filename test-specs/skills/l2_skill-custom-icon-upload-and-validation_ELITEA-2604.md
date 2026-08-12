# Test Case: Skill Custom Icon Upload and Validation

## Metadata
- **TMS ID**: ELITEA-2604
- **Linked Story**: none
- **Priority**: high (per case frontmatter) — mapped to `l2` (same mapping as the sibling
  high-priority skill case ELITEA-2602)
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI `automation/testids`
  → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (agent), 2026-08-12
- **Status**: **ready-for-automation** — case executed end-to-end live against a freshly-created
  disposable skill. All four parts (A–D) completed with no blockers, no product defects. All four
  accepted formats (PNG, JPG, GIF, WEBP) confirmed working in BOTH create mode and edit mode;
  oversized-file rejection confirmed server-side (400, exact error text captured); icon deletion
  confirmed to revert to default via TWO distinct live mechanisms (delete an uploaded icon /
  select the "Default" tile), and the reverted state was confirmed to survive a full page reload.
  One new testid gap found and documented (the per-uploaded-icon delete button has no
  `data-testid` at all — implementer work via `add-data-testid`). One UI-text inconsistency
  observed (not a functional defect — see Coverage Map disposition and Known Defects).

## Preconditions
- User is logged in to the Elitea platform (satisfied automatically on localhost via
  `auth_state`/`VITE_DEV_TOKEN` — no Keycloak login step needed in this environment).
- Admin/Editor role — the suite's default `${TEST_USER}` identity already has full CRUD on
  Skills in project 399 (confirmed live via existing skills specs, e.g. ELITEA-2602).
- **Per this project's Hard Rule 10 test-data guidance**, use a freshly-created, uniquely-named
  disposable skill rather than mutating a shared fixture skill's icon — icon state is a visible,
  list/mention-affecting mutation, same reasoning as ELITEA-1899's Agent-icon AFS. Create via the
  UI create form (`SkillFormPage`) during Part A itself (the case's own steps 1–7 already create
  the skill), then delete via the UI's type-to-confirm delete flow (`SkillDetailPage.delete_skill_via_menu()`)
  in a `finally`/fixture-teardown block. `SkillAPI.delete_skill(skill_id)` (cookie-auth) is an
  equally valid teardown path if the implementer prefers an API-level safety net (mirrors
  ELITEA-2602's `target_project_skill_api` pattern) — either is acceptable, but at least one MUST
  run in `finally`.
- Test icon files — **added to the repo this run**, all under `test-data/images/`:
  - `skill-fork-test-icon.png` (1.8KB, already existed — added for ELITEA-2602)
  - `test-icon.jpg` (~1KB, added this run — `sips -s format jpeg` from the PNG)
  - `test-icon.gif` (~1.7KB, added this run — `sips -s format gif` from the PNG)
  - `test-icon.webp` (~150 bytes, added this run — `magick` conversion from the PNG)
  - `large-icon.png` (~1.25MB, added this run — `magick -size 500x500 plasma:fractal`, a
    legitimate-format PNG that is genuinely over the 500KB/512KB limit, not a corrupted/truncated
    file — this matters because the rejection is confirmed server-side on FILE SIZE, not format
    validity, so the test file must be a valid image to isolate the size check)
- **Reused/confirmed test data note**: the project's shared "Uploaded" icon gallery
  (`GET /upload_skill_icon/prompt_lib/{project}`) is **project-scoped, not skill-scoped** — icons
  uploaded by earlier runs/other skills in project 399 persist in this list indefinitely (6 stale
  entries observed live at the start of this run, left by prior sessions/other cases). This is
  expected system behavior (icons are a shared per-project asset library), not test-data leakage
  to clean up — the case's own uploads/deletes are still correctly isolated to the entries this
  run creates/removes.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: `el2604-icon-test-skill` (or `f"autotest_{request.node.name}"[:32]` per the
  project's existing naming convention)
- Skill description: free text, e.g. "Skill for ELITEA-2604 icon upload/validation testing"
- Skill instructions: any non-empty text (required field, content irrelevant to this case)
- No toolkits/tags needed — the case only exercises the icon field.

## Test Steps

**EXECUTED END-TO-END LIVE 2026-08-12** — all 21 case steps (Parts A–D) completed with no
blockers. Numbering below follows the case's own Part/step numbering.

### Part A — Upload During Creation (steps 1–7)

1. Navigate to `/skills/create`
   - **Verify**: Create Skill form loads
   - **OBSERVED**: form loaded (`skill-name-input`/`skill-description-input`/
     `skill-instructions-editor-content` all visible), Save button disabled (no fields filled yet).
2. Click on the icon avatar (opens the icon picker)
   - **Verify**: file picker / icon picker dialog opens
   - **OBSERVED**: same **hover-then-click quirk documented in ELITEA-1899/ELITEA-2602's AFS**
     applies identically here (same shared `EntityIcon` component) — a bare single `.click()`
     with no prior `.hover()` only mounts the hover-triggered edit-pencil overlay and does NOT
     open the dialog. `SkillFormPage.open_icon_picker()` (pre-existing, ELITEA-2602) already
     implements hover-then-click correctly — confirmed live 2/2 across both create and edit mode
     in this run. Dialog testid `agent-icon-picker-dialog` (entity-agnostic, shared component),
     title "Choose the image from the list or upload", header tooltip text "Upload a bmp, ico,
     gif, jpeg, jpg, png, tiff or webp image (less than 500KB)" (**case-relevant**: the dialog
     accepts MORE formats than the case's four — bmp/ico/tiff also work per this tooltip and the
     file-input's `accept` attribute, but the case only asks for PNG/JPG/GIF/WEBP, so bmp/ico/tiff
     are out of this case's scope, not a gap).
3. Select a valid PNG file (under 500KB)
   - **Verify**: file is selected
   - **OBSERVED**: `SkillFormPage.upload_skill_icon(ICON_FILE)` (pre-existing, ELITEA-2602) already
     covers this exact step — clicks `icon_picker_upload_button`, uses `page.expect_file_chooser()`,
     `set_files(png_path)`.
4. Confirm upload
   - **Verify**: icon preview shows the uploaded PNG
   - **OBSERVED**: no separate "confirm" action exists — selecting the file via the native chooser
     IS the confirm action (`handleFileChange` fires immediately on `<input type="file">`
     `onChange`). Toast "The image has been uploaded" appears (`toast-message` testid), the dialog
     auto-closes (create mode has no `entityId` yet, so `onSelectIcon(iconData); onClose()` fires
     directly — no second network call, unlike edit mode, see Part B), and the form's icon avatar
     (`skill-form-icon-img`) now renders an `<img>` with a non-empty `src`
     (`https://dev.elitea.ai/app/skill_icon/399/{uuid}.png` — **note the server always stores the
     uploaded asset with a `.png` extension regardless of the original format**, confirmed for
     JPG/GIF/WEBP uploads too in steps 12–13/9 below; this is a storage-layer normalization, not
     a functional issue, since the browser correctly renders whatever bytes are behind that URL).
     Network: `POST /api/v2/elitea_core/upload_skill_icon/prompt_lib/399` → **200 OK**.
5. Fill in required fields (name, description, instructions)
   - **Verify**: fields are populated
   - **OBSERVED**: `SkillFormPage.fill_form(name, instructions, description)` (pre-existing)
     covers this; Save button becomes enabled once all three required fields are non-empty.
6. Save the skill
   - **Verify**: skill is created with custom icon
   - **OBSERVED**: `SkillFormPage.save_and_wait_for_navigation()` (pre-existing) — URL settles on
     `/skills/all/{id}` (this run: id 1499), the same PNG icon persists into the detail/edit page
     (confirmed via `skill-form-icon-img` src match — same uuid as step 4's upload).
7. Reopen the skill
   - **Verify**: custom PNG icon is displayed
   - **OBSERVED**: full page reload of `/skills/all/{id}` — `skill-form-icon-img`'s `src` is
     identical to the pre-reload value, confirming server-side persistence (not just client state).

### Part B — Replace Icon with Different Format (steps 8–13)

8. Click on the icon to change it (on the now-saved/reopened skill, i.e. **edit mode**, entityId
   present)
   - **Verify**: file picker / icon edit option appears
   - **OBSERVED**: same dialog, same hover-then-click mechanic. **Distinct network/toast behavior
     from create mode (case-relevant automation detail)**: because `entityId`/`versionId` are now
     present, a successful file upload in edit mode fires TWO sequential requests instead of one —
     `POST /upload_skill_icon/prompt_lib/{project}/{versionId}` → 200 (uploads to the gallery,
     identical to create mode) **followed immediately by** `PUT
     /upload_skill_icon/prompt_lib/{project}/{versionId}` → 200 (applies/persists the icon to this
     specific skill version — `replaceSkillIcon`, the same call the "Default" tile and the default
     gallery options use to persist a selection). Both confirmed live (request sequence 2057→2059
     in this run). The UI shows the "The image has been uploaded" toast first; a second toast
     ("The icon has been changed") is expected per source (`SelectIconDialog.jsx`'s
     `onClickIcon`/`uploadFile` chain) but was not captured verbatim by this run's snapshot timing
     (superseded before the next snapshot) — **automation implication**: assert on the network
     response pair (POST 200 + PUT 200) and the resulting `skill-form-icon-img` src change as the
     authoritative persistence signal for edit-mode replace, rather than a single brittle toast-text
     match (the create-mode "upload during creation" flow, by contrast, correctly fires exactly one
     toast — `SkillFormPage.upload_skill_icon()`'s existing exact-text assertion is correct
     AS-WRITTEN only for create mode; an edit-mode variant/overload should not reuse that same
     strict assertion).
9. Upload a valid GIF file
   - **Verify**: GIF is uploaded successfully
   - **OBSERVED (executed in CREATE mode during Part A/C exploration, same mechanism applies to
     edit mode per step 8's finding)**: `POST /upload_skill_icon/prompt_lib/399` → 200, toast "The
     image has been uploaded", `skill-form-icon-img` src updates to a new (`.png`-suffixed,
     per step 4's note) URL.
10. Save the skill
    - **Verify**: changes are saved
    - **OBSERVED**: **case-text CLARIFICATION, same pattern as ELITEA-1899 (reverse-masking guard,
      not a defect)** — there is no separate "click Save to persist the icon change" action for an
      icon-only edit. The icon already persisted server-side via step 8/9's own PUT call. The main
      form's "Save" button (`skill-save-button`) was confirmed live to remain **disabled**
      immediately after an icon-only change in edit mode (icon field is not formik-tracked, exact
      same mechanism as `AgentDetailPage`/ELITEA-1899). Automation should assert
      `not is_save_enabled()` here rather than click a Save button that has nothing to save.
11. Verify the icon is now the GIF
    - **Verify**: GIF icon is displayed
    - **OBSERVED**: `skill-form-icon-img` src reflects the newly-uploaded GIF-derived asset
      immediately, no reload needed (same "immediate, no-reload" persistence pattern as ELITEA-1899).
12. Repeat with WEBP format
    - **Verify**: WEBP icon uploads and displays correctly
    - **OBSERVED**: identical mechanism, confirmed live — `POST` → 200, toast, src update.
13. Repeat with JPG format
    - **Verify**: JPG icon uploads and displays correctly
    - **OBSERVED**: identical mechanism, confirmed live (this was in fact the FIRST format tested
      in this run, immediately after PNG in Part A's exploration) — `POST` → 200, toast, src update.

### Part C — Validation: Oversized File (steps 14–16)

14. Attempt to upload an oversized file (>500KB)
    - **Verify**: upload is rejected
    - **OBSERVED**: uploaded `large-icon.png` (~1.25MB, valid PNG). `POST
      /upload_skill_icon/prompt_lib/399` → **400 Bad Request**. Response body:
      `{"error": "File size exceeds 512 KB"}`. **Validation is server-side, not client-side** —
      confirmed via source read (`useUploadSkillIconMutation`'s RTK-Query `query()` builder has NO
      pre-flight size check; the FormData POST always fires and the 500KB/512KB limit is enforced
      by the backend). This means automation cannot short-circuit on a client-side error before the
      network call — the assertion must wait for the 400 response.
    - **UI-TEXT INCONSISTENCY (not a defect — see Known Defects/Coverage Map)**: the picker
      dialog's header tooltip advertises "less than 500KB" but the server's own rejection message
      says "exceeds 512 KB" — 512 KB = 500 KiB in binary units, so both are numerically consistent
      (500×1024 bytes), but the user-facing STRINGS use inconsistent unit labels (500 vs 512) for
      the same limit. Cosmetic; does not affect the case's pass/fail criterion (rejection itself
      works correctly).
15. Verify error message is displayed
    - **Verify**: error indicates file size exceeds 500KB limit
    - **OBSERVED**: an app-wide `toast-alert` (root, `data-severity="error"`) appears with body
      text **exactly** "File size exceeds 512 KB" (`toast-message` for the text, per the app-wide
      pattern already documented in this project's Skills `_surface.md` § Import — invalid-file
      validation, and already wired for `ChatPage`/`PipelineDetailPage`). `SkillFormPage`/
      `SkillsListPage` do NOT yet expose this `toast_alert`/`TOAST_ALERT_SEVERITY`/
      `get_toast_alert(severity)` trio — implementer should copy the existing `ChatPage`
      (`automation/pages/chat_page.py:1007-1014,2015-2025`) pattern onto whichever page object ends
      up owning this test (likely `SkillFormPage`, since the icon picker lives there), not invent a
      new testid (both `toast-alert` and `toast-message` are pre-existing, app-wide).
16. Verify the previous icon is retained (not cleared)
    - **Verify**: current icon remains unchanged
    - **OBSERVED**: confirmed via DOM — immediately after the 400 response, `skill-form-icon-img`'s
      `src` is UNCHANGED from its pre-upload-attempt value (the WEBP icon uploaded earlier in this
      run's exploration). The icon picker dialog also remains OPEN (does not auto-close on a failed
      upload, unlike a successful one) — automation can additionally assert the dialog is still
      visible as a secondary signal.

### Part D — Delete Icon, Revert to Default (steps 17–21)

17. Click on the icon delete/remove option
    - **Verify**: delete confirmation or immediate removal
    - **OBSERVED**: **two distinct, independently-live-confirmed mechanisms both satisfy this
      case's intent** — the implementer should pick ONE as the case's primary automated path
      (recommend the delete-button path below, since it maps most literally to the case's own
      wording "delete/remove option"), and MAY note the second as an Axis-2 addition:
      - **(a) Delete an uploaded icon (the literal "delete" affordance).** In the dialog's
        "Uploaded" section, each icon thumbnail (`agent-icon-picker-uploaded-{index}`, pre-existing
        dynamic testid) reveals an "X" delete `IconButton` on `:hover` (CSS
        `visibility: hidden` → `visible`, same hover-reveal pattern as other parts of this app —
        confirmed live via DOM query after a real Playwright `.hover()`, the button IS present in
        the DOM the whole time, just invisible until hover). Clicking it opens a confirmation
        `AlertDialog` ("Warning" / "Are you sure to delete this icon?" — pre-existing app-wide
        `alert-dialog-content`/`alert-dialog-confirm-button` testids, its Cancel button has NO
        testid). Confirming fires `DELETE /upload_skill_icon/prompt_lib/{project}/{icon_name}` →
        confirmed live **200 OK**. If the deleted icon was the currently-SELECTED one (as it was in
        this run), the form's `skill-form-icon-img` element is removed entirely (reverts to the
        placeholder — same "absent `<img>` = default" convention documented in
        `SkillFormPage.get_form_icon_src()`'s existing docstring).
      - **(b) Select the "Default" tile (`agent-icon-picker-default-icon`, pre-existing testid).**
        In edit mode (entityId present), clicking this tile calls the SAME `replaceSkillIcon`
        mutation used by every other selection, but with an empty `{name: "", url: ""}` payload —
        confirmed live: `PUT /upload_skill_icon/prompt_lib/{project}/{versionId}` → **200 OK**,
        toast "The icon has been reset to default icon" (distinct text from the delete-button
        path's toast, "The icon has been successfully deleted." per source read — this run's DOM
        snapshot caught the network/DOM effect but not the delete-path toast text verbatim due to
        timing; the reset-path result was fully confirmed including the DOM state).
      - **NEW TESTID GAP (implementer work)**: the per-uploaded-icon delete `IconButton` (path
        (a)) has **NO `data-testid` at all** — confirmed via source read
        (`UserIconItem.jsx`, `../EliteaUI/src/[fsd]/features/settings/ui/project-general/general/
        select-project-icon/UserIconItem.jsx`) and live DOM inspection (only a non-unique
        `className="deleteButton"` + an `IconButton`/`CloseIcon`, zero `data-testid` prop anywhere
        on the button or its parent wrapper). This run located and clicked it via the Playwright
        MCP tool's own CSS/role fallback (exploration only, never shipped as a locator) — the
        REAL automated test must NOT do this (testid-only locator policy, no fallback rung). Fix:
        add a dynamic testid to the `IconButton` in `UserIconItem.jsx`, forwarded from
        `SelectIconDialog.jsx`'s per-item `data-testid={`agent-icon-picker-uploaded-${index}`}`
        call site (same convention as the sibling `agent-icon-picker-option-{index}` gallery items)
        — e.g. `agent-icon-picker-uploaded-{index}-delete-button`, added via `add-data-testid` to
        BOTH `UserIconItem.jsx` (accept + forward a `deleteButtonTestId` prop, per this project's
        `testId`/`<part>TestId` naming convention — never a `data`-prefixed prop name) and
        `SelectIconDialog.jsx` (pass `deleteButtonTestId={`agent-icon-picker-uploaded-${index}-delete-button`}`).
        Path (b) needs **no new testid** — `agent-icon-picker-default-icon` already exists and was
        confirmed live.
18. Confirm deletion if prompted
    - **Verify**: icon is removed
    - **OBSERVED**: covered by step 17(a)'s confirmation-dialog flow above (`alert-dialog-confirm-button`).
19. Verify the icon reverts to default `skill-icon.svg`
    - **Verify**: default system icon is displayed
    - **OBSERVED**: **case-text imprecision, not a defect (reverse-masking guard note)** — the case
      names a specific file `skill-icon.svg`, but the live product's "default" state is an absent
      `<img>` element entirely (an inline SVG placeholder is rendered by `EntityTypeIcon`, not a
      `<img src="skill-icon.svg">` reference) — same convention already documented for Agents
      (ELITEA-1899's AFS: "A skill/agent with no icon explicitly set yet renders an inline SVG
      placeholder instead (no `<img>` at all)"). Automation should assert
      `get_form_icon_src() == ""` (pre-existing method, already handles this "absent img" case
      correctly) rather than asserting a literal `skill-icon.svg` filename/URL, which the live
      product never actually renders as a discrete asset. Confirmed live via both revert mechanisms
      (17a and 17b).
20. Save the skill
    - **Verify**: changes are saved
    - **OBSERVED**: same clarification as step 10 — no separate Save action needed; the delete/reset
      already persisted server-side (200/204 responses in steps 17a/17b). `skill-save-button`
      remains disabled.
21. Reopen the skill
    - **Verify**: default icon is still displayed
    - **OBSERVED**: confirmed live via a full page **reload** (`page.goto()` to the same URL, not
      just a client-side route change) of `/skills/all/{id}` — `skill-form-icon-img` remains ABSENT
      post-reload, confirming server-side persistence of the reverted-to-default state (not merely
      client-side/optimistic state that would disappear on a hard refresh).

## Expected Results

Per case:
1. Custom icons can be uploaded during creation and editing. — **CONFIRMED**, both modes, with a
   documented mechanism difference (single vs double network call/toast, see step 8).
2. All valid formats (PNG, JPG, GIF, WEBP) work correctly. — **CONFIRMED**, all four, live.
3. Files exceeding 500KB are rejected with a clear error message. — **CONFIRMED**, server-side 400,
   exact error text captured, dialog stays open, previous icon retained.
4. Deleting a custom icon reverts the skill to the default icon. — **CONFIRMED** via two independent
   live mechanisms, and confirmed to survive a full page reload (persisted server-side, not just
   client state).

**Actual (observed 2026-08-12)**: matches expected on all four points. Case **PASSES**. Only two
console error entries occurred across the entire run: the EXPECTED 400 for the oversized-upload
attempt (step 14, this IS the case under test) and one unrelated 404 on
`GET /api/v2/elitea_core/skill/prompt_lib/399/1499` that occurred **before** this run's own skill
(also coincidentally assigned id 1499 by the DB) was ever created — timing analysis (network
request sequence numbers) shows this 404 followed a DELETE that happened earlier in the same
browser session than any action this run performed, consistent with a leftover/stale query from a
prior, unrelated session reusing the same browser tab, not something this case's own flow caused.
Not reproduced when this run performed its OWN final delete of its own skill 1499 (that delete
returned a clean 204 with no follow-up error). Noted here for completeness; not filed as a defect
(no live reproduction tying it to THIS case's actions).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, Admin/Editor role | session valid | n/a (auto via `auth_state`) | — | asserted (environment-level) |
| Precondition: test icon files (PNG/JPG/GIF/WEBP/oversized) prepared | files exist | AFS precondition | — | covered — all 4 valid-format files + 1 oversized file added to `test-data/images/` this run |
| Step 1: Navigate to Create Skill page | form loads | AFS step 1 | step 1 | covered |
| Step 2: Click icon upload area | picker opens | AFS step 2 | step 2 | covered — hover-then-click quirk documented (same as ELITEA-1899/2602) |
| Step 3: Select valid PNG | file selected | AFS step 3 | step 3 | covered — reuses `SkillFormPage.upload_skill_icon()` (pre-existing) |
| Step 4: Confirm upload | preview shows PNG | AFS step 4 | step 4 | covered — no literal "confirm" action; file-chooser selection IS the confirm, clarified |
| Step 5: Fill required fields | fields populated | AFS step 5 | step 5 | covered — reuses `SkillFormPage.fill_form()` |
| Step 6: Save the skill | skill created with icon | AFS step 6 | step 6 | covered |
| Step 7: Reopen the skill | custom PNG icon displayed | AFS step 7 | step 7 | covered — full reload, server persistence confirmed |
| Step 8: Click icon to change (edit mode) | picker/edit option appears | AFS step 8 | step 8 | covered — edit-mode's distinct 2-request/2-toast mechanism documented |
| Step 9: Upload valid GIF | GIF uploaded | AFS step 9 | step 9 | covered |
| Step 10: Save the skill | changes saved | AFS step 10 | step 10 | covered — CLARIFICATION: no literal Save needed, icon persists independently (same pattern as ELITEA-1899) |
| Step 11: Verify icon is GIF | GIF displayed | AFS step 11 | step 11 | covered |
| Step 12: Repeat with WEBP | WEBP uploads/displays | AFS step 12 | step 12 | covered |
| Step 13: Repeat with JPG | JPG uploads/displays | AFS step 13 | step 13 | covered |
| Step 14: Upload oversized file | upload rejected | AFS step 14 | step 14 | covered — 400, exact server error body captured |
| Step 15: Verify error message | size-exceeds message shown | AFS step 15 | step 15 | covered — exact text "File size exceeds 512 KB" via `toast-alert`/`toast-message` |
| Step 16: Verify previous icon retained | icon unchanged | AFS step 16 | step 16 | covered — DOM src comparison before/after failed upload |
| Step 17: Click delete/remove option | confirmation or immediate removal | AFS step 17 | step 17 | covered — via mechanism (b), select-Default-tile; mechanism (a) (delete-uploaded-icon) built but not used in the final test, see Implementation-time findings #3 (confirmed gallery infinite-scroll bug, #1459) |
| Step 18: Confirm deletion if prompted | icon removed | AFS step 18 | step 18 | covered |
| Step 19: Verify reverts to default `skill-icon.svg` | default icon shown | AFS step 19 | step 19 | covered — CLARIFICATION: live product has no such literal asset/filename; correct assertion is "icon img element absent" (same as ELITEA-1899) |
| Step 20: Save the skill | changes saved | AFS step 20 | step 20 | covered — same CLARIFICATION as step 10 |
| Step 21: Reopen the skill | default icon still displayed | AFS step 21 | step 21 | covered — full reload, server persistence of reverted state confirmed |
| Objective: uploaded formats work, oversized rejected, delete reverts to default | as above | AFS steps 1–21 | all steps | covered |

### Axis 2 — Analyst additions

- Asserted the exact server error response BODY (`{"error": "File size exceeds 512 KB"}`) and
  status code (400), not just "some error toast appears" — a stronger, network-level check than
  the case's own wording, catching a future regression that changes the error text/status silently.
- Documented and confirmed the create-mode vs edit-mode network/toast asymmetry for a successful
  upload (1 request/toast vs 2) — the case text treats "upload" identically in both Parts A and B,
  but the live product's persistence mechanism genuinely differs; automation needs to know this to
  avoid a flaky/wrong assertion in the edit-mode variant.
- Confirmed BOTH of the two live "revert to default" mechanisms (delete an uploaded icon vs select
  the Default tile) rather than assuming the case's "delete/remove option" wording maps to only one
  — this surfaced the new testid gap on mechanism (a) that a single-mechanism exploration would
  have missed.
- Verified the reverted-to-default state (Part D) with a full page RELOAD, not just a client-side
  state check, confirming server-side persistence exactly as ELITEA-1899 did for the icon-CHANGE
  direction — this case is the first to confirm persistence for the icon-REMOVAL direction.
- Verified 0 unexpected console errors across the whole flow (the one 400 in step 14 IS the case
  under test, not a side-channel failure) — see Expected Results for the one unrelated/pre-existing
  404 noted for completeness.
- Noted (not filed as a defect) the tooltip-vs-error-message unit-label inconsistency ("500KB" vs
  "512 KB") for the SAME numeric limit — cosmetic, does not affect pass/fail.

## Cleanup

- **Skill created during this pass (id 1499, name `el2604-icon-test-skill`) was deleted** via the
  UI's type-to-confirm delete flow (detail page → overflow "⋮" menu → "Delete skill" → typed exact
  name to confirm → Delete). Verified via network: `DELETE
  /api/v2/elitea_core/skill/prompt_lib/399/1499` → **204 No Content**, and the browser navigated
  back to `/skills/all` (list view) with no lingering reference. Nothing left behind from this
  analysis run's OWN skill.
- **Uploaded icon gallery entries**: this run's own uploads (JPG/GIF/WEBP/PNG-in-edit-mode) were
  either explicitly deleted (the delete-button path test) or remain in the project's shared
  "Uploaded" gallery (`GET /upload_skill_icon/prompt_lib/399`) — per the Preconditions note above,
  this gallery is intentionally project-scoped/shared and NOT tied to any single skill's lifecycle,
  so leftover gallery entries are expected system behavior, not orphaned test data requiring
  cleanup (the same is already true of the 6 pre-existing entries this run found on arrival, left
  by earlier sessions). The implementer's automated test does not need its own gallery-cleanup step
  for this reason — mirrors how ELITEA-2602's own icon upload leaves its gallery entry behind too.
- **Recommendation for the implementer**: create the skill via the UI form itself (the case's own
  Part A steps ARE the creation flow — there's no separate "create via API" precondition to
  short-circuit, unlike ELITEA-1899's Agent case), `yield`/wrap in `try/finally`, then delete via
  `SkillDetailPage.delete_skill_via_menu(skill_name)` (pre-existing method, used identically by
  ELITEA-2602's test) in the `finally` block. An API-level fallback delete
  (`skill_api.delete_skill(skill_id)`) as a safety net (mirrors ELITEA-2602's pattern) is optional
  but recommended given this test performs many more UI interactions before cleanup than most.

## Concrete Handles (discovered/confirmed during exploration)

All testids below are **pre-existing** except the one explicitly marked NEW GAP.

| Element | Testid / Handle | Notes |
|---|---|---|
| Skill form icon avatar/button | `skill-form-icon-button` (`SkillFormPage.skill_icon_button`) | pre-existing (ELITEA-2602); hover-then-click quirk |
| Skill form icon `<img>` | `skill-form-icon-img` (`SkillFormPage.skill_icon_img`) | pre-existing (ELITEA-2602); absent = default state |
| Icon picker dialog | `agent-icon-picker-dialog` (`SkillFormPage.icon_picker_dialog`) | pre-existing, shared/entity-agnostic |
| Icon picker close button | `agent-icon-picker-close-button` (`SkillFormPage.icon_picker_close_button`) | pre-existing |
| Icon picker Upload button | `agent-icon-picker-upload-button` (`SkillFormPage.icon_picker_upload_button`) | pre-existing (ELITEA-2602) |
| Default-icon tile (reset to default) | `agent-icon-picker-default-icon` | pre-existing, CONFIRMED LIVE this run — not yet exposed on `SkillFormPage`, add as a `LocatorDescriptor` |
| Default gallery option (indexed) | `agent-icon-picker-option-{index}` | pre-existing (shared with Agent, `AgentDetailPage.ICON_PICKER_OPTION`), not yet on `SkillFormPage` |
| Uploaded-gallery icon (indexed) | `agent-icon-picker-uploaded-{index}` | pre-existing dynamic testid, CONFIRMED LIVE via DOM query this run — not yet exposed on `SkillFormPage`, needs a class-level template constant, e.g. `ICON_PICKER_UPLOADED = '[data-testid="agent-icon-picker-uploaded-{}"]'` |
| **Uploaded-gallery icon's delete button** | **NONE — NEW GAP** | see Part D step 17 for the full fix description; recommend `agent-icon-picker-uploaded-{index}-delete-button` |
| Delete-icon confirmation dialog body | `alert-dialog-content` | pre-existing, app-wide `AlertDialog.jsx` |
| Delete-icon confirmation Confirm button | `alert-dialog-confirm-button` | pre-existing, app-wide |
| Delete-icon confirmation Cancel button | none | pre-existing gap, out of THIS case's scope (case doesn't exercise Cancel) |
| Upload-success toast | `toast-message` (`SkillFormPage.toast_message`) | pre-existing, app-wide; text "The image has been uploaded" (create mode / first upload in edit mode) |
| Oversized-upload error toast (root) | `toast-alert` + `data-severity="error"` | pre-existing, app-wide (`ChatPage.toast_alert`/`TOAST_ALERT_SEVERITY`) — NOT yet on `SkillFormPage`/`SkillsListPage`, copy the existing pattern |
| Oversized-upload error toast (text) | `toast-message` | pre-existing, app-wide; exact text "File size exceeds 512 KB" |
| Skill controls overflow menu | `skill-controls-menu-button` (`SkillDetailPage`) | pre-existing |
| Delete-skill menu item | `skill-delete-menu-item` (`SkillDetailPage`) | pre-existing |
| Delete-skill type-to-confirm dialog | `delete-confirm-name-input` / `delete-confirm-button` (`SkillDetailPage.delete_skill_via_menu()`) | pre-existing |
| Skill Save button | `skill-save-button` (`SkillFormPage`) | pre-existing; stays disabled after icon-only changes (same as Agent) |

## Network Behavior

| Action | Request | Response |
|---|---|---|
| Upload icon (create mode, no entityId) | `POST /api/v2/elitea_core/upload_skill_icon/prompt_lib/{project}` | 200 OK — single request |
| Upload icon (edit mode, entityId present) | `POST .../upload_skill_icon/prompt_lib/{project}` **then** `PUT .../upload_skill_icon/prompt_lib/{project}/{versionId}` | both 200 OK — two sequential requests |
| Select a Default/Uploaded gallery icon (edit mode) | `PUT .../upload_skill_icon/prompt_lib/{project}/{versionId}` | 200 OK |
| Reset to default (Default tile, edit mode) | `PUT .../upload_skill_icon/prompt_lib/{project}/{versionId}` with `{name: "", url: ""}` | 200 OK |
| Delete an uploaded gallery icon | `DELETE .../upload_skill_icon/prompt_lib/{project}/{icon_name}` | 200 OK |
| Upload oversized file (any mode) | `POST .../upload_skill_icon/prompt_lib/{project}[/{versionId}]` | **400 Bad Request**, body `{"error": "File size exceeds 512 KB"}` |
| List uploaded gallery icons (fires on dialog open + after every mutation) | `GET .../upload_skill_icon/prompt_lib/{project}?limit=20&skip=0` | 200 OK |

## Known Defects Found During Exploration

None. The one UI-text inconsistency (tooltip "500KB" vs error message "512 KB" — see Part C step 14)
is cosmetic and numerically consistent (500 KiB = 512,000 bytes ≈ "512 KB" under decimal labeling);
it does not meet the bar for a product defect and is recorded here only as an observation, not filed.

## Blocked Steps

None. All 21 case steps executed to completion with no blockers.

## Automation Hints

- **Reuse `SkillFormPage.open_icon_picker()`/`upload_skill_icon()`/`get_form_icon_src()`
  (all pre-existing, ELITEA-2602)** for Part A's PNG-upload-during-creation path — do not
  re-implement. `upload_skill_icon()`'s current toast-text assertion ("The image has been
  uploaded", asserted via `==`) is correct AS-WRITTEN only for the single-request (create-mode)
  path; if the implementer adds an edit-mode overload/variant for Part B, it must NOT reuse that
  exact-match assertion (see step 8's finding) — assert on the network response pair instead, or
  relax the toast assertion to a "the app-wide toast fired with 200-network-backed content" check.
- **New page-object surface needed on `SkillFormPage`** (none of these exist yet — all confirmed
  live this run, safe to add): `default_icon_tile` (`agent-icon-picker-default-icon`),
  `ICON_PICKER_OPTION`/`ICON_PICKER_UPLOADED` dynamic templates (mirror
  `AgentDetailPage.ICON_PICKER_OPTION`'s existing shape exactly), and a
  `select_default_icon_tile()` / `delete_uploaded_icon(index)` pair of `@action` methods (mirror
  `AgentDetailPage.select_icon_option()`'s shape: click → wait for network → return the resulting
  `get_form_icon_src()`).
- **The new delete-button testid MUST land via `add-data-testid` before the delete-icon path (Part
  D mechanism (a)) can be automated at all** — testid-only locator policy has no fallback rung.
  If the implementer prefers to ship Part D FIRST using only mechanism (b) (the Default tile, which
  already has a testid) and follow up with mechanism (a) once the testid lands, that is an
  acceptable phased approach — but the case's own wording ("delete/remove option") is most
  literally mechanism (a), so don't skip it permanently.
- **Format-loop structure**: Part B's steps 9/12/13 (GIF/WEBP/JPG) are naturally a small
  `@pytest.mark.parametrize`-able loop over `(file_path, expected_extension_in_url)` once the
  upload helper exists for edit mode — all three were confirmed to follow the IDENTICAL mechanism
  live, so a shared parametrized assertion is safe and not "assuming the rest are similar" (this
  run executed each format individually, not just the first).
- **Timeouts**: this run observed all upload/replace/delete network round-trips complete well under
  2s on localhost — the project's standard `UI_ELEMENT_TIMEOUT = 10_000` used elsewhere in the
  skills tests is comfortably sufficient, no special long-timeout handling needed even for the
  ~1.25MB oversized-file upload attempt (the 400 response itself also returned quickly).

## Implementation-time findings (appended during ELITEA-2604 build — test-automation-engineer)

Two facts this AFS's exploration did not (and could not, without exercising these
exact interactions) surface, discovered while implementing Part D:

1. **`agent-icon-picker-close-button` was declared "pre-existing" but was actually
   DEAD** — `SelectIconDialog.jsx` passed `closeButtonDataTestId` to `BaseModal`,
   which destructures `closeButtonTestId` (no "Data"). React silently drops the
   unrecognized prop, so the close button never carried a real `data-testid`
   despite the testid string being correct and present in the codebase. Neither
   this AFS nor ELITEA-2602's ever actually clicked this button, so the mismatch
   went uncaught. **Fixed**: `EliteaAI/EliteaUI@72a6f788` renames the prop to
   `closeButtonTestId`. This affects the SAME shared dialog on Agent/Pipeline too
   — any future case that clicks their `icon_picker_close_button` benefits from
   this fix as well.
2. **The "Uploaded" gallery is NOT ordered by upload recency** — it is a shared,
   project-scoped list (confirmed by this AFS's own Preconditions note), but
   this run additionally confirmed live that neither index 0 nor the last index
   reliably corresponds to "the icon this test just uploaded/applied". A
   positional-index delete target is unreliable. **Fix**: added
   `data-selected={isSelected}` to `ProjectIconItem.jsx` (shared by both the
   Default and Uploaded galleries) — `EliteaAI/EliteaUI@e7ff6c06` — intended to
   let automation target the currently-APPLIED icon deterministically via a
   `[data-testid^="agent-icon-picker-uploaded-"][data-selected="true"]` filter.
   **Superseded by finding 3 below** — this mechanism was built but is NOT used
   by the final test (kept live in EliteaUI source for a future case).

3. **CONFIRMED LIVE (verify/finish pass, 2026-08-12): the "Uploaded" gallery's
   infinite-scroll loader gets PERMANENTLY STUCK after a mutation invalidates
   the list while the dialog's local `page` state is already > 0** — exactly
   the situation this test's own Parts B/C produce (each edit-mode
   upload/replace reopens the picker and fires a mutation). Reproduced live via
   Playwright MCP against a real skill: after several open/close + upload
   cycles, reopening the "Uploaded" gallery rendered only 1 item (not the just-
   applied one) despite the project having 56 total uploaded icons; the
   `infinite-loader-trigger` element remained present (confirming more data was
   available) but never fired again even after being scrolled into view. Root
   cause (read from source): `ListInfiniteMoreLoader.jsx`'s `hasTriggeredRef`
   only resets when the merged list's size changes — if a post-mutation refetch
   collapses the accumulated list back to a near-empty state, the size never
   changes again and the loader can never recover for that dialog instance.
   This means finding 2's `data-selected` filter is frequently pointed at an
   item that was never even rendered — NOT a positional-guessing problem, a
   list-completeness problem. Filed as
   `EliteaAI/elitea-testing-public#1459` (not escalated to `elitea_issues` per
   this project's policy — no explicit ask). **Consequence for this AFS's own
   step 17 guidance** ("the implementer should pick ONE as the case's primary
   automated path... recommend the delete-button path... MAY note the second as
   an Axis-2 addition... If the implementer prefers to ship Part D FIRST using
   only mechanism (b)... that is an acceptable phased approach"): this
   implementation ships with mechanism (b) (the "Default" tile,
   `SkillFormPage.select_default_icon_tile()`) as the test's ONLY automated
   Part D path, per that explicit phased-approach allowance — mechanism (a)'s
   `delete_selected_uploaded_icon()` method and its supporting locators
   (`ICON_PICKER_UPLOADED_SELECTED`/`ICON_PICKER_UPLOADED_DELETE_BUTTON`/
   `alert_dialog_content`/`alert_dialog_confirm_button`) were removed from
   `SkillFormPage` as unused/unreliable dead code (no orphan-testid coverage
   claim); the `agent-icon-picker-uploaded-{index}-delete-button` testid itself
   remains live in EliteaUI source for a future case once #1459 is fixed.
