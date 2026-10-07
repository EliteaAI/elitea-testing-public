# Test Case: Artifacts Landing Page UI – Empty Bucket (No Files)

## Metadata
- **TMS ID**: ELITEA-1805
- **Linked Story**: [EliteaAI/elitea-testing-public#2392](https://github.com/EliteaAI/elitea-testing-public/issues/2392) (board #9 tracking card)
- **Priority**: l3 (medium — as authored in the source TMS case frontmatter, `priority: medium`; maps to `l3` per `spec-format.md`'s digit table, `3`=medium — NOT `l2`, matching this folder's own established high→`l2`/medium→`l3` convention, e.g. siblings ELITEA-1809/1811/1856-1862)
- **Environment Explored**: DEV as deployed (`https://dev.elitea.ai/app/artifacts`), project `Private`. Auth via `scripts/dev_storage_state.py`-refreshed storage state.
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live (all 11 case steps observed). Two genuine case-text/product-behavior divergences found and filed as clarifications (not product bugs — see below); one pre-existing clarification (#1617) re-confirmed live and reused as-is per dispatch instructions. No defect blocks completion of the case; both findings are isolable tail-end steps per `.agents/testing.md`'s analysis-time sanctioned-RED entry, so `defect-found` does not apply.

**MCP note:** the Playwright MCP server's bundled Chrome binary is not present in
this container (`Chromium distribution 'chrome' is not found at
/opt/google/chrome/chrome`) — fell back to a direct `playwright.sync_api` script
driving the real browser (chromium at `/opt/ms-playwright/chromium-1243`, headless)
against the live DEV storage state. All handles below were exercised live, not
inferred from source alone.

## Overlap check vs existing automation
`automation/pages/artifacts_page.py` was read in full (3363 lines). No existing
test in `automation/tests/ui/artifacts/` touches the Artifacts **landing page's**
own left-panel header/footer/storage-selector or the empty-bucket main-panel
rendering as its own subject — existing specs all operate on an
already-selected, already-populated bucket (upload/download/delete/preview
flows). `test_landing_page_empty_bucket` (the TMS case's own stale
`automation_test_id`) does not exist anywhere in `automation/factory` — verified
(`git log automation/factory | grep 1625` → no hit; the file doesn't exist in the
tree). Treated as a fresh case per the dispatch's own framing. **Zero behavioral
overlap** → `ready-for-automation`.

## Preconditions
- User is logged in (`${TEST_USER}`, API-login `auth_state` fixture).
- At least one bucket with zero files exists in the project. **Case's "as" is a
  placeholder**, not a literal name to hardcode (same convention as
  ELITEA-1808/1809/1832/1839/1866) — this run created a fresh bucket
  `elitea1805-empty` via the UI "New Bucket" form (project `Private` had **zero**
  buckets at session start — confirmed via the footer reading `"Buckets:0"` before
  creation).

## Test Data
### reuse-existing
- None safely reusable — an empty bucket's "emptiness" is only guaranteed by the
  test's own fresh creation (reusing a shared bucket risks another test having
  uploaded a file into it between runs).

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket name**: a fresh, unique, zero-file bucket, e.g.
  `f"autotest-empty-{int(time.time()*1000) % 1000000}"` — validated live against
  `CreateBucket.jsx`'s yup schema (`^[a-zA-Z][a-zA-Z0-9-]*$`, max 56 chars).
- **Retention policy**: leave at the form's default (`"Years"` / `1`) — the case
  never varies this field; confirmed live the resulting tooltip reads
  `"Retention Policy: 1 Year"`.
- No file upload — the case's entire subject is the zero-file state.

### generate-shared-with-cleanup
- None.

## Test Steps

**Step 0 (precondition setup, not a numbered case step) — Create the empty
bucket.**
- Click `artifacts-create-bucket-button`, fill `artifacts-bucket-name-input`
  with the generated name, leave retention at default, click
  `artifacts-bucket-save-button`.
- **Verify**: `POST .../artifacts/buckets/...` → `200 OK`; bucket row
  `[data-testid="artifacts-bucket-row-{name}"]` becomes visible on the landing
  page.

1. Navigate to `${BASE_URL}/artifacts` (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible.
2. Verify the left-panel header (case step 2).
   - **Verify**: `artifacts-buckets-heading.text_content() == "Buckets"` (DOM
     text is "Buckets" — the case's "BUCKETS" describes the CSS
     `text-transform: uppercase`, not the literal content, same note already on
     the existing `buckets_heading` field). The "folder icon" the case refers to
     is the create-bucket control itself — `artifacts-create-bucket-button`
     visible (confirmed live: `NewFolder` icon, `aria-label`-less but
     testid'd). The "search icon" is `artifacts-search-buckets-button` visible
     (confirmed live, `aria-label="Search buckets"` on hover-free read — reuse
     the existing attribute-read technique from ELITEA-1809's AFS, no popper
     wait needed).
3. Verify the bucket list under the storage provider header (case step 3).
   - **Verify**: a storage-provider block reading `"Storage:"` + the storage
     name (confirmed live: `"Storage:Elitea S3 storage"`) is visible above the
     bucket list, with a dropdown chevron SVG as its last child (confirmed live
     via DOM dump — purely decorative, no accessible name; verified **visually**
     via screenshot rather than a manufactured DOM handle, since no step
     interacts with the chevron itself — clicking the container opens the
     storage-selection menu, which this case never exercises). At least one
     bucket row (`BUCKET_ROW_ANY_SELECTOR`) is visible beneath it.
4. Click the empty bucket's row (case step 4).
   - **Verify**: `[data-testid="artifacts-bucket-row-{name}"].get_attribute("data-selected") == "true"` —
     state read as an attribute, not a class/positional guess.
5. Verify highlighting + left-panel "No files in this bucket" (case step 5).
   - **Verify (highlight)**: same `data-selected="true"` read as Step 4 — this
     part of the case holds exactly as written.
   - **Verify (left-panel "No files in this bucket") — CONFIRMED CASE-TEXT
     DIVERGENCE, filed as clarification** (issue `EliteaAI/elitea-testing-public#2393`,
     sibling of `#651`): on a bucket's **first-ever** selection in the page's
     lifetime, this sub-label does **not** appear after a single click — only
     the main panel updates. Live-confirmed deterministic 3-click toggle
     pattern on the SAME row: click 1 (not yet active) → selected, no expand;
     click 2 (already active) → expands, label appears; click 3 → collapses
     again. Root cause is the same `handleSelectBucket`
     `if (isActive) onToggle(...)` gate `#651` already documented for
     ELITEA-1824 (an *already*-active row's re-click), just hit on its
     first-selection edge here. **Automate the case's literal intent anyway**:
     after the Step 4 click, if the sibling isn't yet visible, click the SAME
     row a second time (a deliberate, intentional toggle — not a retry-the-same-
     action loop) before asserting; this reaches the real, confirmed, stable
     end state. Handle: `[data-testid="artifacts-bucket-row-{name}"] + div`
     (css rung — see § Concrete Handles for the ladder rationale).
6. Verify the main-panel header shows the bucket name (case step 6).
   - **Verify**: `artifacts-breadcrumb-bucket-label.text_content() == name`.
7. Verify no file table in the main panel (case step 7).
   - **Verify**: `artifacts-file-row` count == `0`.
8. Verify the main-panel empty state (case step 8).
   - **Verify**: `artifacts-empty-state.text_content() == "No files in this bucket"`;
     `artifacts-upload-files-empty-state-button` visible. The icon above the
     message (confirmed live: `UnavailableIcon`, decorative, no role/label) —
     verified **visually** via screenshot (see § Coverage Map Axis 1 disposition
     note; no DOM handle manufactured for a purely decorative element no step
     interacts with).
9. Verify the top-right toolbar icons (case step 9).
   - **Verify — CONFIRMED CASE-TEXT DIVERGENCE, filed as clarification**
     (issue `EliteaAI/elitea-testing-public#2394`): for an empty bucket, assert
     the OPPOSITE of the case's literal wording — `artifacts-file-search-input`,
     `artifacts-upload-files-button`, `artifacts-download-files-button`, and
     `artifacts-delete-files-button` all resolve to **zero** elements
     (`ArtifactTableToolbar.jsx`'s `{!isEmptyFiles && (...)}` gate unmounts the
     entire right-hand action group when the file list is empty — confirmed
     live, by design: nothing to search/select/download/delete, and the
     center "Upload files" button from Step 8 already covers the upload need).
10. Verify the left-panel footer (case step 10).
    - **Verify**: footer text contains `f"Buckets:{N}"` and `f"Size:{X}"` with
      `N` == the actual bucket count and a non-empty size string (confirmed
      live format is `"Buckets:1Size:0 B"` — no literal "MB" unit; the case's
      "X MB" is a generic placeholder, not literal text to match).
11. Verify the retention/file-count tooltip (case step 11).
    - **Verify — pre-existing clarification, re-confirmed live, reused per
      dispatch instructions** (`EliteaAI/elitea-testing-public#1617`, still
      accurate on DEV today): hovering the bucket NAME in the left panel shows
      **nothing** (confirmed live: `[role="tooltip"]` count stays `0` after a
      real `.hover()` + 1.2s wait — this bucket's short name never triggers the
      conditional-overflow tooltip). The real retention/file-count tooltip is on
      the main-panel info icon (`aria-label="Bucket info"`, next to the
      breadcrumb). Hovering it shows, confirmed live:
      `"Retention Policy:1 YearNumber of files:0"` (two stacked rows,
      concatenated in `.text_content()`) — matches the case's test-data
      template `"Retention Policy: X, Number of files: 0"` once `X` =
      `"1 Year"` is substituted. **Spec step 11 against this real location**,
      linking #1617.

## Expected Final State
- The empty-bucket landing page renders left-panel header (heading + create +
  search), storage-provider selector, the bucket row (selected, highlighted via
  `data-selected`), the left-panel tree's own "No files in this bucket" line
  (reachable via the confirmed toggle sequence — see Step 5), the main-panel
  breadcrumb header, no file table, the centered empty state (icon + message +
  Upload button), **no** top-right toolbar actions (by design, confirmed via
  #2394), the footer bucket-count/size, and the info-icon tooltip with the
  correct retention/file-count content (per #1617's confirmed location).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | Session valid | Preconditions | `auth_state` fixture | asserted |
| Precondition: an empty bucket exists ("as" placeholder) | Collision-free empty bucket | Preconditions + Test Step 0 | fresh bucket created via UI form | asserted *(generated unique name, not literal "as" — established placeholder convention)* |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Left-panel header (BUCKETS + folder icon + search icon) | Header correct | Test Step 2 | heading text + 2 testid visibility checks | asserted |
| Step 3: Bucket list under storage provider + dropdown arrow | List visible | Test Step 3 | storage block text + `BUCKET_ROW_ANY_SELECTOR` + chevron visual check | asserted *(chevron verified visually, no DOM handle — see § Concrete Handles)* |
| Step 4: Click empty bucket | Bucket selected | Test Step 4 | `data-selected="true"` | asserted |
| Step 5: Bucket highlighted + "No files in this bucket" in left-panel tree | Both shown | Test Step 5 | highlight: `data-selected`; tree label: toggle-then-assert sequence | asserted *(tree label needs an intentional second click — case-text clarification #2393, not a defect; literal case intent still proven)* |
| Step 6: Main-panel header shows bucket name | Header correct | Test Step 6 | `artifacts-breadcrumb-bucket-label` text | asserted |
| Step 7: No file table shown | Table absent | Test Step 7 | `artifacts-file-row` count == 0 | asserted |
| Step 8: Main-panel empty state (icon + message + Upload button) | All 3 shown | Test Step 8 | message + button testids; icon via screenshot | asserted *(icon: visual check, no accessible handle exists — see note)* |
| Step 9: Top-right search + upload/download/delete icons present | All present | Test Step 9 | **inverted** — asserts all 4 ABSENT | clarification *(case text wrong for an empty bucket — #2394; design intentionally hides these controls)* |
| Step 10: Left-panel footer "Buckets: N Size: X MB" | Correct counts | Test Step 10 | footer text, regex-parsed | asserted *(live format "Buckets:N Size:X" with real units, not literal "MB")* |
| Step 11: Hover bucket name → tooltip w/ retention + file count | Tooltip shown | Test Step 11 | hover on main-panel info icon, not left-panel name | asserted *(location corrected per pre-existing #1617, re-confirmed live this run — not the literal element the case names)* |
| Expected Final State (composite) | All of the above together | Test Steps 1-11 | combination | asserted |
| Pass criterion: "all steps complete without errors" | No unexpected errors | All steps | console-error check (0 errors observed) | asserted |

### Axis 2 — Observables asserted beyond the case
- **`data-selected` attribute read instead of a visual/CSS-class highlight
  guess** for Step 5's "highlighted" claim — *added: attribute-based state
  check per the ladder's state-as-attribute rule, more robust than inferring
  highlight from computed background color.*
- **Console-error check across the whole flow** — *added: standard silent-error
  guard, consistent with sibling artifacts cases' precedent; 0 errors observed
  this run.*
- **DOM-level absence assertions for all 4 toolbar-action testids** (Step 9) —
  *added: stronger and more specific than "icons present/absent" prose; ties the
  assertion directly to `ArtifactTableToolbar.jsx`'s `isEmptyFiles` gate.*

## Cleanup
1. Delete the test bucket via `ArtifactAPI.delete_bucket(name)` in the test's
   own teardown. **Known pre-existing defect, already filed
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)):**
   this delete call 404s on this DEV environment, so the bucket will likely
   leak — not new to this case, out of scope to fix here.
2. **This exploration run's artifact**: bucket `elitea1805-empty` was created
   via the live UI flow in the `Private` project and left in place (project had
   0 buckets at session start, 1 at hand-off) — safe for the implementer or
   lead to delete at any time via `ArtifactAPI.delete_bucket("elitea1805-empty")`.
3. Local exploration screenshots (`test-results/screenshots/`, gitignored —
   untracked per this repo's existing pattern of untracked case-evidence
   screenshots): `ELITEA-1805-step01-landing.png`,
   `ELITEA-1805-step04-bucket-selected.png`,
   `ELITEA-1805-step08-main-empty-state.png`,
   `ELITEA-1805-step05-recheck.png`.

## Concrete Handles (discovered during exploration)

**Locator policy (current, 2026-10 ladder):** `.agents/testing.md` §
Locator policy / `.agents/role-overrides.md`. Existing testid on DEV →
`role=`+`name=` → `label=` → stable `css=` → declared `xpath=`, every
non-testid declaration carrying `suggested_testid=`. All rows below were
exercised live against `https://dev.elitea.ai`.

| Rung | Element | Handle | Provenance | Notes |
|---|---|---|---|---|
| 1 (testid) | Buckets heading | `artifacts-buckets-heading` | **testid on DEV ✓** | existing `buckets_heading` field |
| 1 (testid) | Create-bucket ("folder") button | `artifacts-create-bucket-button` | **testid on DEV ✓** | existing `create_bucket_button` field |
| 1 (testid) | Search-buckets button | `artifacts-search-buckets-button` | **testid on DEV ✓** | existing `search_buckets_button` field; `aria-label="Search buckets"` readable without triggering the hover popper |
| 1 (testid, dynamic) | Bucket row | `[data-testid="artifacts-bucket-row-{}"]` | **testid on DEV ✓** | existing `BUCKET_ROW` template constant |
| 1 (sub-attribute of above) | Bucket row selected state | `.get_attribute("data-selected")` on the bucket-row element | **testid on DEV ✓** | `data-selected="true"/"false"`, confirmed live — state as attribute, not a class/positional guess |
| 4 (css, stable attribute) | Storage-provider selector (name + dropdown chevron) | `[data-tour="artifacts-storage-selector"]` | **ladder — no `data-testid` on DEV, but a stable, intentional `data-tour` attribute already renders** | confirmed live via DOM dump; `BucketStorageSelector.jsx`'s root `Box` already carries `data-tour={ARTIFACT_TOUR_TARGET_IDS.storageSelector}` for the interactive-tours feature — a non-generated, non-positional, already-unique attribute, used here as the css rung. `suggested_testid="artifacts-storage-selector"` for the eventual real `data-testid`. |
| — (decorative, no handle) | Dropdown chevron SVG inside the storage selector | n/a | n/a | no role/label/stable attribute of its own; purely decorative (`ArrowDownIcon`, confirmed live via DOM dump); case step 3 only asks to verify its visual presence, satisfied via screenshot — no handle manufactured for an element no step interacts with |
| 4 (css, stable attribute) | Left-panel "No files in this bucket" tree sub-label | `[data-testid="artifacts-bucket-row-{}"] + div` (CSS adjacent-sibling, template per bucket name — same dynamic-template convention as `BUCKET_ROW`) | **ladder — no `data-testid` on this element itself; scoped via the stable, unique testid of its ADJACENT sibling (the bucket row)** | `BucketContent.jsx`'s zero-files branch renders a plain `<Typography data-selected={undefined}>No files in this bucket</Typography>` with **no testid of its own** — confirmed live via full outerHTML dump; it is the bucket row's DOM-structural next sibling (both direct children of the same wrapper `Box`), confirmed unique (exactly 1 match project-wide with 1 bucket present). Disambiguation is required: the IDENTICAL text ALSO renders in the main panel (`artifacts-empty-state`) simultaneously — a bare `get_by_text()` would match both. `suggested_testid="artifacts-bucket-tree-empty-state"` on the `Typography` in `BucketContent.jsx`'s zero-files branch (would let the implementer drop the sibling-combinator once added). **Only resolves after an intentional second click on an already-active bucket row** — see Test Step 5 / issue #2393. |
| 1 (testid) | Main-panel breadcrumb bucket-name label | `artifacts-breadcrumb-bucket-label` | **testid on DEV ✓** | existing `breadcrumb_bucket_label` field |
| 2 (role+name) | Bucket-info tooltip trigger (retention/file-count) | `get_by_label("Bucket info")` (ARIA `aria-label="Bucket info"` on the `IconButton`) | **ladder — no `data-testid` on DEV; stable ARIA label used instead** | `BucketInfoTooltip.jsx`'s `IconButton` — confirmed live, unique on the page (exactly 1 match). `suggested_testid="artifacts-bucket-info-button"`. |
| 2 (role, standard ARIA) | Bucket-info tooltip content | `page.locator('[role="tooltip"]')`, read after hovering the handle above | **ARIA role, standard pattern** | confirmed live content `"Retention Policy:1 YearNumber of files:0"` (two stacked rows, label+value, concatenated in `.text_content()`) |
| 1 (testid) | Main-panel empty-state message | `artifacts-empty-state` | **testid on DEV ✓** | existing `empty_state_label` field |
| — (decorative, no handle) | Empty-state icon | n/a | n/a | `UnavailableIcon` (`ArtifactTableNoFiles.jsx`), no role/label/stable attribute; verified visually via screenshot only — no step interacts with it |
| 1 (testid) | Main-panel "Upload files" button (center, empty state) | `artifacts-upload-files-empty-state-button` | **testid on DEV ✓** | existing `upload_files_empty_state_button` field — a DIFFERENT element from the toolbar's own upload button |
| 1 (testid) | File row (absence check) | `artifacts-file-row` | **testid on DEV ✓** | existing `ARTIFACT_FILE_ROW` constant; `.count() == 0` |
| 1 (testid, absence check) | Toolbar search input | `artifacts-file-search-input` | **testid on DEV ✓** | existing `file_search_input` field; `.count() == 0` when bucket is empty (confirmed live, by design — #2394) |
| 1 (testid, absence check) | Toolbar upload button | `artifacts-upload-files-button` | **testid on DEV ✓** | existing `upload_files_button` field; `.count() == 0` when empty |
| 1 (testid, absence check) | Toolbar download button | `artifacts-download-files-button` | **testid on DEV ✓** | existing `download_files_button` field; `.count() == 0` when empty |
| 1 (testid, absence check) | Toolbar delete button | `artifacts-delete-files-button` | **testid on DEV ✓** | existing `delete_files_button` field; `.count() == 0` when empty |
| 5 (xpath, declared last resort) | Left-panel footer (Buckets/Size) | `xpath=//span[text()="Buckets:"]/parent::div/parent::div` (full footer container text, then regex-parse `Buckets:(\d+)` / `Size:(.+)$`) | **ladder — no `data-testid`, no ARIA role, no label; only MUI-generated classes (`css-*`) on this element — rungs 1-4 all fail, hence xpath** | `BucketFooter.jsx`, confirmed live full text `"Buckets:1Size:0 B"`. `suggested_testid="artifacts-bucket-footer"` on the footer's root `Box`, which would collapse this to a rung-1 `css=` or direct testid read. |

## Network Behavior
- Bucket creation (Test Step 0): `POST .../artifacts/buckets/...` → `200 OK`
  (confirmed live, mirrors ELITEA-1808/1809's documented contract).
- The empty-bucket landing page itself issues no additional write requests —
  purely a read/render case. The bucket's own file-list fetch
  (`useAllArtifacts`) returns an empty `contents` array, driving both the
  main-panel (`isEmptyFiles`) and left-panel (`BucketContent`'s zero-files
  branch) empty states from the same data.

## Known Defects Found During Exploration
**None found as product bugs.** Two case-text/product-behavior divergences
were confirmed live and filed as CLARIFICATIONS (not defects — both are
consistent, by-design product behavior that the case text simply describes
incorrectly):
- [`EliteaAI/elitea-testing-public#2393`](https://github.com/EliteaAI/elitea-testing-public/issues/2393) —
  first-ever bucket selection doesn't auto-expand the left-panel tree; sibling
  of the already-documented `#651` toggle mechanism.
- [`EliteaAI/elitea-testing-public#2394`](https://github.com/EliteaAI/elitea-testing-public/issues/2394) —
  main-panel toolbar actions are intentionally absent (not merely disabled) for
  an empty bucket.
- [`EliteaAI/elitea-testing-public#1617`](https://github.com/EliteaAI/elitea-testing-public/issues/1617) —
  pre-existing, re-confirmed live this run, reused per dispatch instructions
  (step 11's tooltip location).

No console errors observed during the full flow (bucket creation → selection →
toggle-expand → hover checks).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Page object: extend `automation/pages/artifacts_page.py` — most handles
  already exist as class fields; add the two `suggested_testid`-hinted
  declarations (storage selector css rung, bucket-info-button role rung) plus
  the dynamic sibling-combinator template and the footer xpath, following the
  existing `BUCKET_ROW`/`ARTIFACT_FILE_ROW` UPPER_CASE-constant pattern for the
  two dynamic/structural ones (sibling template, footer xpath) since those are
  raw string templates `.format()`-filled at call sites, not single-page-fixed
  `LocatorDescriptor` fields.
- Step 5's toggle sequence is NOT a retry-until-pass loop — it's a single,
  deliberate second click, asserted as a known two-step sequence (see AFS
  note + issue #2393), not a flaky-test workaround.
- Step 9 asserts absence (`.count() == 0`), not presence — mirror the sibling
  "visible" checks used for a populated bucket elsewhere in the suite, inverted.
- Fixture: no existing fixture creates a bucket and leaves it deliberately
  empty — this case needs its own setup (see § Test Data), not the shared
  `artifact_bucket` fixture (which some tests use with files already uploaded).
