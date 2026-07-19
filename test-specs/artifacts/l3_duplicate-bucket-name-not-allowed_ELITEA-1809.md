# Test Case: Duplicate Bucket Name Is Not Allowed

## Metadata
- **TMS ID**: ELITEA-1809
- **Linked Story**: [EliteaAI/elitea-testing-public#227](https://github.com/EliteaAI/elitea-testing-public/issues/227) (tracking issue)
- **Priority**: l3 (medium — as authored in the source TMS case frontmatter,
  `priority: medium`). **Filename deviation note:** the dispatch prompt requested
  `l2_duplicate-bucket-name-not-allowed_ELITEA-1809.md`, but the source case file
  (`ELITEA-1809_duplicate-bucket-name-is-not-allowed.md`) declares `priority: medium`
  in its own frontmatter and body (`**Priority:** medium`), which maps to `l3` per
  `spec-format.md`'s mechanical digit table (`1`=critical, `2`=high, `3`=medium,
  `4`=low). Named the file `l3_...` to match the case's own authoritative priority
  rather than silently complying with a path that contradicts it — flagging this
  explicitly per the declared-improvisation protocol rather than picking one
  silently. Orchestrator: adjust downstream bookkeeping if `l2` was intentional for
  a reason outside the TMS case's own metadata.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399,
  confirmed synced to `origin/main` via `git fetch origin` immediately before and
  during this run — see § Concrete Handles for the exact provenance per testid).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live (all 18 case
  steps observed and pass). No product defect found: the duplicate-name rejection,
  red error notification, form-stays-open behavior, and zero-duplicate-created
  guarantee are all confirmed exactly as specified. Two genuine testid gaps found
  (the bucket-search input and its clear/X button have NO `data-testid` on either
  `origin/main` or `origin/automation/testids` — confirmed via fresh `git fetch
  origin` + `git grep` on both refs) — specced as `testid needed:` work orders per
  the analyst-slot rule (`.agents/role-overrides.md`), **not** self-fixed by this
  analyst pass (unlike ELITEA-1808's precedent, which predates that rule's current
  phrasing — this run follows the currently-authoritative role-overrides.md, which
  explicitly assigns testid-gap fixes to the **implementer** slot, not the analyst).
  Not `already-covered` / not `extend-existing` — see § Overlap check below.

## Overlap check vs existing automation

`automation/pages/artifacts_page.py` (read in full, 1165 lines) and
`automation/tests/ui/artifacts/test_artifacts_create_bucket_upload_file.py`
(ELITEA-1808, the only existing test that drives the "New Bucket" form) were both
read before this run. ELITEA-1808 automates the **happy-path** bucket-creation flow
(unique name → 200 → bucket appears in list) and never submits a name that
collides with an existing bucket — it has no assertion on the 400/duplicate path,
no assertion on the error toast's exact text, and never touches the bucket-search
feature (`search_buckets_button` exists as a `LocatorDescriptor` but has zero
callers anywhere in `automation/tests/ui/artifacts/` — confirmed via grep). No
other existing artifact test (`test_artifacts_multi_file.py`,
`test_artifacts_upload_duplicate_cancel.py`,
`test_artifacts_download_single_file_dropdown.py`,
`test_artifacts_download_multiple_files_zip.py`,
`test_artifacts_upload_multiple_files.py`) touches bucket creation or bucket search
at all — they all obtain their bucket via the API-only `artifact_bucket` fixture.

Verdict: **zero behavioral overlap** — the duplicate-name validation path, the
exact error-message assertion, and the bucket-search feature are all fresh
scenarios. `ready-for-automation`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- **A bucket with the test's target name already exists.** The case's "bucket-1"
  is a **case-text placeholder**, not a literal name to hardcode — same
  established convention as ELITEA-1808/1832/1839 (confirmed again live this run:
  no bucket named exactly `bucket-1` exists among this project's 175 current
  `Private`-project buckets, snapshot taken at run start). This precondition is
  **created by the test itself** in setup (see § Test Data) — it is a real,
  necessary state mutation (Hard Rule 10: the case's own subject is "does the
  system reject a name that collides with something real", so a real collision
  target must exist), not an incidental one. The **duplicate-creation attempt
  itself** (the case's actual subject, steps 8-14) creates nothing — confirmed
  live via the left-panel bucket-count footer reading `"175"` both immediately
  before and immediately after the failed Save click, and via a DOM-level
  uniqueness check (see Test Step 17-18).

## Test Data

### reuse-existing
- None. No bucket named `bucket-1` (or matching the generated precondition name)
  pre-exists; nothing here is safely reusable across runs since the precondition
  bucket's name must be deterministically known to both the setup step and the
  duplicate-attempt step within the same test.

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Precondition bucket name**: must contain the literal substring **`buck`**
  (the case's own "Search keyword" test-data value, used in Test Steps 2-7 and
  15-18) — this project's generic `_generate_bucket_name(node_name)` helper
  (ELITEA-1808's naming scheme, `automation/fixtures/data_fixtures.py:455`'s
  pattern) does **not** guarantee a `buck` substring depending on the test's own
  node name, so do **not** reuse it verbatim for this case. Use a
  case-specific generator instead, e.g.:
  ```python
  def _generate_duplicate_test_bucket_name() -> str:
      ts = str(int(time.time() * 1000))[-6:]
      return f"autotest-buck1-{ts}"
  ```
  Validated live against `CreateBucket.jsx`'s yup schema
  (`^[a-zA-Z][a-zA-Z0-9-]*$`, max 56 chars) — `autotest-buck1-800755` (this run's
  actual generated name) passed validation and was accepted by the create-bucket
  POST with `200 OK`.
- **Retention policy**: leave at the form's default (`"years"` / `1`) for BOTH the
  precondition-creation call and the duplicate-attempt call — the case never
  varies this field. Confirmed live: `CreateBucket.jsx`'s formik defaults
  (`RETENTION_MEASURES[3]` = `"years"`, `DEFAULT_RETENTION_VALUE` = `1`).
- No file upload is involved in this case (`test.txt` etc. — N/A).

### generate-shared-with-cleanup
- None.

## Test Steps

**Step 0 (precondition setup, not a numbered case step) — Create the precondition
bucket via the "New Bucket" form.**
- Navigate to `${BASE_URL}/artifacts`, click `artifacts-create-bucket-button`,
  fill `artifacts-bucket-name-input` with the generated name (select-all + type —
  MUI field, confirmed live this run `press('ControlOrMeta+a')` +
  `press_sequentially()`/`type()` correctly replaces the pre-filled
  `"new-bucket"` default with no mangled-prepend artifact, unlike ELITEA-1808's
  documented `Control+a` caveat — re-verify live if this regresses), leave
  retention at default, click `artifacts-bucket-save-button`.
  - **Verify**: `POST ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}`
    → `200 OK` (confirmed live:
    `POST http://localhost:5173/api/v2/artifacts/buckets/default/399` → 200).
  - **Verify**: `[data-testid="artifacts-bucket-row-{generated_name}"]` becomes
    visible (condition-based wait, reusing the existing
    `wait_for_bucket_in_list()` method from ELITEA-1808 — same timing caveat
    applies: do not assert immediately after the Save click).
  - This is a genuine mutation the observable requires, per Hard Rule 10 — it is
    **not** part of the pass/fail assertions of the case itself, only the
    mechanism that makes the duplicate-attempt meaningful.

1. Navigate to `${BASE_URL}/artifacts` (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible (existing testid,
     `ArtifactsPage.wait_for_page_load()` already does this).
2. Click `artifacts-search-buckets-button` (case step 2).
   - **Verify**: search input becomes visible (placeholder `"Search
     buckets..."`, confirmed live via `BucketsPanel.jsx`/`SimpleSearchBar.jsx`).
3. Verify the tooltip text (case step 3).
   - **Verify**: `artifacts-search-buckets-button.get_attribute("aria-label")
     == "Search buckets"` — confirmed live this is how MUI's `<Tooltip
     title="Search buckets">` (`BucketSearch.jsx:22-25`) surfaces its title:
     as a static `aria-label` on the trigger element itself, readable via the
     EXISTING testid without needing to trigger the hover-only floating
     `role="tooltip"` popper (confirmed live: `page.locator('[role="tooltip"]')`
     stays at count 0 even after a real `.hover()` + 500ms wait — the
     `aria-label` is the reliable, testid-anchored signal, not the popper).
     This keeps the assertion testid-only-compliant (reads an attribute of an
     already-testid-resolved element; does not locate anything by role/label).
4. Type `"buck"` into the bucket-search input (case step 4).
   - **Verify**: input reflects `"buck"`. Requires
     `testid needed: artifacts-bucket-search-input` (see § Concrete Handles —
     genuine gap, confirmed absent on both `origin/main` and
     `origin/automation/testids`).
5. Verify the bucket list filters to only `buck`-containing names (case step 5).
   - **Verify**: client-side filter is debounced 300ms
     (`BucketsPanel.jsx:47`'s `useDebounceValue(searchQuery, 300)`) — wait for
     that condition, not a fixed value; confirmed live the filtered list drops
     from 175 buckets to a small subset (this run: `autotest-buck1-800755`,
     `autotest-bucket-api-discovery`, `probe-bucket-body`,
     `probe-bucket-body-2`, and 24 `autotest-test-create-bucket-via-form-and-*`
     leftover buckets from ELITEA-1808 runs — all contain "buck" as a substring
     of "bucket").
6. Verify the precondition bucket is present in the filtered results (case step
   6, "bucket-1" placeholder → generated name).
   - **Verify**: `[data-testid="artifacts-bucket-row-{generated_name}"]` visible
     (existing dynamic testid, `BUCKET_ROW` template already in
     `artifacts_page.py`).
7. Clear the search field and close the search box (case step 7).
   - **Verify**: full 175-bucket list is restored (confirmed live: clicking the
     clear/X button next to the search input clears `searchQuery` AND sets
     `isSearchActive` to `false` in one action —
     `BucketsPanel.jsx`'s `handleSearchClear`). Requires
     `testid needed: artifacts-bucket-search-clear-button` (see § Concrete
     Handles).
8. Click `artifacts-create-bucket-button` (case step 8).
   - **Verify**: URL becomes `${BASE_URL}/artifacts/create-bucket` (full page
     navigation, matches ELITEA-1808's confirmed behavior).
9. Verify the "New Bucket" form is visible (case step 9).
   - **Verify**: `artifacts-bucket-name-input` visible, pre-filled with
     `"new-bucket"`; `artifacts-bucket-retention-measure-select-combobox` text
     `"Years"`; `artifacts-bucket-retention-value-input` value `"1"`;
     `artifacts-bucket-save-button` visible (same 4 checks as ELITEA-1808's Test
     Step 3, reused verbatim).
10. Enter the SAME name as the precondition bucket into
    `artifacts-bucket-name-input` (case step 10; select-all via
    `press('ControlOrMeta+a')` + `type()`/`press_sequentially()` — confirmed
    live this exact sequence replaces the field cleanly, no mangled-prepend).
    - **Verify**: field displays the generated name exactly (identical string
      to the precondition bucket from Step 0).
11. Leave Retention policy as default (case step 11).
    - **Verify**: still `"Years"` / `"1"` (unchanged).
12. Click `artifacts-bucket-save-button` (case step 12).
    - **Verify**: `POST ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}`
      → `400 Bad Request` with JSON body
      `{"message": "Bucket with name {generated_name} already exists"}`
      (confirmed live via full response-body capture, § Network Behavior).
13. Verify the red error notification (case step 13).
    - **Verify**: `toast-message` (existing generic app-wide testid, already a
      `LocatorDescriptor` on `ArtifactsPage` — reused, not a new handle) becomes
      visible with text exactly `f"Bucket with name {generated_name} already
      exists"` — confirmed live byte-for-byte via the POST's response body
      (`buildErrorMessage()` in `src/common/utils.jsx:158-159` passes
      `err.data.message` straight through to `toastError()`, which is the SAME
      `Toast`/`MuiAlert` component ELITEA-1826/1832 already documented for the
      SUCCESS path — `severity="error"` renders the MUI `filled` red variant,
      confirmed visually in the evidence screenshot). Auto-dismisses after
      `TOAST_DURATION` = 3000ms by default (or an env-configured
      `ERROR_TOAST_DURATION` override, `useErrorToastDuration()`) — use a
      condition-based wait for the visible state, never a fixed sleep, and
      don't assert its continued presence past ~3s.
14. Verify the "New Bucket" form remains open (case step 14).
    - **Verify**: `self.page.url` still contains `/artifacts/create-bucket`
      (confirmed live: the failed Save does NOT navigate away — `CreateBucket.jsx`
      only calls `navigate(-1)` inside the `if (!error)` branch of `onSubmit`,
      so a 400 leaves the form mounted); `artifacts-bucket-name-input`,
      `artifacts-bucket-save-button` still visible with the (unchanged, still
      duplicate) name still in the field.
15. Click "Artifacts" in the left sidebar (case step 15).
    - **Verify**: URL becomes `${BASE_URL}/artifacts` (bucket query param
      cleared).
16. Click `artifacts-search-buckets-button` again and type `"buck"` (case step
    16). Same handles/verification as Steps 2-5.
17. Verify the filtered list contains no duplicate of the precondition bucket
    (case step 17).
    - **Verify (primary, testid-only, robust regardless of search-input testid
      availability)**: `page.locator('[data-testid="artifacts-bucket-row-{}"]'
      .format(generated_name)).count() == 1` — a real duplicate bucket, if one
      had been created, would render a SECOND DOM element sharing the identical
      dynamic testid string (same mechanism ELITEA-1808 used to catch the
      pre-fix non-unique dot-menu testid) — this is a stronger, DOM-level proof
      than eyeballing the search-filtered list.
    - **Verify (secondary, case-mandated)**: exactly one row matching the
      generated name is visible within the `"buck"`-filtered list (fulfills the
      case's own literal wording; requires the two new search testids from
      Steps 4/7).
18. Verify only one instance is present (case step 18 — same observable as 17,
    case's own text splits verify-filtered vs. verify-count into two steps;
    folded here since both testid-based checks above satisfy it).
    - **Verify (composite signal)**: left-panel bucket-count footer text
      (`"Buckets: 175"`) is IDENTICAL before Step 0's precondition creation... 
      wait — footer increments by 1 after Step 0 (174→175, confirmed live) and
      then stays at `"175"` unchanged across the entire duplicate-attempt flow
      (Steps 8-14) — confirmed live via two separate snapshots (immediately
      before Step 8's click and immediately after Step 17's search). This
      footer text has **no testid** (`BucketFooter.jsx` confirmed via source
      read) — **not** requesting one, since no case step requires reading it
      directly (informational-only signal in this AFS, captured via a
      DOM-text read anchored off the already-testid'd `artifacts-buckets-heading`
      panel container, not a bare CSS locator on an untested element).

## Expected Results
- The bucket-search feature (icon → input with `"Search buckets"` tooltip → live
  300ms-debounced client-side filter → clear/close) works identically whether
  used before or after the duplicate-creation attempt.
- Attempting to create a bucket with a name that collides with an existing one:
  fails the POST with `400` and a server-generated
  `{"message": "Bucket with name {name} already exists"}` body; surfaces that
  exact message in the app-wide red `toast-message` component; leaves the "New
  Bucket" form open at `/artifacts/create-bucket` (no navigation); creates
  **zero** new buckets (DOM-level `artifacts-bucket-row-{name}` count stays at 1;
  bucket-count footer stays unchanged).
- No console errors during the flow **except** the browser's own automatic
  "Failed to load resource: 400" network log for the intentionally-triggered
  400 response — this is expected for any negative-path exercise and is not an
  application-level error (see § Known Defects Found).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture (skips login on localhost) | asserted |
| Precondition: bucket "bucket-1" already exists | Collision target exists | Preconditions + Test Step 0 | generated-name bucket created via UI form, `artifacts-bucket-row-{name}` visible | asserted *(generated unique name containing "buck", not literal "bucket-1" — see § Test Data, same established convention as ELITEA-1808/1832/1839)* |
| Test Data: Existing bucket name = bucket-1 | Placeholder for the collision name | Test Step 0, 10 | generated name reused identically in both calls | asserted *(placeholder, not literal)* |
| Test Data: Search keyword = buck | Filters bucket list | Test Steps 4, 16 | debounced client-side filter | asserted |
| Test Data: Error message = "Bucket with name bucket-1 already exists" | Exact error text (with generated name substituted) | Test Step 13 | `toast-message` text == server response `message` field, captured via full response-body read | asserted *(dynamic name substitution, wording pattern otherwise identical)* |
| Step 1: Navigate to Artifacts | Artifacts page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Click search icon | Search input opens w/ tooltip | Test Step 2 | search input becomes visible | asserted |
| Step 3: Verify tooltip "Search buckets" | Tooltip text correct | Test Step 3 | `aria-label` attribute of `artifacts-search-buckets-button` == "Search buckets" | asserted |
| Step 4: Enter "buck" | List filters | Test Step 4 | search input value == "buck" | asserted *(requires `testid needed: artifacts-bucket-search-input`)* |
| Step 5: Verify list filters to "buck"-matches | Only matching buckets shown | Test Step 5 | filtered DOM list, debounce-aware wait | asserted |
| Step 6: Verify "bucket-1" present in filtered results | Precondition bucket listed | Test Step 6 | `artifacts-bucket-row-{name}` visible in filtered state | asserted |
| Step 7: Clear search, close search box | Full list restored | Test Step 7 | full 175-bucket list re-visible | asserted *(requires `testid needed: artifacts-bucket-search-clear-button`)* |
| Step 8: Click create-bucket icon | "New Bucket" form opens | Test Step 8 | URL becomes `/artifacts/create-bucket` | asserted |
| Step 9: Verify "New Bucket" form opens | Form visible | Test Step 9 | 4 testid visibility/value checks | asserted |
| Step 10: Enter bucket name "bucket-1" (duplicate) | Name field shows it | Test Step 10 | `artifacts-bucket-name-input` value check | asserted *(generated name, not literal — same placeholder convention)* |
| Step 11: Leave Retention as default | Unchanged | Test Step 11 | value checks unchanged | asserted |
| Step 12: Click Save | Save attempted | Test Step 12 | `POST .../buckets/...` → 400 | asserted |
| Step 13: Verify red error notification with exact message | Error shown | Test Step 13 | `toast-message` visible + exact text match | asserted |
| Step 14: Verify "New Bucket" form remains open | Form still visible, no nav | Test Step 14 | URL unchanged + fields still visible | asserted |
| Step 15: Click "Artifacts" | Navigate to Artifacts root | Test Step 15 | URL becomes `/artifacts` | asserted |
| Step 16: Click search icon, enter "buck" | Filters list | Test Step 16 | same as Steps 2-5 | asserted |
| Step 17: Verify no duplicate "bucket-1" in filtered list | Only one entry | Test Step 17 | `artifacts-bucket-row-{name}` DOM count == 1 (primary) + filtered-list single-match (secondary) | asserted |
| Step 18: Verify only one "bucket-1" present | No duplicate created | Test Step 18 | composite: DOM count == 1 + unchanged bucket-count footer text | asserted |
| Expected Final State: only one "bucket-1" exists, error shown, form open | Composite pass condition | Test Steps 13, 14, 17, 18 | combination of the above | asserted |
| Pass criterion: "All steps complete without errors" | No unexpected errors during flow | All steps | console-error check (only the expected 400 resource-load log observed) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Exact 400 response body captured and asserted** (`{"message": "Bucket with
  name {name} already exists"}`) rather than only reading the rendered toast text
  — *added: stronger signal that ties the UI-visible message directly to the
  server contract, and documents `buildErrorMessage()`'s pass-through behavior
  for future cases that hit other `err.data.message`/`err.data.error` shapes.*
- **DOM-level duplicate-count check** (`artifacts-bucket-row-{name}` locator
  `.count() == 1`) as the PRIMARY no-duplicate proof, independent of the
  search-filter UI — *added: more robust than eyeballing a filtered list, and
  doesn't depend on the two testid gaps this AFS flags; if the search-input
  testid work is deferred, this check alone still fully proves the case's core
  claim.*
- **Bucket-count footer read (informational, no new testid)** confirming the
  total stayed unchanged across the failed attempt — *added: a second
  independent signal (aggregate count vs. per-row DOM presence) that the failed
  POST truly created nothing server-side, not just that the UI didn't render a
  visible duplicate.*
- **Console-error check across the full flow, with the expected 400
  resource-load log explicitly documented as non-failing** — *added: standard
  silent-error guard (consistent with sibling cases' precedent), but explicitly
  scoped so the implementer doesn't chase the browser's own automatic network log
  as a false regression.*

## Cleanup
1. Delete the precondition bucket via `ArtifactAPI.delete_bucket(generated_name)`
   in the test's own teardown. **Known pre-existing defect, already filed
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)):** this
   delete call 404s on both URL-format attempts in the current dev environment,
   so the bucket will likely leak — do not treat "the delete call ran" as proof
   the bucket is gone; not new to this case, out of scope to fix here.
2. **The duplicate-creation attempt itself creates nothing to clean up** — this
   is the exact behavior the case proves; there is no second bucket, no orphaned
   resource, no partial state from the 400 response.
3. **This exploration run's artifacts** (not part of the automated test): bucket
   `autotest-buck1-800755` was created via the live UI flow in the `Private`
   project (id 399) to verify the case, and left in place — matches this
   project's existing convention of un-deleted `autotest-*` buckets already
   present in `Private` from prior runs (175 total at hand-off, up from 174 at
   session start); safe for the implementer or lead to delete at any time via
   `ArtifactAPI.delete_bucket("autotest-buck1-800755")`.
4. Local exploration screenshots (repo root, untracked):
   `ELITEA-1809-step13-duplicate-error-notification.png`,
   `ELITEA-1809-step17-18-search-buck-no-duplicate.png` — attached as evidence
   for this AFS; safe to leave per this repo's existing pattern of untracked
   case-evidence screenshots at repo root.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's
locator policy (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`) is **testid-only, no fallback ladder** —
`LocatorDescriptor(testid=...)` with no `fallback=`/`locator=`. Per the
currently-authoritative Analyst-slot rule in `role-overrides.md`, the two
genuine gaps below are specced as `testid needed:` work orders for the
**implementer** to add via `add-data-testid` — **not** self-fixed by this
analyst pass.

**Provenance verified freshly this run**: `cd ../EliteaUI && git fetch origin`
run immediately before checking (output: already up to date, branch
`automation/testids` tracking `origin/automation/testids` cleanly), then
`git grep` run against both `origin/main` and `origin/automation/testids` for
every testid below.

| Element | testid | Status | Provenance | Notes |
|---|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | existing | **on-main ✓** | left panel |
| "+ Artifact Bucket" button | `artifacts-create-bucket-button` | existing | **on-main ✓** | opens `/artifacts/create-bucket` |
| Search buckets button | `artifacts-search-buckets-button` | existing | **on-main ✓** | `aria-label` == "Search buckets" (MUI Tooltip's static accessible-name wiring — read this attribute for Test Step 3, do not need to trigger the hover popper) |
| **Bucket search input** | `artifacts-bucket-search-input` | **added** (implementer pass) | **on-automation/testids only** (EliteaAI/EliteaUI@3d2edf53, awaiting human promotion to main) | Re-confirmed absent via fresh `git fetch origin` + `git grep` on both `origin/main` and `origin/automation/testids` immediately before this implementer pass (both empty, matching the analyst's own finding); added as a one-line `data-testid` prop on the `<SimpleSearchBar>` call site in `BucketsPanel.jsx:126-131`; live-rendering confirmed via HMR before commit |
| **Bucket search clear/X button** | `artifacts-bucket-search-clear-button` | **added** (implementer pass) | **on-automation/testids only** (EliteaAI/EliteaUI@3d2edf53, awaiting human promotion to main) | Same fresh re-verification as above; added directly on the `<IconButton onClick={handleSearchClear}>` in `BucketsPanel.jsx:132-138`; live-rendering confirmed via HMR before commit |
| New Bucket form — Name input | `artifacts-bucket-name-input` | existing (ELITEA-1808) | **on-automation/testids only** (awaiting human promotion to main) | `CreateBucket.jsx`, in `inputProps` on the `<TextField id="name">` |
| New Bucket form — Retention measure select | `artifacts-bucket-retention-measure-select-combobox` | existing (ELITEA-1808) | **on-automation/testids only** | the `-combobox` suffix is auto-derived by the shared `SingleSelect` component; use this suffixed one to read/interact, not the root testid |
| New Bucket form — Retention value input | `artifacts-bucket-retention-value-input` | existing (ELITEA-1808) | **on-automation/testids only** | `CreateBucket.jsx`, in `inputProps` |
| New Bucket form — Save button | `artifacts-bucket-save-button` | existing (ELITEA-1808) | **on-automation/testids only** | `CreateBucket.jsx` |
| New Bucket form — Cancel button | none | not touched by this case | n/a | this case never clicks it; out of scope, same as ELITEA-1808's ruling |
| Bucket row container (dynamic) | `BUCKET_ROW` template = `[data-testid="artifacts-bucket-row-{}"]` | existing (ELITEA-1808) | **on-automation/testids only** | already a class constant in `artifacts_page.py`; reused here as the PRIMARY duplicate-detection mechanism (`.count() == 1`) |
| Error/success toast (generic, app-wide) | `toast-message` | existing | **on-main ✓** | already a `LocatorDescriptor` (`success_toast_message`) on `ArtifactsPage`; reused for the error-severity case — same component, `severity="error"` renders the red `MuiAlert` filled variant |

## Network Behavior
- **Precondition bucket creation** (Test Step 0):
  `POST ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}` with body
  `{name, expiration_measure, expiration_value}` → `200 OK`. Confirmed live:
  `POST http://localhost:5173/api/v2/artifacts/buckets/default/399`.
- **Duplicate-attempt bucket creation** (Test Step 12): identical endpoint and
  identical request body shape (same name as the precondition) →
  `400 Bad Request`, response body confirmed live via full capture:
  `{"message": "Bucket with name autotest-buck1-800755 already exists"}`. This
  exact `message` field is what `buildErrorMessage()`
  (`src/common/utils.jsx:158-159`) surfaces verbatim in the `toast-message`
  component.
- No unexpected requests observed between any click and its corresponding
  network call.

## Known Defects Found During Exploration

**None found.** The case's expected behavior holds exactly as specified: red
error notification with the precise server-generated message, "New Bucket" form
stays open (no navigation away), and zero duplicate buckets created (confirmed
via both a DOM-level testid-count check and an unchanged aggregate bucket-count
footer reading). One console entry was observed during the flow and is
documented here so it is not rediscovered and mis-filed:

- `[ERROR] Failed to load resource: the server responded with a status of 400
  (Bad Request) @ http://localhost:5173/api/v2/artifacts/buckets/default/399:0`
  — this is the browser's own automatic network-layer log for ANY non-2xx
  `fetch`/XHR response; it fires unconditionally whenever the intentionally-
  triggered 400 occurs and carries no additional information beyond the status
  code already captured via the network-request assertion in Test Step 12. Not
  an application-level JS error, not a regression signal — the implementer's
  console-error check for this test should exclude/allow this specific expected
  entry (or assert on error TYPE — this is a `Failed to load resource` browser
  log, not a page-context `console.error()` call — rather than asserting zero
  console entries of any kind, which sibling cases with only happy-path network
  traffic can afford to do but this negative-path case cannot).

## Implementer Amendments (Phase 2 exploration, ELITEA-1809 implementer pass)

Three findings from live re-verification, declared per
`.agents/role-overrides.md`'s declared-improvisation protocol (technique-level,
no scope/coverage change — all three still fully assert their case element's
expected result):

1. **Step 15 ("Click 'Artifacts' in the left sidebar") has no compliant
   handle.** Live source read of `SidebarMenuItem.jsx` /
   `SidebarBody.jsx` (EliteaUI) confirms the sidebar nav entries render via a
   SHARED component with no `data-testid` on any entry — adding one would
   require threading a `testId` prop through `SidebarBody.jsx`'s render loop,
   which touches every sidebar nav item (Chat, Agents, Skills, Pipelines,
   Credentials, Toolkits, ...), not just Artifacts — a broad, high-blast-radius
   shared-component change no other part of this case touches, and out of
   proportion to a single click. Implemented instead via the existing
   `ArtifactsPage.navigate_to_artifacts()` (direct URL navigation) — the SAME
   mechanism the case's own Step 1 already uses to reach the identical
   observable (URL becomes `${BASE_URL}/artifacts`). The interaction
   *mechanism* changes; the asserted *outcome* does not.
2. **Step 13's "red" toast has no stable DOM-level severity signal.** Live
   inspection of the error-state `toast-message` element
   (`get-attribute class`) returned a Vite-hashed class (`MuiBox-root
   css-1sn4tny`) with no semantic "error"/"filled-error" token — asserting on
   it would be brittle (build-hash, not a stable contract) and adds no real
   verification strength beyond the exact-text match, which the
   duplicate-name message itself already uniquely identifies as the
   rejection path (jointly proven by the 400 status + unchanged-form
   evidence in Steps 12/14). Implemented as an exact-text assertion only, no
   color/class check.
3. **The "bucket-count footer unchanged" Axis-2 signal (originally proposed
   as a `BucketFooter.jsx` text read) is replaced with a testid-compliant
   equivalent.** `BucketFooter.jsx` has no testid, and reading its "Buckets:
   N" text would require either (a) adding a testid to an element no case
   step reads directly — against the "scope is load-bearing" testid ruling
   (`.agents/testing.md` § Locator policy) — or (b) chaining a raw CSS
   selector off an existing testid'd field, forbidden by
   `.claude/rules/page-objects.md` ("Don't chain a raw selector off an
   existing field inside a method"). Implemented instead via a new
   `ArtifactsPage.get_visible_bucket_count()` using the
   `[data-testid^="artifacts-bucket-row-"]` PREFIX-selector pattern — already
   established precedent in this codebase (`agent_detail_page.py`'s
   `SKILL_CARD_ANY_SELECTOR`, `chat_page.py`'s `MENTION_SKILL_ITEM_PREFIX`,
   `mcp_form_page.py`'s `TOOL_CHIP_PREFIX`, `pipeline_detail_page.py`'s
   `SELECT_OPTION_PREFIX`). Used three ways: (i) narrows-on-filter proof at
   Steps 4-6 (filtered count < unfiltered baseline), (ii) full-list-restored
   proof at Step 7 (count == baseline after closing search), and (iii) a
   same-baseline comparison between the Step 4-6 and Step 16-18 filtered
   counts — an equal-strength, environment-count-independent replacement for
   the originally proposed raw "175 unchanged" footer read (which was also
   fragile: the literal "175" the analyst observed live is not a fixed
   value — it drifts across runs as other tests' `autotest-*` buckets leak,
   per those tests' own documented known-defect-#636 cleanup caveats).

4. **`close_bucket_search()` needs the SAME 300ms debounce wait as
   `search_buckets()`, not just an input-visibility wait.** Confirmed live
   via a real test run (R1 failure): `BucketsPanel.jsx`'s `filteredBuckets`
   derives from `debouncedSearchQuery` (`useDebounceValue(searchQuery,
   300)`), which lags the underlying `searchQuery` state by the same 300ms
   window even when clearing it to `''` via the clear/X button —
   `handleSearchClear` sets `isSearchActive` to `false` (unmounting the
   search input) SYNCHRONOUSLY, but the bucket list itself doesn't
   re-render to its full, unfiltered state until the debounce elapses. A
   wait on the search input's visibility alone is therefore not a
   sufficient completion condition for "list restored" — observed live:
   asserting `get_visible_bucket_count() == baseline` immediately after the
   input disappeared caught a stale filtered count (32 rendered vs. 178
   expected). Fixed by adding the same
   `BUCKET_SEARCH_DEBOUNCE_WAIT_MS` wait after the input-hidden wait in
   `close_bucket_search()`.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`).
  Needs these new methods/locators:
  1. Two new `LocatorDescriptor`s once the implementer adds the testids:
     `bucket_search_input` (testid `artifacts-bucket-search-input`),
     `bucket_search_clear_button` (testid `artifacts-bucket-search-clear-button`).
  2. `open_bucket_search()` — click `search_buckets_button` (already exists),
     wait for `bucket_search_input` visible.
  3. `search_buckets(query: str)` — click + type into `bucket_search_input`
     (plain `type()`/`press_sequentially()` is fine here — this is a native
     MUI `InputBase`, not proven to need the select-all MUI-onChange workaround
     the "New Bucket" form's `TextField`s need); wait for the 300ms debounce
     (condition-based: wait for the bucket list DOM to stop changing, or accept
     a short explicit wait matching the documented 300ms
     `useDebounceValue` — this is one of the few places in this codebase where a
     short fixed wait is defensible, since the debounce interval itself is a
     hardcoded product constant, not a network round-trip).
  4. `close_bucket_search()` — click `bucket_search_clear_button`, wait for the
     search input to disappear / full list to restore.
  5. `attempt_duplicate_bucket_creation(name) -> Response` — same shape as the
     existing `click_bucket_save_button()` (ELITEA-1808) but this case
     EXPECTS the response status to be 400, not 200 — do not reuse
     `click_bucket_save_button()`'s implicit-success framing; either add a
     sibling method or have the test itself inspect
     `response.status == 400` after calling the existing method (the existing
     method just wraps `expect_response` and hands back the raw `Response`
     object — it does not assert status internally, so it's safe to reuse
     as-is and assert 400 at the call site).
  6. `count_bucket_rows(name) -> int` — thin wrapper around
     `self.page.locator(self.BUCKET_ROW.format(name)).count()`, the PRIMARY
     duplicate-detection mechanism for this case.
- Precondition setup and the duplicate attempt BOTH go through the "New Bucket"
  form UI (not the `artifact_bucket` API fixture) — this keeps both bucket
  creations flowing through the exact same code path the case exercises,
  and avoids any risk of the API and UI validation schemas silently diverging.
- Wait strategy: Test Step 12→13 needs a condition-based wait on `toast-message`
  becoming visible (short timeout is fine, ≤3-5s given the documented
  `TOAST_DURATION`/`ERROR_TOAST_DURATION`); do NOT wait past its auto-dismiss
  window before reading its text, and don't assert it stays visible.
- Console-error assertion for this specific test must allow the single expected
  "Failed to load resource: 400" browser log (see § Known Defects Found) — filter
  it out explicitly rather than asserting zero console entries.
