# Test Case: Upload Files to Bucket Subfolder via Three Upload Options and Verify Bucket Selection and Contents

## Metadata
- **TMS ID**: ELITEA-1824
- **Linked Story**: [EliteaAI/elitea-testing-public#228](https://github.com/EliteaAI/elitea-testing-public/issues/228) (tracking issue)
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399, freshly synced
  against `origin/main` this session via `git fetch origin` — see § Concrete Handles for
  per-testid provenance).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **defect-found** — case executed end-to-end live (all 46 case steps + all 3
  preconditions), and a real, reproducible product defect was discovered and filed
  ([#649](https://github.com/EliteaAI/elitea-testing-public/issues/649)) that directly
  contradicts the case's own literal expected results for steps 31/32/35/36 (the bucket
  3-dot-menu "Upload files" entry point does not reset its default path to the bucket root
  when the user was previously navigated into a subfolder — see § Known Defects). This is
  an **isolated** defect, not a blocking one: every one of the case's other 42 steps passed
  cleanly against the live product, and the full 46-step flow (including the buggy step)
  was completed end-to-end using a one-line workaround (clearing the Path field / re-
  navigating to bucket root before invoking the bucket-menu upload). Per this project's
  merge-gate "Sanctioned-RED exception" (`.agents/testing.md` § Merge gate) this is exactly
  the shape that pattern exists for — **recommend the implementer proceed with automation
  using `expect.soft()` + `# Known defect: #649`** for the one affected assertion rather
  than pausing the whole case; see § Automation Hints for the concrete guidance. Two
  additional CLARIFICATIONs (case-text drift, not defects) were also filed:
  [#650](https://github.com/EliteaAI/elitea-testing-public/issues/650) (menu item is
  "Rename" not "Edit") and
  [#651](https://github.com/EliteaAI/elitea-testing-public/issues/651) (bucket-row click
  toggles expand/collapse rather than unconditionally expanding). Two genuine testid gaps
  were found (center empty-state "Upload files" button, breadcrumb header labels) and one
  missing `data-*` state attribute (selected/highlighted bucket row and tree item) — all
  specced as `testid needed:` per `.agents/role-overrides.md` § Analyst slot (NOT
  self-fixed this run — that section explicitly reserves testid additions for the
  implementer slot: *"Do not soften a testid demand into a MINOR defect or a note; it is
  implementer work, and the AFS is its work order"*). Not `already-covered` / not
  `extend-existing` — see § Overlap check below.

## Overlap check vs existing automation

`automation/pages/artifacts_page.py` was read in full before this run (1292 lines), plus
the three closest sibling AFS files/specs were read in full:
`test-specs/artifacts/l2_create-bucket-path1-and-upload-file_ELITEA-1808.md`
(`test_artifacts_create_bucket_upload_file.py`),
`test-specs/artifacts/l2_upload-flow-upload-multiple-files-at-once_ELITEA-1826.md`
(`test_artifacts_multi_file.py` family), and
`test_artifacts_upload_duplicate_cancel.py`/ELITEA-1832.

- **ELITEA-1808** — drives the bucket-menu "Upload files" entry point, but ONLY from the
  Artifacts landing page BEFORE any bucket has ever been opened/navigated into (a single
  file, into a freshly-created empty bucket). `currentPrefix` is empty at that point, so
  the defect this case (1824) found never manifests in 1808's flow — 1808 never had a
  chance to observe it. Also, 1808 drives bucket **creation** via the UI form; 1824's own
  precondition instead assumes a bucket already exists — creation is not a tested step
  here.
- **ELITEA-1826** — drives the **toolbar** upload button with **3 simultaneous** files in
  ONE dialog action, no duplicates, no subfolder navigation. Different entry point count
  (1, not 3), different file-selection shape (batch vs. sequential across 3 distinct entry
  points), and never touches the bucket-menu entry point or subfolder/root selection
  behavior at all.
- **ELITEA-1832** — drives the toolbar upload with a deliberate duplicate-file collision
  and Cancel; terminal assertions verify the upload was **aborted**. Never reaches a
  completed upload, never touches the bucket-menu entry point, never tests folder
  selection/breadcrumb/URL behavior.

None of the three existing specs combine (a) all three visually-distinct upload entry
points in one flow, (b) folder vs. root path targeting per entry point, or (c) left-panel
bucket/folder tree selection + breadcrumb + URL synchronization. Verdict: **zero
behavioral overlap** — this is a materially new, broader end-to-end scenario.
`defect-found` (see § Status above for why this is not `blocked`).

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists and is empty (the case's `bucket-1` is a **case-text placeholder**, not a
  literal fixture name — confirmed live again this run: the left-panel bucket list showed
  187 buckets at the time of this run, including every `autotest-*` bucket from prior
  cases' runs, and none named exactly `bucket-1`; same finding as ELITEA-1808/1826/1832).
  **Confirms the dispatch's reasoning**: unlike ELITEA-1808 (where bucket *creation* IS a
  tested step), this case's own precondition is "Bucket bucket-1 exists and is empty" —
  creation is setup, not a case step. The existing `artifact_bucket` pytest fixture
  (`automation/fixtures/data_fixtures.py:455`, API-created via `ArtifactAPI.create_bucket`,
  fresh/empty/function-scoped, deleted in its own teardown) is the correct
  `reuse-existing`-shaped setup — same as ELITEA-1826's precedent, NOT ELITEA-1808's
  UI-driven creation. (This exploration run itself used the UI "+ Artifact Bucket" form for
  operator convenience/speed while manually verifying the flow — that is NOT what the
  automated test should do; the automated test should use the `artifact_bucket` fixture.)
- Test files `sample.txt`, `sample.png`, `sample.md` are available for upload — generate
  via `tmp_path` in test setup (§ Test Data).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the `artifact_bucket` fixture (see § Preconditions) — do **not**
  hardcode `bucket-1`.
- **Subfolder name `a1`** — confirmed live as a real, intentional literal from the case
  text (used consistently across all three upload entry points and all the tree/breadcrumb
  assertions) — not a placeholder.
- **File names — confirmed live these are NOT placeholders, same finding as ELITEA-1826.**
  The case's own steps 15/24/36/41/42/45 assert the exact literal strings `sample.txt`,
  `sample.png`, `sample.md` must appear (or be absent) in specific locations. Since
  `artifact_bucket` mints a fresh, uniquely-named bucket per test, there is no collision
  risk in reusing these literal filenames verbatim.
- **File content/format** — generate via `tmp_path` (project convention, no checked-in
  `automation/fixtures/files/` directory exists):
  - `sample.txt` — small fixed text content (this run: 57 B).
  - `sample.md` — small fixed markdown content (this run: 56 B).
  - `sample.png` — a minimal valid PNG built in-memory. **Reuse, don't reinvent**: the
    exact in-memory PNG-builder helper already exists at
    `test_artifacts_upload_duplicate_cancel.py:75-91` (`_minimal_png_bytes()`) — confirmed
    live this run it uploads and renders correctly as `"PNG Image"` in the Type column
    (this run: 69 B).
- **Confirmed live Type-column mapping** (re-confirms ELITEA-1826's finding): `.txt` →
  `"Text"`, `.md` → `"Markdown"`, `.png` → `"PNG Image"`.
- **Viewport**: same finding as ELITEA-1808/1826 — the "Last update" timestamp column is
  present in the DOM but visually clipped below ~1600px width. This run used 1600×900;
  automation should set the same or otherwise confirm the column before asserting the
  timestamp segment.

No `reuse-existing` fixture applies for the bucket's CONTENTS (only for the empty bucket
itself, via `artifact_bucket`) — same reasoning as the sibling cases: a bucket in a
specific multi-file, multi-folder state isn't safe to share across parallel/serial runs.

## Test Steps

1. Navigate to `${BASE_URL}/artifacts` (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible.
2. Verify the fixture-created bucket is visible in the left-panel bucket list (case step 2).
   - **Verify**: `[data-testid="artifacts-bucket-row-{bucket_name}"]` visible.
3. Navigate into the bucket via `navigate_to_bucket(bucket_name)` (case step 3) — confirmed
   live this reaches the identical state a left-panel click would, per the existing
   page-object docstring / ELITEA-1826 precedent.
   - **Verify**: `is_bucket_empty() == True` (case steps 3-4 — "No files in this bucket"
     message + center "Upload files" button both present).
4. Click the CENTER "Upload files" button — the empty-state button, **not** the toolbar one
   (case step 5). **Confirmed live via DOM inspection this run: these are two DIFFERENT
   elements.** The toolbar button (top-right, used in step 16) has `data-testid=
   "artifacts-upload-files-button"`. The center empty-state button
   (`ArtifactTableNoFiles.jsx`'s `<Button.BaseBtn>`) has **NO testid at all** — confirmed
   via source (`git show origin/automation/testids:src/pages/Artifacts/component/
   ArtifactTableNoFiles.jsx`, no `data-testid` prop anywhere on the button). See § Concrete
   Handles for the `testid needed:` row.
   - **Verify**: native file-chooser fires immediately (case step 6) — confirmed live via
     `expect_file_chooser()`, no loading delay.
5. Select `sample.txt` via `file_chooser.set_files([sample_txt_path])` (case step 7).
6. Confirm selection — mechanically the same Playwright action as step 5 (case step 8; no
   separate native "Open" click to drive).
   - **Verify**: `artifacts-upload-path-dialog` visible; `artifacts-upload-path-input`'s
     prefix text is `"{bucket_name}/"` (case step 9).
7. Click into `artifacts-upload-path-input` and type `a1` (case step 10 — "append '/a1'").
   Confirmed live: the prefix segment (`"{bucket_name}/"`) is a read-only startAdornment;
   typing `a1` into the editable textbox produces the combined displayed path
   `"{bucket_name}/a1"` — do NOT type a leading `/`, the prefix already supplies the
   trailing slash.
   - **Verify**: combined Path text reads `"{bucket_name}/a1"`.
8. Click `artifacts-upload-path-upload-button` (case step 11).
   - **Verify**: `PUT ${ELITEA_URL}/artifacts/s3/{bucket_name}/a1/sample.txt?project_id=
     ${PROJECT_ID}` → `200 OK` (confirmed live, § Network Behavior).
9. Verify the success toast (case step 12).
   - **Verify**: `toast-message` becomes visible with EXACT text
     `"Your file(s) have been successfully uploaded!"` — confirmed live this run via a
     `MutationObserver` installed before triggering a (separate, throwaway) upload, since a
     single-shot snapshot can miss the short-lived toast; use Playwright's auto-retrying
     `expect(...).to_be_visible()`/`.to_contain_text(...)` immediately after the Upload
     click, never a single instantaneous DOM read.
10. Verify the left panel shows subfolder `a1` nested under the bucket (case step 13).
    - **Verify**: `[data-testid="artifacts-tree-item-a1/"]` visible — **note the trailing
      slash in the testid value**, confirmed live this run (`FileTreeItem.jsx` keys folder
      nodes by their full relative path INCLUDING a trailing `/`, unlike file nodes which
      have no trailing slash, e.g. `artifacts-tree-item-sample.txt`).
11. Verify the main-panel breadcrumb header shows `"{bucket_name} > a1"` (case step 14).
    - **Verify**: **no testid exists for this** — confirmed via source
      (`src/pages/Artifacts/component/BreadcrumbNavigation.jsx` renders each crumb as a
      bare `<Typography variant="headingSmall">` with no `data-testid`; the bucket-name
      label itself is a separate, also-untestid'd `<Typography>` rendered by the toolbar
      header). See § Concrete Handles for the `testid needed:` rows.
12. Verify `sample.txt` is listed in the file table with Name/Type/Size/Last-update
    populated (case step 15).
    - **Verify**: `get_file_row_text("sample.txt")` contains `"sample.txt"`, `"Text"`, a
      byte-size string, and a `\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)` timestamp (pattern
      only).
13. Click the TOOLBAR "Upload files" icon (top-right corner) — `artifacts-upload-files-
    button` (case step 16). Confirmed live its parent element carries
    `aria-label="Upload files"` (MUI `Tooltip` static-attribute technique — matches the
    case's "tooltip: 'Upload files'" note).
    - **Verify**: native file-chooser fires immediately (case step 17).
14. Select `sample.png` (case step 18).
15. Confirm selection (case step 19 — same fold as step 6).
    - **Verify**: `artifacts-upload-path-dialog` visible; Path prefix now reads
      `"{bucket_name}/a1/"` (case step 20) — confirmed live this correctly carries over the
      currently-navigated folder (no change needed, matches case step 21).
16. Click `artifacts-upload-path-upload-button` (case step 22).
    - **Verify**: `PUT .../artifacts/s3/{bucket_name}/a1/sample.png?project_id=
      {PROJECT_ID}` → `200 OK`.
17. Verify success toast (case step 23) — same mechanism as step 9.
18. Verify `sample.png` is listed alongside `sample.txt` in the `"{bucket_name} > a1"` view
    (case step 24).
    - **Verify**: `set(get_file_names()) == {"sample.txt", "sample.png"}`;
      `get_total_file_count_from_pagination() == 2`.
19. Hover the bucket's own row in the left panel and click its 3-dot menu trigger (case
    step 25). Confirmed live: `open_bucket_menu(bucket_name)` (existing page-object method,
    ELITEA-1808) works unchanged from this navigated-into-a-subfolder state.
    - **Verify**: dropdown shows "Upload files", "Rename", "Pin to top", "Delete" (case
      step 26 — **case text says "Edit"; live product says "Rename"** — case-text drift,
      filed as CLARIFICATION [#650](https://github.com/EliteaAI/elitea-testing-public/issues/650),
      not a defect; assert the live label `"Rename"`).
20. Click `bucket-menu-upload-files-menuitem` (case step 27).
    - **Verify**: native file-chooser fires immediately (case step 28).
21. Select `sample.md` (case step 29).
22. Confirm selection (case step 30 — same fold as step 6).
    - **Verify (KNOWN DEFECT — [#649](https://github.com/EliteaAI/elitea-testing-public/issues/649)
      — soft-assert only, see § Known Defects and § Automation Hints)**: case steps 31/32
      expect the Path field to read `"{bucket_name}"` only (bucket root, no subfolder).
      **Confirmed live this run it instead reads `"{bucket_name}/a1/"`** — the bucket-menu
      upload entry point does not reset the dialog's default path to bucket root; it
      inherits whatever folder the user is CURRENTLY navigated into (root cause: shared
      `currentPrefix` state in `useFileUpload.hooks.js`, not reset for this entry point —
      full detail in § Known Defects). `expect.soft()` this assertion against the buggy
      actual value, tagged `# Known defect: #649`.
23. **Workaround (required to continue the case meaningfully — do this regardless of step
    22's soft-assert outcome):** clear the Path field back to empty (removing the inherited
    `"a1/"` suffix) before clicking Upload, so the file lands at the intended bucket root.
    Confirmed live this is a simple `select_text()` + type-empty / backspace on
    `artifacts-upload-path-input`.
24. Click `artifacts-upload-path-upload-button` (case step 33).
    - **Verify**: `PUT .../artifacts/s3/{bucket_name}/sample.md?project_id={PROJECT_ID}` →
      `200 OK` (root-level key, no `a1/` prefix — confirms the workaround succeeded).
25. Verify success toast (case step 34).
26. Verify the main-panel breadcrumb shows `"{bucket_name}"` only, no subfolder suffix (case
    step 35) — same `testid needed:` gap as step 11.
27. Verify `sample.md` is listed in the file table at bucket root (case step 36).
    - **Verify**: `file_exists("sample.md")` at root; `sample.md` row shows Type
      `"Markdown"`.
28. Click the bucket's own row/name in the left panel (case step 37). **Confirmed live this
    is a TOGGLE, not an unconditional expand** — case-text drift, filed as CLARIFICATION
    [#651](https://github.com/EliteaAI/elitea-testing-public/issues/651), not a defect. See
    § Automation Hints for the deterministic sequencing the implementer needs (a single
    blind click is not reliable here).
29. Verify the bucket is highlighted/selected AND the tree expands to show subfolder `a1`
    (case step 38).
    - **Verify (selection state)**: **no `data-*` state attribute exists** — confirmed live
      via `getAttribute` inspection, the ONLY signal is a CSS `background-color` change via
      an unstable emotion-hash class (`css-guc4qj`-style, regenerated per build). This
      violates this project's own rule (`.agents/testing.md` § Locator policy: state is a
      `data-*` filter on the stable testid, never CSS-only) — see § Concrete Handles for
      the `testid needed:` row (a `data-selected` attribute, NOT a new testid, on the
      already-testid'd `artifacts-bucket-row-{name}`).
    - **Verify (expand state)**: `[data-testid="artifacts-tree-item-a1/"]` visible (after
      the deterministic click sequencing from step 28's note).
30. Click on subfolder `a1` under the bucket in the left panel — `[data-testid=
    "artifacts-tree-item-a1/"]` (case step 39).
    - **Verify**: URL becomes `...?bucket={bucket_name}&folder=a1`.
31. Verify `a1` is highlighted AND the breadcrumb shows `"{bucket_name} > a1"` (case step
    40).
    - **Verify (selection state)**: same `data-*` gap as step 29, on
      `artifacts-tree-item-a1/` this time — confirmed live, identical finding (class-only,
      no attribute).
    - **Verify (breadcrumb)**: same `testid needed:` gap as step 11.
32. Verify the file table in `"{bucket_name} > a1"` contains EXACTLY 2 files: `sample.txt`
    and `sample.png` (case step 41).
    - **Verify**: `get_total_file_count_from_pagination() == 2`;
      `set(get_file_names()) == {"sample.txt", "sample.png"}`.
33. Verify `sample.md` is NOT listed in this view (case step 42).
    - **Verify**: `file_exists("sample.md") == False` while in the `a1` folder view.
34. Click on the bucket's own row/name (root level) in the left panel (case step 43).
    - **Verify**: URL becomes `...?bucket={bucket_name}` (no `folder` param).
35. Verify the breadcrumb shows `"{bucket_name}"` only (case step 44) — same
    `testid needed:` gap as step 11.
36. Verify `sample.md` is listed at the root level (case step 45).
    - **Verify**: `file_exists("sample.md") == True` at root.
37. Verify the URL reflects the currently-selected bucket and folder path (case step 46).
    - **Verify**: needs no testid — read `page.url` directly. Confirmed live across every
      navigation this run: root state → `?bucket={name}` (no `folder` param); subfolder
      state → `?bucket={name}&folder=a1`.

## Expected Results
- All three upload entry points (center empty-state button, toolbar icon, bucket-menu
  dropdown item) successfully upload files via the identical underlying
  `artifacts-upload-path-dialog` / `PUT /artifacts/s3/{bucket}/{key}` mechanism.
- `sample.txt` and `sample.png` land in `{bucket}/a1/`; `sample.md` lands at `{bucket}/`
  root — but **only via the workaround in Test Step 23**, since the bucket-menu entry
  point's own DEFAULT path is bugged (§ Known Defects, [#649](https://github.com/EliteaAI/elitea-testing-public/issues/649)).
- Left-panel tree and main-panel breadcrumb stay in sync with the current bucket/folder
  selection, including a working (if untestid'd) highlighted/selected visual state.
- The URL query params (`bucket`, `folder`) always reflect the current selection.
- No console errors during the flow (confirmed: 0 errors across the entire run, 14 total
  console messages, only 1 pre-existing unrelated Vite dev-server warning about
  `docx-js-editor` module externalization).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture | asserted |
| Precondition: bucket "bucket-1" exists and is empty | Bucket available, empty | Preconditions + Test Data | `artifact_bucket` fixture (fresh, unique name — "bucket-1" confirmed live as case-text placeholder, none of 187 buckets literally named that) | asserted |
| Precondition: sample.txt/png/md available | Files exist locally | Preconditions + Test Data | `tmp_path`-generated files, PNG via `_minimal_png_bytes()` | asserted |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Verify bucket-1 exists in list | Bucket visible | Test Step 2 | `artifacts-bucket-row-{name}` visible | asserted |
| Step 3: Click bucket-1 | Empty-state shown | Test Step 3 | `is_bucket_empty()==True` | asserted |
| Step 4: Verify empty state + center Upload button | Empty state displayed | Test Step 3 (folded) | same observable | asserted *(decomposed)* |
| Step 5: Click center Upload button | File explorer opens | Test Step 4 | `expect_file_chooser()` on the (testid-needed) center button | asserted |
| Step 6: Verify file explorer opens | Explorer open | Test Step 4 (folded) | same observable | asserted *(decomposed)* |
| Step 7: Select sample.txt | File selected | Test Step 5 | `set_files([sample_txt])` | asserted |
| Step 8: Click Open | Modal opens | Test Step 6 | `set_files()` IS the confirm | asserted *(decomposed)* |
| Step 9: Verify modal opens, Path pre-filled with bucket-1 | Modal open, correct path | Test Step 6 | `get_upload_path_prefix_text()` contains `{bucket_name}/` | asserted *(generated name, not literal "bucket-1")* |
| Step 10: Append "/a1" to Path | Path shows "bucket-1/a1" | Test Step 7 | combined Path text check | asserted |
| Step 11: Click Upload | Upload completes | Test Step 8 | `PUT .../a1/sample.txt` → 200 | asserted |
| Step 12: Verify success notification | Toast shown | Test Step 9 | `toast-message` exact text, MutationObserver-confirmed | asserted |
| Step 13: Verify a1 subfolder appears under bucket-1 | a1 visible in tree | Test Step 10 | `artifacts-tree-item-a1/` visible (note trailing slash) | asserted |
| Step 14: Verify breadcrumb "bucket-1 > a1" | Breadcrumb correct | Test Step 11 | text content of two untestid'd spans | clarification *(testid needed — see § Concrete Handles)* |
| Step 15: Verify sample.txt listed with metadata | Row populated | Test Step 12 | `get_file_row_text()` Name/Type/Size/timestamp | asserted |
| Step 16: Click toolbar upload icon | File explorer opens | Test Step 13 | `expect_file_chooser()` on `artifacts-upload-files-button` | asserted |
| Step 17: Verify file explorer opens | Explorer open | Test Step 13 (folded) | same observable | asserted *(decomposed)* |
| Step 18: Select sample.png | File selected | Test Step 14 | `set_files([sample_png])` | asserted |
| Step 19: Click Open | Modal opens | Test Step 15 | same fold pattern | asserted *(decomposed)* |
| Step 20: Verify Path pre-filled "bucket-1/a1" | Path correct | Test Step 15 | prefix text check | asserted |
| Step 21: Verify path unchanged | No edit needed | Test Step 15 | same check | asserted |
| Step 22: Click Upload | Upload completes | Test Step 16 | `PUT .../a1/sample.png` → 200 | asserted |
| Step 23: Verify success notification | Toast shown | Test Step 17 | same as step 9 | asserted |
| Step 24: Verify both files listed together | 2 files shown | Test Step 18 | file-name set + pagination count | asserted |
| Step 25: Hover bucket, click 3-dot menu | Menu appears | Test Step 19 | `open_bucket_menu()` | asserted |
| Step 26: Verify menu items (case says "Edit") | 4 items visible | Test Step 19 | live label is "Rename", not "Edit" | clarification *(filed [#650](https://github.com/EliteaAI/elitea-testing-public/issues/650), not a defect)* |
| Step 27: Click "Upload files" | File explorer opens | Test Step 20 | `expect_file_chooser()` | asserted |
| Step 28: Verify file explorer opens | Explorer open | Test Step 20 (folded) | same observable | asserted *(decomposed)* |
| Step 29: Select sample.md | File selected | Test Step 21 | `set_files([sample_md])` | asserted |
| Step 30: Click Open | Modal opens | Test Step 22 | same fold pattern | asserted *(decomposed)* |
| Step 31: Verify Path pre-filled "bucket-1" (root) | Path is root-only | Test Step 22 | **actual: `"{bucket_name}/a1/"`, not root** | defect *(filed [#649](https://github.com/EliteaAI/elitea-testing-public/issues/649) — see § Known Defects)* |
| Step 32: Verify path has no subfolder | Root-only path | Test Step 22 | same as step 31 | defect *(same #649)* |
| Step 33: Click Upload | Upload completes | Test Steps 23-24 | workaround clears path first, then `PUT .../sample.md` (root key) → 200 | asserted *(via workaround — see § Known Defects)* |
| Step 34: Verify success notification | Toast shown | Test Step 25 | same as step 9 | asserted |
| Step 35: Verify breadcrumb "bucket-1" (root) | Breadcrumb correct | Test Step 26 | same testid gap as step 14 | clarification *(testid needed)* |
| Step 36: Verify sample.md at root level | File at root | Test Step 27 | `file_exists("sample.md")` at root | asserted |
| Step 37: Click bucket-1 in left panel | Bucket selected | Test Step 28 | click is a TOGGLE, not unconditional | clarification *(filed [#651](https://github.com/EliteaAI/elitea-testing-public/issues/651), not a defect)* |
| Step 38: Verify highlighted + expands to show a1 | Selected + expanded | Test Step 29 | expand state via tree-item visibility (asserted); selected state has NO data-* attribute | clarification *(testid needed — see § Concrete Handles)* |
| Step 39: Click a1 subfolder | a1 selected | Test Step 30 | URL becomes `...&folder=a1` | asserted |
| Step 40: Verify a1 highlighted + breadcrumb "bucket-1 > a1" | Highlighted + breadcrumb | Test Step 31 | same two gaps as steps 14/38 | clarification *(testid needed)* |
| Step 41: Verify exactly 2 files (sample.txt, sample.png) | 2 files shown | Test Step 32 | pagination count + name set | asserted |
| Step 42: Verify sample.md NOT in a1 view | sample.md absent | Test Step 33 | `file_exists()==False` | asserted |
| Step 43: Click bucket-1 (root level) | Root shown | Test Step 34 | URL loses `folder` param | asserted |
| Step 44: Verify breadcrumb "bucket-1" | Breadcrumb correct | Test Step 35 | same testid gap as step 14 | clarification *(testid needed)* |
| Step 45: Verify sample.md at root | File at root | Test Step 36 | `file_exists()` at root | asserted |
| Step 46: Verify URL reflects selection | URL correct | Test Step 37 | `page.url` read directly, no testid needed | asserted |
| Expected Final State: 3 upload paths correct, URL synced | Composite pass condition | Test Steps 8/16/23-24/30/34/36-37 | combination of the above (Step 33's defect worked around) | asserted *(with the one soft-assert exception, #649)* |
| Pass criterion: "All steps complete without errors" | No errors | All steps | 0 console errors across full run (14 messages, 1 unrelated pre-existing warning) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Root-cause isolation of the #649 defect via a second controlled pass** — *added: after
  observing the buggy default path, re-tested the identical entry point from a
  freshly-reselected bucket ROOT (empty `currentPrefix`) and confirmed it correctly shows
  the root-only path there — proves the defect is specifically about *stale prior
  navigation state*, not a general breakage of the dialog. This is the difference that
  makes the defect report actionable (points directly at `useFileUpload.hooks.js`'s
  `computeFullPath`/`currentPrefix` reuse) rather than a vague "path sometimes wrong".*
- **Network-level proof for every one of the 4 upload PUTs (3 case files + 1 throwaway
  toast-check file), each verified 200 OK** — *added: stronger signal than DOM-only
  checks, and the two "wrong-location" vs. "correct-location" PUT URLs for `sample.md`
  are the direct evidence for the #649 defect report.*
- **Independent MutationObserver-based confirmation the success toast fires with the
  EXACT case-specified string** — *added: same rationale as ELITEA-1826's precedent,
  confirmed again fresh this run rather than only cited by reference.*
- **Testid provenance verified via a fresh `git fetch origin` + `git grep` against both
  `origin/main` and `origin/automation/testids`** for every handle this case touches —
  *added: `.agents/role-overrides.md` § Analyst slot hard requirement; also surfaced that
  `delete-confirm-button` (used only for this run's own cleanup, not case-required) is
  testids-only, awaiting promotion.*
- **Console-error check across the full flow (14 messages total)** — *added: standard
  silent-error guard, consistent with sibling cases' precedent.*
- **Cleanup-mechanics discovery**: used the file-row dot-menu Delete flow
  (`artifact-actions-{filename}-menu-button` → `artifacts-file-delete-menuitem` →
  `delete-confirm-button`) to remove a mis-placed file during this exploration — *added:
  confirmed live and documented for the implementer's/any future case's cleanup needs,
  not required by this case's own steps but useful precedent.*

## Cleanup
1. Delete the fixture-created bucket via `ArtifactAPI.delete_bucket(bucket_name)`
   (`automation/api/client.py:1205`) in the test's own teardown (via `artifact_bucket`
   fixture). **Known pre-existing defect, already filed
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)):** this delete
   call 404s on both URL-format attempts in the current dev environment, so the bucket will
   likely leak — not new to this case, out of scope to fix here.
2. No other entities are created by this case (no Agent, no Toolkit, no Credential).
3. **This exploration run's artifacts** (not part of the automated test): bucket
   `autotest-el1824-042317` was created via the live UI "New Bucket" form (operator
   convenience for manual exploration — the automated test itself should use the
   `artifact_bucket` fixture instead, see § Preconditions) in the `Private` project (id
   399), containing at hand-off: `sample.txt` (57 B) and `sample.png` (69 B) in subfolder
   `a1/`, and `sample.md` (56 B) at bucket root. A throwaway `toastcheck-1824.txt` (used
   only to independently verify the success-toast text) was uploaded and deleted again
   during this run. An earlier mis-placed `a1/sample.md` (created while reproducing the
   #649 defect before applying the workaround) was also deleted via the file-row dot-menu.
   Left in place — matches this project's existing convention of ~187 un-deleted
   `autotest-*` buckets already present from prior runs; safe to delete at any time via
   `ArtifactAPI.delete_bucket("autotest-el1824-042317")`.
4. Local exploration screenshots (repo root, untracked):
   `ELITEA-1824-BUG-bucket-menu-upload-path-not-reset-to-root.png` (uploaded + embedded in
   [#649](https://github.com/EliteaAI/elitea-testing-public/issues/649) per
   `.agents/role-overrides.md` § screenshot evidence),
   `ELITEA-1824-step44-45-46-final-state-root-with-a1-and-samplemd.png` (local-only,
   supplementary).
5. Local temp upload source files (untracked, harmless to leave or delete):
   `.playwright-mcp/sample.txt`, `.playwright-mcp/sample.png`, `.playwright-mcp/sample.md`,
   `.playwright-mcp/toastcheck-1824.txt`.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator
policy (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) is
**testid-only, no fallback ladder** — `LocatorDescriptor(testid=...)` with no
`fallback=`/`locator=`. Every row below carries a **PROVENANCE** column verified this run
via `cd ../EliteaUI && git fetch origin` followed by `git grep` against both
`origin/main` and `origin/automation/testids` (raw command output captured this run;
summarized per row).

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | on-main ✓ | existing, `ArtifactsPage.wait_for_page_load()` |
| Bucket row (hover/click target) | `artifacts-bucket-row-{name}` (dynamic) | on-automation/testids only (awaiting promotion) | `BucketItem.jsx`; used for hover-to-reveal-menu, click-to-select/toggle-expand, and as the wait condition after bucket creation |
| Bucket-menu trigger | `bucket-menu-{name}-menu-button` (dynamic) | on-automation/testids only | `BucketItem.jsx`; hover-gated, must hover `artifacts-bucket-row-{name}` first |
| Bucket-menu "Upload files" item | `bucket-menu-upload-files-menuitem` | on-automation/testids only | static testid regardless of which bucket's menu is open |
| **Center empty-state "Upload files" button** | none | **testid needed: `artifacts-upload-files-empty-state-button`** | `ArtifactTableNoFiles.jsx`'s `<Button.BaseBtn>` (case step 5) — confirmed via source this run: zero `data-testid` prop anywhere on this element on EITHER branch. This is a DIFFERENT element from the toolbar upload button below — confirmed live via DOM inspection (`document.querySelectorAll('button')` scan) they render as two separate buttons with different classes/positions, only one of which (`artifacts-upload-files-button`) has a testid. |
| Toolbar "Upload files" button (top-right) | `artifacts-upload-files-button` | on-main ✓ | `ArtifactTableToolbar.jsx`; case step 16's entry point; confirmed live parent carries `aria-label="Upload files"` (matches case's tooltip note) |
| "Upload files to ..." dialog | `artifacts-upload-path-dialog` | on-automation/testids only | existing (ELITEA-1832) |
| Upload path input | `artifacts-upload-path-input` | on-automation/testids only | prefix segment is a read-only startAdornment; type only the subfolder suffix, no leading `/` |
| Upload path "Upload" button | `artifacts-upload-path-upload-button` | on-automation/testids only | existing (ELITEA-1832) |
| Left-panel tree item (file/folder) | `artifacts-tree-item-{key}` (dynamic) | on-automation/testids only | `FileTreeItem.jsx`; **folder keys carry a trailing slash** (`artifacts-tree-item-a1/`), confirmed live this run — file keys do not (`artifacts-tree-item-sample.txt`) |
| **Bucket-row / tree-item "selected/highlighted" state (steps 38, 40)** | none | **testid needed: add `data-selected="true"/"false"` attribute** on the ALREADY-testid'd `artifacts-bucket-row-{name}` and `artifacts-tree-item-{key}` elements — NOT a new testid, per `.agents/testing.md` § Locator policy ("state via data-* attribute, never a separate testid") | Confirmed live via `getAttribute` inspection on both elements: zero `data-*` state attribute exists today, the ONLY signal of "selected" is a `background-color: rgba(41, 184, 245, 0.15)` style change via an unstable emotion-hash CSS class (regenerated per build, e.g. `css-guc4qj`) — not automatable per policy as-is |
| **Main-panel breadcrumb header (steps 14, 35, 40, 44)** | none | **testid needed: `artifacts-breadcrumb-bucket-label`** (bucket-name span, rendered by `ArtifactTableToolbar.jsx`) **+ `artifacts-breadcrumb-folder-label`** (dynamic, one per crumb, rendered by `BreadcrumbNavigation.jsx`'s per-crumb `<Typography variant="headingSmall">`) | Confirmed via source this run (`BreadcrumbNavigation.jsx`): crumbs render as bare `<Typography>` with zero `data-testid`. The folder label is CONDITIONALLY present (absent at bucket-root state, present when inside a subfolder) — same conditional-rendering shape as the existing `ARTIFACTS_TREE_ITEM` pattern, not a state-toggled testid violation. |
| File list container / file row / folder row | `artifacts-file-list` / `artifacts-file-row` / `artifacts-folder-row` | on-main ✓ | existing |
| File-row actions dot-menu trigger | `artifact-actions-{filename}-menu-button` (dynamic) | on-main ✓ | existing (ELITEA-1839); used this run only for exploration cleanup (deleting a mis-placed file), not required by the case's own steps |
| File-row "Delete" menu item | `artifacts-file-delete-menuitem` | on-automation/testids only | computed via the shared `DotMenu`/`BasicMenuItem` `key`→`${key}-menuitem` mechanism (`ArtifactRowActions.jsx`'s `key: 'artifacts-file-delete'`), same pattern as `bucket-menu-upload-files-menuitem` — not a literal string in source, hence not directly `git grep`-able by the exact testid string |
| Delete-confirmation dialog "Delete" button | `delete-confirm-button` | on-automation/testids only | `DeleteEntityModal.jsx`; used this run only for exploration cleanup |
| Success toast (generic, app-wide) | `toast-message` | on-main ✓ | confirmed live this run for the successful-upload path (all 3 case files + 1 throwaway), exact text `"Your file(s) have been successfully uploaded!"` |

## Network Behavior
- **Bucket open**: `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id=${PROJECT_ID}
  &format=json` → `200 OK` on `navigate_to_bucket()`.
- **Upload via center empty-state button (option 1)**: `PUT {ELITEA_URL}/artifacts/s3/
  {bucket}/a1/sample.txt?project_id=${PROJECT_ID}` → `200 OK`.
- **Upload via toolbar button (option 2)**: `PUT {ELITEA_URL}/artifacts/s3/{bucket}/a1/
  sample.png?project_id=${PROJECT_ID}` → `200 OK`.
- **Upload via bucket-menu (option 3) — BUGGY default path**: confirmed live
  `PUT {ELITEA_URL}/artifacts/s3/{bucket}/a1/sample.md?project_id=${PROJECT_ID}` → `200 OK`
  fires if the Path field is left at its (buggy) default — this is the WRONG location per
  the case's own expectation.
- **Upload via bucket-menu (option 3) — after the workaround**: confirmed live
  `PUT {ELITEA_URL}/artifacts/s3/{bucket}/sample.md?project_id=${PROJECT_ID}` → `200 OK`
  (correct root-level key) once the Path field is manually cleared first.
- **Upload via bucket-menu from a freshly-reselected bucket root** (the isolation check for
  #649): confirmed live the SAME entry point correctly pre-fills `"{bucket}/"` (root-only)
  when `currentPrefix` is empty at click time — isolates the defect to stale-navigation-
  state reuse, not a general dialog breakage.
- No unexpected requests observed between any click and its corresponding network call;
  zero console errors across the entire run (14 total console messages, 1 pre-existing
  unrelated Vite warning).

## Known Defects Found During Exploration

**[MAJOR] Bucket 3-dot-menu "Upload files" does not reset the default Path to bucket root**
— filed as [#649](https://github.com/EliteaAI/elitea-testing-public/issues/649).

Root cause (confirmed via source, `EliteaUI/src/[fsd]/features/artifacts/lib/hooks/
useFileUpload.hooks.js`): `onBucketUpload(bucketName)` (the bucket-menu entry point) only
sets `pendingUploadBucket` — it never resets/ignores the shared `currentPrefix` state.
The dialog's default path is always computed by `computeFullPath()`, which calls
`PathValidationHelpers.computeSecurePath(folderPath, currentPrefix)` using the SAME
`currentPrefix` the toolbar/table upload path (`handleTableUploadRequest`) also uses.
Since `currentPrefix` reflects whatever folder the user is currently browsing —
independent of WHICH ui element (toolbar vs. a specific bucket's own dot-menu) triggered
the upload — the bucket-menu upload silently inherits stale navigation state instead of
defaulting to the bucket root implied by `BucketItem.jsx`'s `handleUploadClick`, which
only ever passes `bucket.name` (no folder) to the handler.

**Isolation proof (this run, 2 controlled passes):** (1) reproduced the bug from a state
where the user had previously navigated into `a1` — Path showed `"{bucket}/a1/"`
(wrong); (2) immediately after, re-selected the SAME bucket at its own root (collapsing
back to `currentPrefix=''`) and repeated the identical entry point — Path correctly
showed `"{bucket}/"` (root-only). This isolates the defect precisely to stale-
`currentPrefix` reuse, not a general breakage of the dialog or the entry point itself.

**Frequency**: Always (2/2) when the precondition holds (user previously navigated into a
subfolder before invoking the bucket-menu upload) — which is exactly this case's own
sequence (options 1/2 navigate into `a1` immediately before option 3 is exercised).

**Not masked**: per `.agents/profile.md` § Bug filing "Never mask" policy, this is an
**isolated** defect (not blocking) — the rest of the case's 45 steps pass cleanly. See
§ Automation Hints for the recommended `expect.soft()` treatment.

Two CLARIFICATIONs (case-text drift, reverse-masking guard applied — NOT defects):
- [#650](https://github.com/EliteaAI/elitea-testing-public/issues/650): case step 26 says
  the bucket-menu shows "Edit"; live product correctly shows "Rename" (same functional
  slot, different label — confirmed intentional via source, `BucketItem.jsx`'s
  `menuItems`).
- [#651](https://github.com/EliteaAI/elitea-testing-public/issues/651): case steps 37-38
  imply a single click on the bucket always expands its subtree; live product's
  `handleSelectBucket` deliberately TOGGLES expand/collapse when the bucket is already
  active (confirmed live: 2 consecutive clicks on an already-active bucket row flip the
  tree's visibility both ways) — intentional UX, not a regression, but non-deterministic
  for a blind single click in automation.

No other console errors or unexpected network behavior observed across the full 46-step
run (0 errors, 14 total console messages).

## Blocked Steps
None. The #649 defect did not block completion of the case — it was worked around (Test
Step 23) so all 46 case steps were verified end-to-end live.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`). Existing
  methods already cover most of the flow (`navigate_to_bucket`, `is_bucket_empty`,
  `upload_files` [toolbar], `open_bucket_menu`, `click_bucket_menu_upload_files_item`,
  `wait_for_upload_path_dialog`, `get_upload_path_prefix_text`,
  `click_upload_path_upload_button`, `wait_for_file_in_tree`, `get_file_row_text`,
  `get_total_file_count_from_pagination`). New method needed: a click handler for the
  CENTER empty-state upload button once its testid is added (e.g.
  `upload_files_via_empty_state(file_paths)`, same `expect_file_chooser()` shape as the
  existing `upload_files()`).
- **#649 recommended treatment**: implement the FULL 46-step flow as written (don't skip
  the buggy assertion), but wrap Test Step 22's Path-value assertion in `expect.soft()`
  against the documented buggy actual value, tagged `# Known defect: #649`, per this
  project's merge-gate "Sanctioned-RED exception" (`.agents/testing.md` § Merge gate) —
  this is precisely the isolated/deterministic/single-cause/open-linked-ticket shape that
  exception exists for. Then apply Test Step 23's workaround (clear the Path field) so
  every downstream step (24-37) can still be verified against a clean, defect-free state.
  Do NOT skip/xfail the whole test — only the one narrow assertion.
- **Step 37/38 (#651) deterministic sequencing**: a single blind click on an already-active
  bucket row is NOT reliable (toggles based on prior state). Recommended approach: after
  the click, check whether `artifacts-tree-item-a1/` is visible; if not, click the bucket
  row a second time. Alternative: bypass the ambiguity by using
  `navigate_to_bucket_folder(bucket_name, "a1")` directly for reaching the folder-selected
  precondition state, and only use the raw click-toggle sequence to specifically exercise
  the toggle behavior itself as its own assertion (not as a means to reach a state).
- **Breadcrumb assertions (steps 11/26/31/35)**: until the `artifacts-breadcrumb-bucket-
  label`/`artifacts-breadcrumb-folder-label` testids are added, there is no compliant
  handle — these steps are blocked at `testid needed:` status, not directly automatable
  today. Do not substitute a text-content scan of `main` as a workaround (violates the
  testid-only policy); wait for the implementer to add the testids via `add-data-testid`
  first.
- **Selected/highlighted-state assertions (steps 38/40)**: same — blocked on the
  `data-selected` attribute addition. Do not substitute a CSS-class or computed-style
  check (unstable, regenerated per build) as a permanent solution.
- Fixtures: `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`) for the bucket;
  `tmp_path` for all three files, reusing `_minimal_png_bytes()` from
  `test_artifacts_upload_duplicate_cancel.py:75-91` for the PNG.
- Wait strategy: file-chooser waits (`expect_file_chooser()`) and upload PUT waits
  (`page.wait_for_response()` / `expect_response()`) both already established in this page
  object — no new wait pattern needed. Toast assertion: `expect(success_toast_message).
  to_be_visible()` immediately after the Upload click, per ELITEA-1826's established
  precedent (auto-retrying `expect()`, never a single-shot read or fixed sleep).
- Viewport: set ≥1600×900 (or otherwise confirm) before asserting the "Last update"
  timestamp column, same finding as ELITEA-1808/1826.
- Suggested test file:
  `automation/tests/ui/artifacts/test_artifacts_upload_three_options_verify_selection.py`.
