# Test Case: Create Artifact Bucket via "+ Artifact Bucket" Button (Path 1) and Upload File

## Metadata
- **TMS ID**: ELITEA-1808
- **Linked Story**: [EliteaAI/elitea-testing-public#212](https://github.com/EliteaAI/elitea-testing-public/issues/212) (tracking issue)
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399). Every JSX file cited
  below was edited directly on `automation/testids` and pushed this run — see § Concrete
  Handles for the exact commit.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end once live (all 17 case
  steps pass), plus a second confirmation pass after the testid fixes landed (re-verified
  the bucket-menu trigger, "Upload files" menu item, and tree-item testid with a REAL
  native Playwright click — see § Known Defects Found for why a second pass was needed).
  Three testid gaps blocked policy-compliant locators and were fixed live this run (not
  left as `testid needed:` work orders — see § Concrete Handles): the "New Bucket" form
  had ZERO testids anywhere; the bucket-row 3-dot menu trigger rendered a single STATIC,
  non-unique testid shared by all 125 buckets in the project; the left-panel tree file
  node had no testid at all. One CLARIFICATION filed (case-text vs. product: no visible
  timestamp column in the file table) — [#642](https://github.com/EliteaAI/elitea-testing-public/issues/642).
  Not `already-covered` / not `extend-existing` — see § Overlap check below.

## Overlap check vs existing automation

`automation/pages/artifacts_page.py` was read in full before this run (741 lines). It has
a `create_bucket_button` `LocatorDescriptor` (testid `artifacts-create-bucket-button`) but
**zero methods that click it or drive the "New Bucket" form** — no automated test anywhere
in `automation/tests/ui/artifacts/` exercises bucket *creation* via the UI. The three
existing artifact test files
(`test_artifacts_multi_file.py`/ELITEA-1327, `test_artifacts_upload_duplicate_cancel.py`/ELITEA-1832,
`test_artifacts_download_single_file_dropdown.py`/ELITEA-1839) all **create their bucket via
`ArtifactAPI.create_bucket()`** (the `artifact_bucket` fixture, API-only, no UI) and never
touch the "+ Artifact Bucket" button or the "New Bucket" form fields.

Upload-wise, ELITEA-1832 drives `upload_files_button` — the **toolbar** upload icon in the
right-panel file-list header. This case's step 8–9 use a completely different control: the
**bucket-row 3-dot menu's "Upload files" menu item** in the **left panel** (`BucketItem.jsx`,
not the toolbar). Confirmed live both trigger the identical underlying dialog/endpoint (same
`artifacts-upload-path-dialog` modal, same `PUT /artifacts/s3/{bucket}/{key}?project_id=...`),
but the **entry point** (bucket-level dot-menu vs. toolbar button, before vs. after a bucket
is opened) is new and untested.

Verdict: **zero behavioral overlap** — the bucket-creation form and the bucket-level
dot-menu upload entry point are both fresh scenarios. `ready-for-automation`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A local file named `test.txt` is available for upload — generate via pytest's `tmp_path`
  fixture at test setup (this project's established convention for upload-test files, per
  ELITEA-1832's AFS: no checked-in `automation/fixtures/files/` directory exists; do not add
  one). Content is irrelevant beyond being non-empty and stable byte-for-byte for the
  size-column assertion (this run used a 51-byte fixed string).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket name**: the case's "bucket-1" is a **case-text placeholder**, not a literal name
  to hardcode — same established convention as ELITEA-1832/ELITEA-1839 (confirmed again
  live this run: no bucket named exactly `bucket-1` exists in any of this project's ~125
  current `Private`-project buckets). Generate a fresh, unique name per test run (e.g.
  `f"autotest-{request.node.name}-{ts}"`, matching the existing `artifact_bucket` fixture's
  naming scheme at `automation/fixtures/data_fixtures.py:455`) — but **do NOT reuse that
  fixture for this case**, because unlike ELITEA-1832/1839 the bucket is not a precondition
  fixture here, it is the test's own subject: **creating the bucket via the UI form is
  Test Steps 2–7 of this case.** Generate the name in test setup, drive the UI to create it,
  then delete it via `ArtifactAPI.delete_bucket()` in teardown (see § Cleanup — same
  known-defect caveat as the other two cases: delete 404s silently, bucket leaks,
  [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)).
- **Bucket name validation** (confirmed live via `CreateBucket.jsx`'s yup schema): must
  start with a letter, letters/numbers/hyphens only (`^[a-zA-Z][a-zA-Z0-9-]*$`), max 56
  chars. The existing `artifact_bucket` fixture's naming scheme already satisfies this.
- **Retention policy default** (confirmed live + in source,
  `EliteaUI/src/common/constants.js:480-481`): `expiration_measure` defaults to
  `RETENTION_MEASURES[3]` = `"years"`, `expiration_value` defaults to
  `DEFAULT_RETENTION_VALUE` = `1` — i.e. exactly "Years, 1" as the case's test data expects.
  Full `RETENTION_MEASURES` list is `['days', 'weeks', 'months', 'years']`, useful context
  if a future case needs a non-default retention value.
- **Name field's own default value**: confirmed live — the Name input is pre-filled with
  the literal string `"new-bucket"` on a fresh (non-edit) form load
  (`CreateBucket.jsx:87`, `currentBucket?.name || 'new-bucket'`). The implementation must
  select-all + replace it (MUI form field — `click()` + `press("Control+a")` +
  `press_sequentially()`, per `.claude/rules/mui-patterns.md`; a bare `fill()` will not
  trigger the underlying `formik.handleChange`).
- **`test.txt`**: `tmp_path / "test.txt"`, small fixed content (see § Preconditions).

No `reuse-existing` fixture applies — same reasoning as the sibling cases: a bucket in a
freshly-created, single-file state isn't safe to share across parallel/serial runs, and this
case's own action (UI-driven creation) makes a pre-seeded fixture actively wrong to use.

## Test Steps

1. Navigate to `${BASE_URL}/artifacts` (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible (existing testid,
     `ArtifactsPage.wait_for_page_load()` already does this).
2. Click `artifacts-create-bucket-button` (case step 2).
   - **Verify**: URL becomes `${BASE_URL}/artifacts/create-bucket`; confirmed live this is a
     full page navigation, not a modal.
3. Verify the "New Bucket" form is visible with all required fields (case step 3):
   - `artifacts-bucket-name-input` visible, pre-filled with `"new-bucket"` (§ Test Data).
   - `artifacts-bucket-retention-measure-select-combobox` visible, text `"Years"`.
   - `artifacts-bucket-retention-value-input` visible, value `"1"`.
   - `artifacts-bucket-save-button` visible.
4. Click `artifacts-bucket-name-input`, select-all (`Control+a`), type the generated bucket
   name via `press_sequentially` (case step 4).
   - **Verify**: field displays the generated name exactly.
5. Do not touch `artifacts-bucket-retention-measure-select` / `artifacts-bucket-retention-value-input`
   (case step 5 — "leave as default").
   - **Verify**: still `"Years"` / `"1"`.
6. Click `artifacts-bucket-save-button` (case step 6).
   - **Verify**: `POST ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}` → `200 OK`
     (confirmed live, § Network Behavior); URL becomes
     `${BASE_URL}/artifacts?bucket={generated_name}` (the app auto-selects the new bucket
     via a `sessionStorage` handoff, `CreateBucket.jsx:122`).
7. Verify the generated bucket appears in the left-panel bucket list (case step 7).
   - **Verify**: `[data-testid="bucket-menu-{generated_name}-menu-button"]` becomes visible
     — **do not** assert on a raw `"Buckets: N"` counter text or take an immediate snapshot
     right after the Save click; confirmed live this run that an accessibility snapshot
     taken *immediately* after the Save-triggered navigation can catch the bucket list
     mid-fetch (shows a stale `"Buckets: 0"` / `"No buckets created yet"` state that
     self-corrects within ~1-2s once the list refetch completes) — condition-based wait
     on the bucket's own presence, not a fixed sleep, avoids this entirely.
8. Hover the generated bucket's row (`.hover()` on the row container — required: the
   dot-menu trigger has `display: none` until hovered, confirmed live via
   `BucketItem.jsx`'s `menuContainer` style, unlike the file-row dot-menu which is NOT
   hover-gated), then click `[data-testid="bucket-menu-{generated_name}-menu-button"]`
   (case step 8).
   - **Verify**: dropdown menu opens showing "Upload files", "Rename", "Pin to top",
     "Delete" (confirmed live — "Share"/"Manage access" are hidden because this run's
     project is the user's personal project, `isPersonalProject` check in
     `BucketItem.jsx:191/197`; irrelevant to this case, noted for context only).
9. Click `[data-testid="bucket-menu-upload-files-menuitem"]` (case step 9).
   - **Verify**: fires the native file-chooser modal state immediately (confirmed live via
     Playwright's `expect_file_chooser` — no loading delay, same immediacy as the toolbar
     upload button per ELITEA-1832's precedent).
10. (Folded into step 9's verify — same observable, no separate action; matches case step
    10's "file explorer is open".)
11. Select `test.txt` via the file chooser (case step 11).
12. Confirm the selection (case step 12 — in Playwright terms, `file_chooser.set_files()`
    IS the confirm; there is no separate native "Open" click to drive).
    - **Verify**: the "Upload files to ..." modal opens (see step 13).
13. Verify the "Upload files to ..." modal opens with Path pre-filled (case step 13).
    - **Verify**: `artifacts-upload-path-dialog` visible (existing testid, ELITEA-1832);
      `artifacts-upload-path-input`'s text starts with `"{generated_name}/"` — confirmed
      live, exact same mechanism/dialog as the toolbar-upload path (§ Overlap check).
14. Click `artifacts-upload-path-upload-button` (case step 14, existing testid).
    - **Verify**: `PUT ${ELITEA_URL}/artifacts/s3/{generated_name}/test.txt?project_id=${PROJECT_ID}`
      → `200 OK` (confirmed live, § Network Behavior — identical endpoint pattern to
      ELITEA-1832's toolbar-upload path).
15. Verify the upload completes successfully (case step 15).
    - **Verify (primary signal)**: `test.txt` becomes visible in the file table
      (`artifacts-file-list` / `artifacts-file-row`, existing testids) — this is the
      load-bearing assertion.
    - **Verify (secondary, fidelity caveat — same as ELITEA-1832 Test Step 12)**: the
      generic `toast-message` testid may briefly show "The bucket has been created
      successfully"-style copy (confirmed present in source,
      `CreateBucket.jsx:174-177`, for the *bucket-creation* toast; the *upload* success
      path was not independently confirmed to show a toast in this run before it would
      have auto-dismissed) — use a short polled-absence-or-presence check, never a single
      instantaneous DOM read, and never make this the sole pass condition.
16. Verify `test.txt` appears in the file table with correct type/size (case step 16 —
    **partial, see § Known Defects Found for the timestamp gap**).
    - **Verify**: row with Name = `"test.txt"`, Type = `"Text"`, Size = the exact byte
      count of the generated content (this run: `"51 B"` for a 51-byte file) —
      `get_total_file_count_from_pagination() == 1`.
    - **NOT asserted**: a "timestamp" column — confirmed live the file table has exactly
      four columns (Name/Type/Size/Actions), no visible upload/last-modified timestamp
      anywhere in this UI. This is case-text drift, not a product defect (reverse-masking
      guard) — filed as CLARIFICATION
      [#642](https://github.com/EliteaAI/elitea-testing-public/issues/642) rather than
      silently dropped or asserted against a nonexistent element. If the implementer wants
      an API-level cross-check, `GET ${ELITEA_URL}/artifacts/s3/{bucket}?project_id=...&format=json`
      returns a `lastModified` ISO-8601 field per file (same technique ELITEA-1832 used for
      its own step 15) — optional, not required by this case's live-verifiable surface.
17. Verify `test.txt` is also listed in the left-panel tree under the generated bucket
    (case step 17).
    - **Verify**: `[data-testid="artifacts-tree-item-test.txt"]` visible, nested under the
      bucket's own tree node — confirmed live the tree auto-expands to show the file
      immediately after upload (no manual expand-click needed, since the bucket is already
      the actively-selected one from step 6's auto-navigation).

## Expected Results
- The "New Bucket" form opens as a full page (not a modal) at `/artifacts/create-bucket`,
  pre-filled with `"new-bucket"` / `"Years"` / `"1"`.
- `POST /artifacts/buckets/default/{project_id}` creates the bucket; the app auto-navigates
  to and auto-selects it.
- The bucket appears in the left-panel bucket list (eventually — see the timing note in
  step 7) with a working, uniquely-testid'd 3-dot menu.
- The bucket-row dot-menu's "Upload files" item opens the identical "Upload files to ..."
  dialog the toolbar upload button uses, pre-filled with the bucket's own path.
- The uploaded `test.txt` appears in both the right-panel file table (Name/Type/Size — no
  timestamp column exists) and the left-panel tree, nested under the bucket.
- No console errors during the flow (see § Known Defects Found for one **ruled-out**
  false-positive from this run's own exploration tooling, not a product defect).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture (skips login on localhost) | asserted |
| Precondition: test.txt available for upload | File exists locally | Preconditions + Test Data | `tmp_path`-generated file | asserted |
| Step 1: Navigate to Artifacts | Artifacts page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Click "+ Artifact Bucket" | "New Bucket" form opens | Test Step 2 | URL becomes `/artifacts/create-bucket` | asserted |
| Step 3: Verify form has Name + Retention fields | Form visible with all fields | Test Step 3 | 4 testid visibility checks (name/retention-select/retention-value/save) | asserted |
| Step 4: Enter bucket name "bucket-1" | Name field shows generated name | Test Step 4 | `artifacts-bucket-name-input` value check | asserted *(generated unique name, not literal "bucket-1" — see § Test Data)* |
| Step 5: Leave retention as default | Retention remains Years/1 | Test Step 5 | value checks unchanged | asserted |
| Step 6: Click Save | Save completes | Test Step 6 | `POST .../buckets/...` → 200 | asserted |
| Step 7: Verify bucket appears in list | Bucket listed in left panel | Test Step 7 | dynamic `bucket-menu-{name}-menu-button` becomes visible | asserted |
| Step 8: Click 3-dot menu next to bucket | Dropdown menu appears | Test Step 8 | menu with 4 items visible after hover+click | asserted |
| Step 9: Select "Upload files" | File explorer opens | Test Step 9 | `expect_file_chooser` fires | asserted |
| Step 10: Verify file explorer opens | File explorer open | Test Step 9 (folded) | same observable as step 9 | asserted *(decomposed)* |
| Step 11: Select test.txt | File selected | Test Step 11 | `file_chooser.set_files([test.txt])` | asserted |
| Step 12: Click Open/OK | File confirmed, modal opens | Test Step 12 | `set_files()` call is the confirm; modal visibility asserted next step | asserted |
| Step 13: Verify "Upload files to ..." modal, Path pre-filled | Modal open, correct path | Test Step 13 | `artifacts-upload-path-dialog` + `artifacts-upload-path-input` text | asserted |
| Step 14: Click Upload | Upload completes | Test Step 14 | `PUT .../artifacts/s3/{bucket}/test.txt...` → 200 | asserted |
| Step 15: Verify upload success notification/confirmation | Success shown | Test Step 15 | file-table appearance (primary) + toast (secondary, fidelity caveat) | asserted |
| Step 16: Verify test.txt in file table w/ type, size, timestamp | Row w/ correct metadata | Test Step 16 | Name/Type/Size asserted; **timestamp column does not exist in this UI** | asserted *(partial)* / clarification *(timestamp — [#642](https://github.com/EliteaAI/elitea-testing-public/issues/642))* |
| Step 17: Verify test.txt in left-panel bucket tree | File in tree under bucket | Test Step 17 | `artifacts-tree-item-test.txt` visible, nested | asserted |
| Expected Final State: bucket created + file in both panels w/ metadata | Composite pass condition | Test Steps 7, 16, 17 | combination of the above | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | console-error check (0 errors both confirmation passes) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Bucket-creation network call verified directly** (`POST /artifacts/buckets/default/{id}`
  → 200) rather than only inferring success from UI state — *added: stronger signal than a
  DOM-only check, consistent with sibling cases' network-level verification pattern.*
- **Upload network call verified directly** (`PUT /artifacts/s3/{bucket}/test.txt` → 200) —
  *added: same rationale, and doubles as confirmation this bucket-dot-menu upload path uses
  the identical mechanism as the already-automated toolbar upload path (useful cross-case
  context, not required by this case's own text).*
- **Console-error check across the full flow** — *added: standard silent-error guard,
  consistent with the sibling cases' precedent.*
- **Ruled-out false-positive documented, not filed** (§ Known Defects Found) — *added:
  a MUI "anchorEl invalid" console warning appeared once during this run's own exploration
  tooling (a raw `element.click()` via `page.evaluate`, not a real Playwright gesture) and
  did NOT reproduce on a second, pristine pass using a real native click — recording this
  saves the implementer from re-discovering and mis-filing the same non-issue.*

## Cleanup
1. Delete the generated bucket via `ArtifactAPI.delete_bucket(bucket_name)`
   (`automation/api/client.py:1205`) in the test's own teardown. **Known pre-existing
   defect, already filed ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)):**
   this delete call 404s on both URL-format attempts in the current dev environment, so the
   bucket will likely leak — do not treat "the delete call ran" as proof the bucket is gone;
   this is not new to this case and out of scope to fix here.
2. No other entities are created by this case (no Agent, no Toolkit, no Credential).
3. **This exploration run's artifacts** (not part of the automated test): bucket
   `autotest-elitea1808-434462` was created via the live UI flow in the `Private` project
   (id 399) to verify the case, containing `test.txt` (51 B) at time of hand-off. A second,
   unrelated bucket `autotest-elitea1808-createupload-931274` was already present in the
   project at the start of this session (from an earlier, incomplete exploration attempt —
   no AFS for ELITEA-1808 existed on disk before this run, so that attempt never reached
   hand-off). Both left in place — matches this project's existing convention of ~125
   un-deleted `autotest-*` buckets already present in `Private` from prior runs; safe for
   the implementer or lead to delete at any time via
   `ArtifactAPI.delete_bucket("autotest-elitea1808-434462")` /
   `ArtifactAPI.delete_bucket("autotest-elitea1808-createupload-931274")`.
4. Local exploration screenshots (repo root, untracked):
   `ELITEA-1808-step1-artifacts-page-empty.png`,
   `ELITEA-1808-step2-3-new-bucket-form.png`,
   `ELITEA-1808-step4-5-name-filled-retention-default.png`,
   `ELITEA-1808-step8-9-bucket-dotmenu-open.png`,
   `ELITEA-1808-step12-13-upload-path-dialog.png`,
   `ELITEA-1808-step15-16-upload-complete-file-visible.png`,
   `ELITEA-1808-BUG-buckets-list-shows-zero-despite-api-data.png` (misleadingly named — see
   § Known Defects Found; this screenshot documents the RESOLVED/self-corrected timing
   state, not a real bug, kept for the record) — attached as evidence for this AFS; safe to
   leave per this repo's existing pattern of untracked case-evidence screenshots at repo
   root.
5. Local temp upload source file: `.playwright-mcp/test.txt` (untracked, harmless to leave
   or delete).

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator
policy (`.agents/testing.md` § Locator policy) is **testid-only, no fallback ladder** —
`LocatorDescriptor(testid=...)` with no `fallback=`/`locator=`. Three gaps below were
**fixed live this run** (not left as `testid needed:` work orders) via the `add-data-testid`
skill, committed and pushed straight onto `automation/testids`
(commit `0c8e0d63`, `test: [EL-0000] add data-testid for create-bucket form, bucket
dot-menu, tree item (ELITEA-1808)`), then re-verified against the live dev server with a
fresh page load before this AFS was written.

| Element | testid | Status | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | existing | left panel |
| "+ Artifact Bucket" button | `artifacts-create-bucket-button` | existing | opens `/artifacts/create-bucket` |
| **New Bucket form — Name input** | `artifacts-bucket-name-input` | **added** | `CreateBucket.jsx`, on the `<TextField id="name">`; form had ZERO testids before this run |
| **New Bucket form — Retention measure select** | `artifacts-bucket-retention-measure-select` (root) / `artifacts-bucket-retention-measure-select-combobox` (the actual clickable `role="combobox"` element — use THIS one to open the dropdown, confirmed live) | **added** | `CreateBucket.jsx`, on `<Select.SingleSelect id="expiration_measure">`; the shared `SingleSelect` component (`src/[fsd]/shared/ui/select/SingleSelect.jsx:82,658-659`) auto-derives the `-combobox` suffix from whatever `data-testid` is passed in |
| **New Bucket form — Retention value input** | `artifacts-bucket-retention-value-input` | **added** | `CreateBucket.jsx`, on the `<TextField id="expiration_value">` |
| **New Bucket form — Save button** | `artifacts-bucket-save-button` | **added** | `CreateBucket.jsx`, on the `<Button.BaseBtn>` that calls `onSave` |
| New Bucket form — Cancel button | none | **implementer scope call — NOT added** | this case never clicks it; per the operator-confirmed scope ruling (`.agents/testing.md`), left out |
| **Bucket-row 3-dot menu trigger** | `bucket-menu-{bucketName}-menu-button` (dynamic) | **fixed — was a bug, not just a gap** | `BucketItem.jsx`, `<DotMenu id="bucket-menu">` → now `id={`bucket-menu-${name}`}`. **Root cause was worse than "missing": the OLD static `id="bucket-menu"` meant every one of the 125 buckets in this run's project rendered the IDENTICAL `data-testid="bucket-menu-menu-button"`** — confirmed live (`document.querySelectorAll('[data-testid]')` on the bucket panel found exactly 1 unique testid string across 125 buttons) — Playwright could only disambiguate via `.nth(index)`, which breaks the instant sort order changes (new bucket, rename, pin, or another test's bucket). This was ALSO an invalid-HTML-ids bug independent of testids (`id={id + '-action'}` was duplicated across all 125 rows in the live DOM simultaneously). Fixed by templating `id` with the bucket's own `name` (already destructured in the component). Follow the project's dynamic-testid class-constant pattern when wiring into the page object (e.g. `BUCKET_MENU_BUTTON = '[data-testid="bucket-menu-{}-menu-button"]'`), same mechanism as the existing `ARTIFACT_ACTIONS_MENU_BUTTON` constant. |
| **"Upload files" bucket-menu item** | `bucket-menu-upload-files-menuitem` | **added** | `BucketItem.jsx`, added `key: 'bucket-menu-upload-files'` to the `menuItems` array's first entry — same `DotMenu`/`BasicMenuItem` mechanism (`testId: item.key` → `${testId}-menuitem`) as ELITEA-1839's fix for the file-row dot-menu |
| Bucket-menu items — Rename / Pin to top / Delete | none | **implementer scope call — NOT added** | this case only touches "Upload files"; per the same scope ruling, left as a follow-up for whichever case first exercises them |
| **Left-panel tree file/folder node** | `artifacts-tree-item-{item.key}` (dynamic, keyed by the item's full relative path, e.g. `artifacts-tree-item-test.txt` for a root-level file, or `artifacts-tree-item-a1/sample.txt` for a nested one) | **added** | `FileTreeItem.jsx`, on the inner `<Box onClick={handleSelect}>` (previously had no testid at all — only a `data-tour` attribute gated on `item.isFile`, unusable under this project's testid-only policy) |
| Upload files button (toolbar, right panel) | `artifacts-upload-files-button` | existing, **not used** by this case | separate entry point from the bucket-dot-menu path this case tests (§ Overlap check) |
| "Upload files to ..." modal — dialog / Path input / Upload button | `artifacts-upload-path-dialog` / `artifacts-upload-path-input` / `artifacts-upload-path-upload-button` | existing (ELITEA-1832) | confirmed live this run: identical dialog fires from the bucket-dot-menu entry point too |
| File list container / file row | `artifacts-file-list` / `artifacts-file-row` | existing | |
| Success toast (generic, app-wide) | `toast-message` | existing elsewhere, fidelity caveat | see Test Step 15 |

## Network Behavior
- **Bucket creation**: `POST ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}`
  with body `{name, expiration_measure, expiration_value}` → `200 OK`. Confirmed live:
  `POST http://localhost:5173/api/v2/artifacts/buckets/default/399`.
- **Bucket list refetch after creation**: `GET {ELITEA_URL}/artifacts/s3/?project_id=${PROJECT_ID}&format=json`
  — this is the call whose in-flight timing caused the transient stale-empty-state render
  noted in Test Step 7. Response shape: `{owner, buckets: [{name, creationDate, size,
  retentionDays, isPinned}, ...]}`.
- **File upload**: `PUT {ELITEA_URL}/artifacts/s3/{bucket}/{file_key}?project_id=${PROJECT_ID}`
  → `200 OK`. Confirmed live:
  `PUT http://localhost:5173/artifacts/s3/autotest-elitea1808-434462/test.txt?project_id=399`
  — **byte-identical endpoint pattern** to the toolbar-upload path ELITEA-1832 already
  documented, confirming both entry points converge on the same upload mechanism.
- No unexpected requests observed between any click and its corresponding network call;
  zero console errors across the confirmation pass that used real native clicks.

## Known Defects Found During Exploration

**None found as a product defect** — one CLARIFICATION filed
([#642](https://github.com/EliteaAI/elitea-testing-public/issues/642), see Test Step 16 /
Coverage Map) for case-text vs. product drift (no visible timestamp column), and one
**ruled-out false positive**, documented here per the Synthetic Input Hygiene guard so it
isn't rediscovered and mis-filed:

- During the FIRST verification pass of the newly-added `bucket-menu-{name}-menu-button`
  testid, a raw `element.click()` fired via `page.evaluate()` (not a real user gesture —
  used only because it was the fastest way to smoke-test the fresh HMR reload) produced a
  console error: `Warning: Failed %s type: %s%s prop MUI: The anchorEl prop provided to the
  component is invalid. The anchor element should be part of the document layout.`
  A **second, pristine pass** — fresh page navigation, real `.hover()` then a genuine
  Playwright `.click()` on the same testid via `getByTestId(...)` — produced **zero console
  errors**. This is exactly the "bug seen only after synthetic input isn't a bug yet"
  pattern: the raw JS click bypassed the row's hover-triggered layout/visibility
  transition, handing MUI's `Popover`/`Menu` an `anchorEl` that (from the synthetic click's
  perspective) wasn't fully laid out yet. **Not filed.** If the implementer's own test
  happens to hit this, the fix is procedural (always hover before clicking a
  hover-gated trigger, use real Playwright actions, never `page.evaluate(...click())`), not
  a product fix.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`). Needs THREE
  new methods this case introduces:
  1. A bucket-creation-form flow (e.g. `create_bucket_via_form(name, wait_for_visible=True)`)
     — click `create_bucket_button`, fill `artifacts-bucket-name-input` (select-all +
     `press_sequentially`, MUI pattern), click `artifacts-bucket-save-button`, then wait
     on the CONDITION described in Test Step 7 (the new bucket's own dynamic
     `bucket-menu-{name}-menu-button` becoming visible) — **not** a fixed sleep, **not** an
     immediate assertion right after the Save click (see the documented timing note).
  2. A bucket-row dot-menu opener (e.g. `open_bucket_menu(bucket_name)`) — hover the row
     first (unlike the file-row dot-menu, this one IS hover-gated), then click the dynamic
     `bucket-menu-{bucket_name}-menu-button` testid. Add a class-level template constant
     (`BUCKET_MENU_BUTTON = '[data-testid="bucket-menu-{}-menu-button"]'`), same pattern as
     the existing `ARTIFACT_ACTIONS_MENU_BUTTON`.
  3. A bucket-dot-menu "Upload files" click (e.g. `upload_files_via_bucket_menu(bucket_name,
     file_paths)`) — open the bucket menu (method 2), click
     `bucket-menu-upload-files-menuitem`, then reuse the EXISTING
     `wait_for_upload_path_dialog()` / `get_upload_path_prefix_text()` /
     `click_upload_path_upload_button()` methods already on `ArtifactsPage` (ELITEA-1832) —
     confirmed live this run they work identically from this entry point, no new dialog
     handling needed.
- Do **not** add a `.nth(index)` fallback anywhere for the bucket-menu testid now that it's
  unique per bucket — the whole point of the fix was to make position-independent targeting
  possible; a positional selector against a 125+-bucket, alphabetically-resorting list is
  exactly the fragility this fix eliminates.
- Fixtures: do NOT use the existing `artifact_bucket` fixture for the bucket itself (it
  creates via API, which is wrong for a case whose own subject is the UI creation flow) —
  generate just the unique NAME the same way that fixture does
  (`automation/fixtures/data_fixtures.py:455`'s naming scheme), then drive creation via the
  new page-object method above. `tmp_path` for `test.txt` (§ Test Data).
- Wait strategy: Test Step 6→7 needs a condition-based wait on the new bucket's dynamic
  testid appearing, not a fixed timeout and not an immediate assertion — see the documented
  timing note in Test Step 7. Step 9's file-chooser and step 14's upload PUT both already
  have natural Playwright wait points (`expect_file_chooser()`, `expect_download()`-style —
  actually just await the `PUT` via `page.wait_for_response()` or assert on the file row
  appearing, no download event involved here since this is an upload).
