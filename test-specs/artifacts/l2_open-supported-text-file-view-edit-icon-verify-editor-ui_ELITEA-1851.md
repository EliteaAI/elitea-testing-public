# Test Case: File Preview/Edit – Open Supported Text File via View/Edit Icon and Verify Editor UI

## Metadata
- **TMS ID**: ELITEA-1851
- **Linked Story**: none
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private`). Every code citation below was verified
  against a **fresh `git fetch origin`** in `../EliteaUI`; provenance recorded
  per-handle in § Concrete Handles.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live, all 14
  case steps observed, no product defects found. This is a brand-new UI surface
  for this suite (the file preview/edit canvas has never been touched by any
  existing spec or page-object method — confirmed via `grep -rn "Preview\|Editor"
  automation/pages/artifacts_page.py` → no hits), so no already-covered/extend
  check applies. Two case-text CLARIFICATIONS filed (see § Known Defects) — per
  the reverse-masking guard these do NOT block automation; the live, correct
  behavior is what gets asserted. A full cluster of `testid needed:` gaps blocks
  policy-compliant locating of every editor-panel control (none of them carry a
  testid today) — additive, well-precedented frontend work, not an
  access/data/env blocker, so status stays `ready-for-automation` per
  `.agents/role-overrides.md` § Analyst slot (a testid gap is never softened to
  `blocked`).

## Preconditions
- User is logged in to the Elitea platform (on localhost, `auth_state` fixture
  skips login).
- A project is selected/accessible (`Private` in this run).
- A bucket exists containing one supported text file (case names it
  `bucket-1`/`machine_learning.py`, Python, 18.5 KB).
  **Confirmed live this run: `bucket-1` does NOT exist in the shared local dev
  environment** (363 pre-existing buckets checked via the in-app bucket search
  for the literal string `bucket-1` — zero matches; same "case-text placeholder,
  not a real fixture name" pattern the sibling ELITEA-1832/ELITEA-1839 AFS files
  already established for this feature area). The bucket + file must be seeded by
  the test itself — see § Test Data. The exact byte size ("18.5 KB") is also a
  case-text placeholder, not a fixture requirement: assert against whatever the
  seeded content's own size renders as (this run's fixture rendered as `16.9 KB`
  for a 17,354-byte file — KB is computed on a 1024 basis).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the existing `artifact_bucket` pytest fixture
  (`automation/fixtures/data_fixtures.py:455`) — function-scoped, creates a
  uniquely-named bucket via `ArtifactAPI.create_bucket()` and deletes it via
  `ArtifactAPI.delete_bucket()` in teardown. Do **not** hardcode `bucket-1`.
- **File**: seed a `.py` file directly via `ArtifactAPI.upload_file(bucket_name,
  "machine_learning.py", content, content_type="text/x-python")`
  (`automation/api/client.py:1282`) — same "seed via API, not the upload UI"
  approach the sibling ELITEA-1839 AFS already established for this feature area
  (faster, browser-independent; the case doesn't ask to test the *upload* flow,
  only the *open-for-preview* flow). Confirmed live this run: the identical
  `PUT /artifacts/s3/{bucket}/{key}?project_id=...` endpoint `upload_file()`
  already wraps is what the browser's own upload UI calls (§ Network Behavior of
  the sibling ELITEA-1839/1840 AFS files already document this for other file
  types; re-confirmed for `.py` in this run via the Type column rendering
  `"Python"` after either upload path).
- **Content constant**: any syntactically-plausible Python content is sufficient
  — the case only asserts *that* the file opens and *what UI chrome* surrounds
  it, never a specific line of code. This run used a small `LinearRegressor`
  module (~17.3 KB, confirmed live to auto-detect as `"Python (detected)"` in
  the editor's language selector — see Test Step 7).

No `reuse-existing` fixture applies — same reasoning as ELITEA-1832/1839: a
bucket in this specific state (exactly one known-language file) isn't safe to
share across parallel/serial runs.

## Test Steps

1. Navigate directly to `${BASE_URL}/artifacts?bucket={bucket_name}` (folds case
   steps 1–2: Artifacts page load + bucket selection into one navigation, same
   pattern `ArtifactsPage.navigate_to_bucket()` already uses).
   - **Verify**: right-panel file table shows exactly one row —
     `machine_learning.py`, Type `"Python"`, a non-empty Size string (case step 3).
2. Locate the file row's "Preview {filename}" icon button (the View/Edit
   loop/magnifier icon) in the Actions cell (case steps 4–5, folded).
   - **Verify**: the button (`aria-label="Preview machine_learning.py"`) is
     present and visible. **CLARIFICATION (not a defect) — see § Known
     Defects**: confirmed live via computed style (`opacity: "1"`,
     `visibility: "visible"`, `display: "flex"`) that this icon is **always**
     rendered visible, not hover-gated — hovering the row is not required to
     reveal it, contradicting the case's framing ("Hover over the row" →
     "icon appears on hover"). Assert **presence**, not a hover-triggered
     appearance.
3. Click the Preview icon button (case step 6).
   - **Verify**: the editor panel opens in the main area, replacing the file-list
     view (case step 7); the browser URL immediately updates to
     `.../artifacts?bucket={bucket_name}&file=machine_learning.py` (case step 14 —
     confirmed live the URL update is synchronous with the click, not a separate
     later event).
4. Verify the panel header shows the full file path (case step 8).
   - **Verify**: header text is exactly `"{bucket_name}/machine_learning.py"`
     (confirmed live via `PreviewHeader.jsx`'s `canvasTitle` — for a path this
     short, `fullPath` is rendered verbatim; the `bucket/…/folder/file`
     truncation only kicks in beyond 3 path segments, not reached by this case).
5. Verify the language label (case step 9).
   - **Verify**: the language selector shows `"Python (detected)"` with a
     dropdown affordance — confirmed live via `Select.SingleSelect`
     (`PreviewHeader.jsx`), which appends `" (detected)"` to whichever option's
     `value` matches the auto-detected language.
6. Verify the file content is displayed with line numbers (case step 10).
   - **Verify**: a CodeMirror instance renders the file's text with a
     left-hand line-number gutter (`.cm-lineNumbers`) — confirmed live, 183+
     numbered lines visible/scrollable for this run's ~17.3 KB fixture.
7. Verify the Save/Discard buttons (case step 11).
   - **Verify presence**: both a `"Save"` and a `"Discard"` button are visible
     in the top-right. **CLARIFICATION (not a defect) — see § Known Defects**:
     confirmed live via both DOM inspection (`disabled: true`, `Mui-disabled`
     class) and source (`PreviewHeader.jsx`:
     `disabled={isSaving || !hasUnsavedChanges}`) that **both buttons start
     DISABLED** on a freshly opened, unedited file — they do NOT start
     "active" as the case's step 11 claims. Assert the **correct, live**
     initial state: Save and Discard are both **present but disabled**.
     (Confirmed the *converse* is also true live, as a sanity check beyond
     this case's own scope: typing one character in the editor flips both
     buttons to `disabled: false` and Save visually turns solid/blue — i.e.
     the case's "Save active/highlighted blue" description is the correct
     description of the ENABLED state, just wrongly attributed to the
     unedited initial state. See § Known Defects for the CLARIFICATION
     filed and § Axis 2 for this confirmatory, out-of-scope observation.)
8. Verify the 3-dot actions menu (case step 12).
   - **Verify**: the overflow-menu button (testid `file-preview-overflow-menu-menu-button`
     — see § Concrete Handles) is visible and NOT disabled; clicking it opens a
     dropdown containing `"Copy Content"`, `"Download"`, `"Delete"` — confirmed
     live via `PreviewHeader.jsx`'s `menuItems` array. (The dropdown's own
     contents are ELITEA-1856's scope — this case only needs the trigger
     **present, enabled, and clickable**, which is confirmed.)
9. Verify the close icon (case step 13).
   - **Verify**: an X icon button (`aria-label="Close preview"`) is present at
     the top-left of the header, to the left of the file-path title.

## Expected Results
- Clicking the Preview icon on a supported text file's row opens the editor
  panel in the main area, replacing the file-list view.
- The panel header shows the full `{bucket}/{filename}` path.
- The language selector shows the auto-detected language, suffixed
  `" (detected)"`, with a dropdown affordance.
- The file's text content renders inside a CodeMirror editor with a
  left-hand line-number gutter.
- Save and Discard buttons are both visible, both **disabled** until the
  content is actually edited (CLARIFICATION vs. case text — see below).
- The 3-dot overflow menu is visible, enabled, and opens a dropdown on click.
- A close (X) icon is present in the header.
- The URL updates to include `&file={filename}` the instant the panel opens.
- No console errors during the flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket "bucket-1" contains "machine_learning.py" (Python, 18.5 KB) | Precondition state exists | Test Data + Test Step 1 | Fresh bucket + file seeded via `ArtifactAPI.upload_file()`; state proven by Test Step 1's file-row assertion. Neither the literal bucket name nor the exact byte size are asserted — both are case-text placeholders (confirmed live: `bucket-1` doesn't exist anywhere in the shared dev environment) | asserted *(seeded, not reused — placeholder naming/size not literal)* |
| Step 1: Navigate to Artifacts section | Artifacts page loads | Test Step 1 | Proven via Test Step 1's file-row assertion (no separate bare page-load/breadcrumb check — same "proxy assertion" shape ELITEA-1839 already established for this page object) | asserted *(proxy assertion, folded into Test Step 1)* |
| Step 2: Click bucket-1 in bucket list | Bucket is selected | Test Step 1 | Direct `?bucket=` URL navigation (`navigate_to_bucket()`), proven by the file row appearing | asserted *(decomposed — direct navigation, not a left-panel click)* |
| Step 3: Verify file table shows machine_learning.py (Python, 18.5 KB) | File visible | Test Step 1 | Row Name/Type cells; Size asserted as non-empty/well-formed, not the literal "18.5 KB" (placeholder — see precondition row) | asserted *(Type asserted exactly; Size asserted as present/well-formed, not the literal value)* |
| Step 4: Hover over the file row | "View/Edit file" icon appears on hover | Test Step 2 | `button[aria-label="Preview machine_learning.py"]` presence | **clarification** — icon is always rendered (not hover-gated); see § Known Defects |
| Step 5: Verify a "View/Edit file" (loop/magnifier) icon appears on hover | Icon is visible | Test Step 2 (folded) | Same as above | **clarification** (folded into step 4's row) |
| Step 6: Click the "View/Edit file" icon | Editor panel opens in main area | Test Step 3 | Panel visible after click | asserted |
| Step 7: Verify the file opens in the editor panel | Editor is visible | Test Step 3 (folded) | Same as above | asserted |
| Step 8: Verify the panel header displays the full file path | Header shows correct path | Test Step 4 | Header text equals `"{bucket}/machine_learning.py"` | asserted |
| Step 9: Verify a language label is shown: "Python (detected)" with a dropdown arrow | Language label is present | Test Step 5 | Language selector text | asserted |
| Step 10: Verify the file content is displayed with line numbers on the left | Line numbers are visible | Test Step 6 | `.cm-lineNumbers` gutter present | asserted |
| Step 11: Verify "Save" (active/highlighted blue) and "Discard" buttons are present ... Save is active | Both visible, Save active | Test Step 7 | Both buttons visible; disabled-state asserted as the correct (disabled) initial state, not "active" | **clarification** — case's "Save is active" on fresh open contradicts observed/source-confirmed behavior; see § Known Defects |
| Step 12: Verify a 3-dot (ellipsis) actions menu icon is present ... active and clickable | Menu present and clickable | Test Step 8 | Menu button visible, not disabled, opens dropdown on click | asserted |
| Step 13: Verify an X (close) icon is present | Close icon is visible | Test Step 9 | `button[aria-label="Close preview"]` visible | asserted |
| Step 14: Verify the URL updates to reflect the open file path | URL includes file parameter | Test Step 3 (folded) | `page.url` contains `bucket={bucket}&file=machine_learning.py`, matching the case's own example format exactly | asserted |
| Expected Final State: editor open with all required UI elements | Composite pass condition | Test Steps 3–9 | Combination of the above | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | `page.on("console", ...)` listener, type == "error" only | asserted |

### Axis 2 — Observables asserted beyond the case
- **Close-button functional check** (not just visibility, case step 13 only asks
  for presence) — *added: clicked it live and confirmed the panel actually
  closes (URL drops `&file=...`, file-list view returns) — proves the element is
  wired, not just rendered. Noted implementation detail: the first click after
  only a `hover()` can land on the MUI Tooltip's own overlay instead of the
  button (confirmed live — see § Automation Hints); a direct click (no prior
  hover) or `force=True` avoids this.*
- **Save/Discard enable-on-edit transition** (not part of this case's own
  steps — ELITEA-1852's scope) — *added: typed one character into the editor
  live and confirmed both buttons flip to `disabled: false` and Save turns
  solid/blue, then clicked Discard and confirmed a "Are you sure you want to
  discard changes?" confirmation dialog appears, confirming Discard reverts to
  the disabled state again. This is the evidence base for the CLARIFICATION in
  § Known Defects — not itself a required assertion of THIS case, and not
  carried into Test Steps above.*
- **No console errors during the whole open → verify → close flow** — *added:
  standard silent-error guard, consistent with this feature area's existing
  precedent (ELITEA-1832/1839).*

## Cleanup
1. Delete the seeded bucket via `ArtifactAPI.delete_bucket(bucket_name)` in the
   `artifact_bucket` fixture's own teardown. **Known pre-existing defect,
   already filed ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)):**
   this delete call 404s in the current dev environment (documented by
   ELITEA-1839's AFS for this same fixture) — the bucket may leak; not new to
   this case, out of scope to fix here.
2. No other entities are created by this case (no Agent, no Toolkit, no
   Credential).
3. **This exploration run's artifacts** (not part of the automated test):
   bucket `autotest-bucket1-1851` was created via the live UI in the `Private`
   project to verify the case, containing `machine_learning.py` (~16.9 KB) at
   time of hand-off. Left in place — matches this feature area's existing
   convention (363+ un-deleted `autotest-*` buckets already present). Safe for
   the implementer or lead to delete at any time via
   `ArtifactAPI.delete_bucket("autotest-bucket1-1851")`.
4. Local exploration screenshots (scratchpad, untracked, not committed):
   `1851-14-file-in-table.png`, `1851-15-wide-view.png`,
   `1851-16-editor-open.png`, `1851-17-dotmenu-open.png`,
   `1851-19-closed2.png`, `1851-20-after-edit.png`,
   `1851-21-discard-confirm.png` — available on request; not attached to the
   AFS itself (not this repo's screenshot-evidence convention for AFS files).

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this
project's locator policy (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md` § Analyst slot) is **testid-only, no fallback
ladder**. An element without a testid is specced below as `testid needed:
{name}` — not softened into a note, not resolved via role/aria-label. Every
row's Provenance was checked against a fresh `git fetch origin` in
`../EliteaUI`.

| Element | testid | Provenance | Status | Notes |
|---|---|---|---|---|
| File row (existing, pre-case) | `artifacts-file-row` | on-main ✓ | existing | Already used by `get_file_row_text()`/`_file_rows()` |
| File row's Preview/View-Edit icon | `testid needed: artifacts-file-preview-{filename}-button` (dynamic, filename-templated — same class-constant pattern as `ARTIFACT_ACTIONS_MENU_BUTTON`) | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | Currently only `aria-label="Preview {filename}"` on a bare `MuiIconButton` (`ArtifactTable.jsx`'s row-actions render) — no `data-testid` at all. Confirmed live: **always rendered** (`opacity:1`, `display:flex`, no hover gating) — do not port a "hover then wait" sequence into the locating code, a direct click suffices. |
| Editor panel — close (X) button | `testid needed: artifacts-file-editor-close-button` | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | `PreviewHeader.jsx` line ~172, `aria-label="Close preview"` only. **MUI Tooltip overlay quirk** (same family as `.claude/rules/mui-patterns.md` § MUI Overlay Interception): confirmed live a click immediately following only a `hover()`/mouse-move can land on the Tooltip's own rendered label instead of registering on the button — a direct `click()` with no preceding hover worked reliably every time in this run; if the implementer's interaction sequence does hover first, use `force=True` or a settle wait. |
| Editor panel — header/title (full path text) | `testid needed: artifacts-file-editor-header` | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | `PreviewHeader.jsx`'s `canvasTitle` `Typography` — plain text node, no testid. Truncates to `bucket/…/folder/file` beyond 3 path segments (not reached by this case's flat-bucket-root file). |
| Editor panel — language selector | `testid needed: artifacts-file-editor-language-select` | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | Custom `Select.SingleSelect` component (`PreviewHeader.jsx`) — no testid threaded through. Renders `"{Label} (detected)"` only when the current value matches `detectedLanguage`. |
| Editor panel — Save button | `testid needed: artifacts-file-editor-save-button` | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | `PreviewHeader.jsx`, `Button.BaseBtn`. `disabled={isSaving \|\| !hasUnsavedChanges}` — confirmed live: **disabled** on fresh open, flips to enabled + solid/blue after any edit. Assert via the `disabled` attribute/`Mui-disabled` class, not visual color. |
| Editor panel — Discard button | `testid needed: artifacts-file-editor-discard-button` | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | Same component/disabled-condition as Save. Confirmed live (out of this case's own scope): clicking it while enabled opens a separate, also-un-testid'd confirmation dialog ("Are you sure you want to discard changes?") — relevant context for whichever future case (ELITEA-1852) actually exercises the edit→discard flow; this case only needs Discard's **presence**, never clicks it. |
| Editor panel — 3-dot overflow menu button | `file-preview-overflow-menu-menu-button` | **on-main ✓** (EliteaAI/EliteaUI@7515f444) | existing | Generated by the shared `DotMenu` component from its `id="file-preview-overflow-menu"` prop (`PreviewHeader.jsx`) — same `{id}-menu-button` convention already used for `bucket-menu-{name}-menu-button`. Pre-existing, not something this case's automation needs to add. |
| Editor panel — 3-dot menu's items (Copy Content / Download / Delete) | none — **needs-adding**, out of this case's scope | **confirmed missing on both `origin/main` and `automation/testids`** | needs-adding (defer to ELITEA-1856) | `DotMenu.jsx` only emits a per-item testid when the item object carries a `key` field; `PreviewHeader.jsx`'s `menuItems` array pushes no `key`. This case only needs the dropdown's **presence after click**, not per-item locating — deferred to whichever case (ELITEA-1856) actually clicks a specific item. |
| Editor content (CodeMirror line numbers + text) | `.cm-lineNumbers` / `.cm-content` (CodeMirror internal DOM) | third-party editor internal | **candidate #579 sanctioned exception** — needs a real app testid on the WRAPPING container first | No app-level testid wraps the CodeMirror instance at all today (confirmed live — zero `data-testid` ancestors between the editor and the panel root). Per `.agents/testing.md` § Locator policy stop+flag discipline: add `artifacts-file-editor-content` (or similar) as a real app testid on the wrapping container, THEN scope `.cm-lineNumbers`/`.cm-content` off that parent (same shape as `mcp_form_page.py`'s `raw_json_editor_content` — a `[data-testid="…"] .cm-content` chain, not a free-floating page-level `.cm-content` selector). This case only needs line-numbers/content **presence**, not text extraction — a simpler bar than ELITEA-1852's eventual edit-content assertions. |

## Network Behavior
- Opening the editor fetches the file's raw content via
  `GET {ELITEA_URL}/artifacts/artifact/default/{project_id}/{encodeURIComponent(bucket)}/{encodeURIComponent(filePath)}`
  — confirmed via source (`useArtifactContentFetch.hooks.js:72`, "same artifact
  content endpoint as the download button"), the identical endpoint the sibling
  ELITEA-1839 AFS already documents for the Download menu item. **Fidelity
  caveat**: this run's CDP-based tooling (see § Automation Hints on tooling) did
  not reliably capture the live request/response pair for this specific call
  (the network listener attaches per-invocation and this repeated series of
  single-shot CLI calls kept missing the window) — the endpoint above is
  source-grounded with high confidence, not independently re-confirmed via a
  captured HTTP transaction in this run. The implementer should confirm it once
  via `page.expect_response()` when writing the test (cheap, and closes this
  gap with a live Playwright-native capture instead of the CDP tooling
  workaround this run used).
- No other request observed between the Preview-icon click and the editor
  becoming interactive.

## Known Defects Found During Exploration
**No product defects** — both divergences below are the live product behaving
*correctly*; the case text is what's stale (reverse-masking guard,
`.agents/role-overrides.md` / `.agents/testing.md`). Filed as CLARIFICATIONS,
not bugs, per `.agents/profile.md` § Bug filing (lightweight, this-repo-only
issue, `question` label per the load-bearing-label convention in
`.agents/profile.md` § Issue tracker):

1. **Case steps 4–5 ("hover reveals the View/Edit icon") vs. live behavior
   (icon is always visible).** Confirmed via computed style
   (`opacity:"1"`, `visibility:"visible"`, `display:"flex"` — no hover
   interaction performed before the check) that the Preview icon button
   renders unconditionally for every file row, not gated behind `:hover`.
   This matches the exact "confirmed always-visible, not hover-gated" pattern
   the sibling ELITEA-1839 AFS already documented for the file row's *dot-menu*
   trigger in this same feature area — i.e. this app's row-actions generally
   don't hide behind hover, and the case text's hover framing is stale
   authoring shorthand, not a regression.
2. **Case step 11 ("Save is active" on initial open) vs. live behavior
   (Save/Discard both start disabled).** Confirmed via DOM (`disabled: true`,
   `Mui-disabled` class) AND source
   (`PreviewHeader.jsx`: `disabled={isSaving || !hasUnsavedChanges}`) that
   both buttons are disabled until the user actually edits the content — a
   deliberate, sensible product design (nothing to save/discard on an
   unmodified file). Confirmed the converse live too: typing a single
   character flips both to enabled and Save turns solid/blue — i.e. the
   case's description of the "active" visual state is itself accurate, just
   wrongly attributed to the wrong moment (open-time instead of
   after-first-edit). This is consistent with sibling case ELITEA-1857's own
   title ("... Save/Discard Inactive [by default]") describing the same
   family of behavior for markdown files — ELITEA-1851's case text is simply
   the one written inconsistently with that established default.

Filed as lightweight `question`-labelled issues in `EliteaAI/elitea-testing-public`
per the standard analyst bug-filing routing (no separate GH tracking issue
exists for this batch board — `cov60` is local-file-only — so each names the
TMS case id `ELITEA-1851` directly instead of a `#<task>` back-reference), NOT
escalated to `EliteaAI/elitea_issues` (no app-bug verdict applies — these
aren't application defects):
- [#994](https://github.com/EliteaAI/elitea-testing-public/issues/994) —
  Preview icon always visible, not hover-gated (case steps 4–5).
- [#995](https://github.com/EliteaAI/elitea-testing-public/issues/995) —
  Save/Discard start disabled on fresh open, not "active" (case step 11).

## Blocked Steps
None. The full cluster of `testid needed:` rows in § Concrete Handles are
implementer work items (per `.agents/role-overrides.md` § Analyst slot: "not
softened into a MINOR defect or a note; it is implementer work, and the AFS is
its work order"), not analyst-side blockers — additive `add-data-testid` work
on components that already exist and already render correctly, not an
access/data/environment gap.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: this is a **brand-new sub-area** of `automation/pages/artifacts_page.py`
  (2100+ lines already) — no existing method touches the preview/editor canvas.
  Given the file's size, consider whether this warrants a dedicated
  `artifact_editor_page.py` / mixin per `.claude/rules/page-objects.md` "one
  class per responsibility" guidance, or whether it stays appended to
  `ArtifactsPage` (this and the file's other List/right-panel state are tightly
  coupled — same page, same URL, just a different pane) — flagging as an
  architecture call for the implementer/lead, not dictating one.
- Fixtures: reuse `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`)
  + `ArtifactAPI.upload_file()` (`automation/api/client.py:1282`) to seed
  `machine_learning.py` — no browser-driven upload needed (§ Test Data).
- Navigation: `${BASE_URL}/artifacts?bucket={bucket_name}` in one direct
  navigation (same pattern `navigate_to_bucket()` already uses) is sufficient —
  no subfolder involved in this case.
- The Preview icon is visible without hovering in the current live app (Test
  Step 2 clarification) — a direct click on the (once-added) testid is
  sufficient; do not add a hover-then-wait sequence.
- **Tooling note, not a product concern**: this analyst pass used
  `browser-verify` (CDP) on an isolated Chrome instance (port 9223,
  `--headless=new`) per this batch's Browser Lane 1 assignment — the shared
  Playwright MCP was intentionally not used. One CDP-specific wrinkle
  encountered and resolved during exploration, irrelevant to the Playwright
  implementation: the page renders **two** hidden `<input type="file">`
  elements (one for the bucket-menu upload entry point, one for the
  toolbar/empty-state entry point) with no distinguishing DOM attribute; a raw
  `document.querySelector('input[type=file]')` grabs the wrong one for the
  toolbar path (fires a `"No bucket selected for upload"` toast from the
  *other* entry point's `handleBucketFileChange` guard). This is a non-issue
  for Playwright's own `expect_file_chooser()`/`set_files()` idiom, which binds
  to the specific triggering click rather than guessing a bare CSS selector —
  noted here only so a future CDP-based exploration doesn't re-lose the same
  hour.
- Wait strategy: no fixed timeout needed anywhere in this flow — the editor
  panel, header, language label, and button states are all synchronously
  present once the panel mounts (confirmed live; no loading spinner/skeleton
  state was observed for a ~17 KB file). A larger/slower file might behave
  differently — out of this case's scope (18.5 KB per the case's own test
  data, well within what rendered instantly here).
- Console-error check: no new console errors observed across the whole
  open → inspect → close flow (§ Axis 2).
