# Test Case: Artifacts File List — Sort files by Name / Type / Size / Last update column headers

## Metadata
- **TMS ID**: GAP-035 (coverage-gap campaign `cov60` card, not an onetest case —
  source: `.agents/automation-board/batches/cov60/cases/GAP-035/source.md`)
- **Linked Story**: none (no `EliteaAI/elitea-testing-public` tracking issue exists
  yet for GAP-035 — checked via the real-time issue list, not `--search`, per
  `.agents/test-automation.yaml` § intake dedup rule: zero hits)
- **Priority**: l3 (medium — source case frontmatter `priority: medium`, per
  `spec-format.md`'s `1`=critical/`2`=high/`3`=medium/`4`=low mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / id `399`). Every
  provenance claim below was verified against a **fresh `git fetch origin`** run
  in `../EliteaUI` immediately before this run (output: fast-forward, no new
  commits — `automation/testids` already current with `origin/automation/testids`).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot, 2026-07-24
- **Status**: **ready-for-automation** — case executed end-to-end live, all 10
  numbered steps observed and pass exactly as specified (ascending/descending
  toggle on all four sortable columns, correct per-field comparator, cleanup
  verified). No product defect found. One `testid needed:` gap (all four column
  headers currently carry zero `data-testid`) blocks policy-compliant automation
  until the implementer wires it — but the fix is a **single-line, zero-risk
  addition** using a mechanism that already exists and is already proven in
  production on `automation/testids` (see § Concrete Handles) — an additive,
  well-precedented change, not an environment/access/data blocker, so this does
  **not** downgrade the status to `blocked`.

## Overlap check vs existing automation

`automation/pages/artifacts_page.py` (grepped in full for `sort`) and every file
under `automation/tests/ui/artifacts/` were checked for any existing exercise of
the column-header sort feature. Zero hits beyond incidental Python-side
`sorted()` calls used for *assertion convenience* in two unrelated ZIP-download
tests (`test_artifacts_download_all_files_select_all_zip.py:373`,
`test_artifacts_download_multiple_files_zip.py:201`) — neither clicks a column
header or asserts `sortConfig`/row-reorder behavior. No existing spec creates a
bucket-scoped `useTableSort`/`GridTableHeader` interaction at all.

Verdict: **zero behavioral overlap** — this is a wholly fresh scenario.
`ready-for-automation`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists that the user can upload to and delete from — **created by the
  test itself** in setup (see § Test Data), not a literal pre-existing fixture.
  Same established convention as ELITEA-1808/1832/1839/1809: the case's
  `gap035-sort` name is a case-text placeholder, not a name to hardcode
  verbatim (confirmed live: no bucket named exactly `gap035-sort` existed among
  this project's 367 pre-existing `Private`-project buckets at run start, and the
  bucket this analyst run created+deleted did not collide with anything).
- At least 3 files that differ by name, type, size, **and** last-modified time.
  **Confirmed live via direct API probe (`GET
  https://dev.elitea.ai/artifacts/s3/{bucket}?project_id=399&format=json` against
  an unrelated, pre-existing bucket with 270 files) that S3 `lastModified`
  values are ISO-8601 with milliseconds always `.000` — i.e. real
  **whole-second** resolution.** Three uploads issued back-to-back with no
  deliberate spacing risk landing in the same second and producing a
  backend-ambiguous "Last update" tie (the pre-sort row order would then fall
  back to whatever order the S3 listing API returns, not true chronological
  order) — see § Automation Hints for the concrete mitigation this requires.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the existing `artifact_bucket` pytest fixture
  (`automation/fixtures/data_fixtures.py:454`) — function-scoped, creates a
  uniquely-named bucket via `ArtifactAPI.create_bucket()` and deletes it via
  `ArtifactAPI.delete_bucket()` in teardown. Do **not** hardcode `gap035-sort`.
  Since this case's OWN Step 10 ("delete the bucket, verify removal") IS one of
  the numbered assertions, drive the deletion through the **UI** (bucket-row
  3-dot menu → Delete → confirm) inside the test body, not solely through the
  fixture's API teardown — let the fixture's teardown be a redundant safety net
  in case the UI deletion assertion fails mid-test, exactly the "belt and
  braces" pattern other artifacts AFS's use for a case's own delete-flow step.
- **3 files, seeded via `ArtifactAPI.upload_file(bucket_name, key, content,
  content_type=...)`** (`automation/api/client.py:1282`) — confirmed live this
  run (matching ELITEA-1840/1839's established finding) that this is the same
  `PUT /artifacts/s3/{bucket}/{key}` endpoint the browser itself calls, so
  seeding this way is indistinguishable from a real UI upload as far as the file
  list / sort behavior is concerned:
  - `alpha.txt` — small, `content_type="text/plain"`, e.g. `b"a" * 50` (this run
    used a 49-byte real text file and it rendered as `Text` / `49 B`)
  - `beta.csv` — medium, `content_type="text/csv"`, sized so the numeric byte
    count is unambiguously between the other two (this run used ~26 KB)
  - `gamma.json` — large, `content_type="application/json"`, sized so the
    numeric byte count is unambiguously the largest (this run used ~156 KB)
  - Exact byte sizes are NOT load-bearing (no size-equality assertion) — only
    the **strict ordering** `alpha < beta < gamma` by size matters, confirmed by
    this run's actual values (49 B < 26.1 KB < 155.7 KB).
  - **File-type labels are name-derived, not content-derived** — confirmed via
    `getFileTypeName()` in `ArtifactTable.jsx` rows-mapping: `.txt`→`Text`,
    `.csv`→`CSV`, `.json`→`JSON`. Do not rename these three extensions or the
    Type-column assertions (`CSV` < `JSON` < `Text` ascending) stop holding.
  - **Upload the three with a real, deliberate gap between each `upload_file()`
    call** — see § Automation Hints for the exact mechanism and why a plain
    back-to-back loop is unsafe given the confirmed whole-second S3 timestamp
    resolution above.

No `reuse-existing` fixture applies — same reasoning as every other sibling
artifacts AFS: a bucket in this specific timestamp-ordered state isn't safe to
share across parallel/serial runs.

## Test Steps

1. Create the bucket and upload the three files (see § Test Data — via
   `artifact_bucket` fixture + `ArtifactAPI.upload_file()`, spaced). Navigate to
   the bucket in the UI.
   - **Verify**: the three files appear in `artifacts-file-list` as
     `artifacts-file-row` rows (`ArtifactsPage.get_file_names()` returns exactly
     `["gamma.json", "beta.csv", "alpha.txt"]`, most-recently-uploaded first).
   - **Verify**: default sort is **Last update, descending** (`gamma.json` —
     newest upload — first; `alpha.txt` — oldest — last). Confirmed live: this
     matches `ArtifactTable.jsx`'s `useTableSort({ defaultField: 'modified',
     defaultDirection: 'desc', ... })` exactly, and the "Last update" header
     renders in its active/bold state on initial load with no click needed.
2. Click the **Name** column header.
   - **Verify**: rows reorder to `["alpha.txt", "beta.csv", "gamma.json"]`
     (ascending, case-insensitive string compare — confirmed live).
   - **Verify**: the Name header cell is now the active one (see § Concrete
     Handles — asserted via the header cell's own computed `opacity`, not a new
     selector).
3. Click the **Name** header again.
   - **Verify**: rows reorder to `["gamma.json", "beta.csv", "alpha.txt"]`
     (descending — confirmed live; this is the asc→desc toggle branch of
     `useTableSort`'s `handleSort`).
4. Click the **Size** column header.
   - **Verify**: rows reorder to `["alpha.txt", "beta.csv", "gamma.json"]`
     (ascending by **numeric** byte size via `SortComparators.fileSize` —
     confirmed live this run: the displayed size TEXT sorts differently
     lexically than numerically — `"155.7 KB"` < `"26.1 KB"` < `"49 B"` as raw
     strings, but the app's actual ascending order was `49 B` < `26.1 KB` <
     `155.7 KB`, proving the comparator is genuinely numeric, not a lexical
     string compare on the displayed label).
5. Click the **Size** header again.
   - **Verify**: rows reorder to `["gamma.json", "beta.csv", "alpha.txt"]`
     (descending — largest first).
6. Click the **Last update** column header.
   - **Verify**: rows reorder to `["alpha.txt", "beta.csv", "gamma.json"]`
     (ascending — oldest upload first — via `SortComparators.date`, a real
     `Date.getTime()` compare per `sortComparators.js:30-37`, confirmed by
     reading the source; the source-code read is the ground truth here, not
     only the display text, since the displayed `dd-MM-yyyy, hh:mm a` format has
     no seconds and this run's `alpha`/`beta` both display the identical
     `"04:25 AM"` minute — the sort still correctly orders them because the
     underlying raw ISO timestamp differs at the seconds level, which the
     comparator reads, not the display string).
7. Click the **Last update** header again.
   - **Verify**: rows reorder to `["gamma.json", "beta.csv", "alpha.txt"]`
     (descending — newest first).
8. Click the **Type** column header.
   - **Verify**: rows reorder to `["beta.csv", "gamma.json", "alpha.txt"]`
     (ascending by file-type label: `CSV` < `JSON` < `Text`).
9. Click the **Type** header again.
   - **Verify**: rows reorder to `["alpha.txt", "gamma.json", "beta.csv"]`
     (descending: `Text` < `JSON` < `CSV` reversed → `Text`, `JSON`, `CSV`).
10. Delete the bucket via its 3-dot menu → Delete → confirm
    (`bucket-menu-{name}-menu-button` → `bucket_menu_delete_menuitem` →
    `delete-confirm-button`, all pre-existing `LocatorDescriptor`s on
    `ArtifactsPage`).
    - **Verify**: success toast "The `{bucket}` bucket has been successfully
      deleted." appears (`toast-message`).
    - **Verify**: the bucket no longer appears in the bucket list (confirmed
      live via the search-filtered "No buckets found" state and the bucket-count
      footer decrementing by exactly 1).

## Expected Results
- Every sortable header (Name, Type, Size, Last update) reorders the file list
  ascending on first click, descending on second click.
- Size uses numeric file-size ordering; Last update uses real date ordering —
  neither is a lexical string compare on the displayed text.
- The clicked header shows the active state (confirmed via computed `opacity`
  on the header-cell testid element itself — see § Concrete Handles).
- Test bucket and its files are fully cleaned up; no orphaned bucket remains.
- No console errors during any interaction (spot-checked after several of the
  sort clicks in this run — see § Automation Hints for a caveat on this
  tool's capture scope).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| desc: correct comparator per field (string, file-size, date) | comparator matches the field's real data type, not lexical | steps 2–9 | `step 4`/`step 6`: numeric/date vs lexical distinction explicitly checked | asserted |
| desc: folders and files sorted within their own groups | folder rows and file rows never interleave when sorted | — | — | **out-of-scope** — the case's own Test Data (3 files, no folder) never exercises this; `ArtifactTable.jsx`'s `sortedRows` memo (line 215-226) does implement a separate folders/files partition-then-concat, confirmed by reading the source, but this case supplies no folder to observe it live against |
| 1 Create bucket + upload 3 files | files appear, default sort = Last update desc | step 1 | `step 1`: `get_file_names()` order + active-header check | asserted |
| 2 Click Name header | ascending by name, active/ascending indicator | step 2 | `step 2`: row order + header opacity | asserted |
| 3 Click Name again | descending by name | step 3 | `step 3`: row order | asserted |
| 4 Click Size header | ascending by numeric size | step 4 | `step 4`: row order (lexical-vs-numeric proof) | asserted |
| 5 Click Size again | descending by numeric size | step 5 | `step 5`: row order | asserted |
| 6 Click Last update header | ascending by date (oldest first) | step 6 | `step 6`: row order | asserted |
| 7 Click Last update again | descending by date (newest first) | step 7 | `step 7`: row order | asserted |
| 8 Click Type header | ascending by type label | step 8 | `step 8`: row order | asserted |
| 9 Click Type again | descending by type label | step 9 | `step 9`: row order | asserted |
| 10 Delete bucket | bucket + files removed, list no longer shows it | step 10 | `step 10`: toast + bucket-count decrement + absence in filtered search | asserted |
| Pass/Fail: "all steps complete without errors" | no errors | steps 1–10 | console check each step (see caveat) | asserted |
| Pass/Fail: "test bucket and files fully cleaned up" | bucket gone | step 10 | step 10 | asserted |

### Axis 2 — Analyst additions

- Verified live (via a direct API probe against an unrelated, pre-existing
  270-file bucket) that S3 `lastModified` truncates to **whole seconds** —
  *added: this is essential automation guidance the case text alludes to
  ("spaced times") but doesn't quantify; without it an implementer could
  plausibly upload all 3 files in the same wall-clock second and ship a test
  that only passes by accident of listing order.*
- Verified the Size-column ascending order does **not** match the lexical
  string order of the displayed size text — *added: directly proves the
  `fileSize` comparator is numeric, satisfying the Pass/Fail criteria's
  explicit "not lexical" requirement with a concrete counter-example rather
  than an assumption.*
- Read `sortComparators.js` and `useTableSort.hooks.js` source in full to
  confirm the exact toggle semantics (`handleSort`: a click on a NEW field
  always starts ascending; a second click on the SAME field toggles
  asc→desc; a third click on the same field wraps back to asc) — *added:
  the case only ever exercises exactly 2 clicks per column, so the
  third-click wrap-around is out of scope for this case's own assertions,
  but recording it here prevents a future case from assuming desc→desc
  "sticky" behavior that doesn't exist.*
- Confirmed `GridTableHeader.jsx`'s `columnTestIdPrefix` prop mechanism
  already exists and is already proven in production use (the MCP table,
  `DataTable.jsx:446`) on `automation/testids` — *added: de-risks the
  "testid needed" item from a new-component-code change to a proven,
  one-line call-site addition; material to the `ready-for-automation`
  (not `blocked`) classification.*
- Checked console messages after several of the sort-header clicks in this
  run (no errors observed in the windows checked) — *added: standard
  side-channel discipline; see § Automation Hints for a caveat on this
  particular tool's per-invocation capture scope, which the pytest/Playwright
  MCP-based implementation does not share.*

## Cleanup
1. UI-driven bucket deletion is itself Test Step 10 (the case's own subject).
2. `artifact_bucket` fixture teardown (`ArtifactAPI.delete_bucket()`) as a
   redundant safety net if the UI deletion assertion fails mid-test.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this
project's locator policy (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`) is **testid-only, no fallback ladder** —
`LocatorDescriptor(testid=...)` with no `fallback=`/`locator=`. The four
column-header gaps below are specced as `testid needed:` work orders for the
**implementer** to add via `add-data-testid` — **not** self-fixed by this
analyst pass.

**Provenance verified freshly this run**: `cd ../EliteaUI && git fetch origin`
(fast-forward, no new commits) run immediately before checking, then `git grep`
against both `origin/main` and `origin/automation/testids` for every testid
below.

| Element | testid | Status | Provenance | Notes |
|---|---|---|---|---|
| File list container | `artifacts-file-list` | existing | **on-main ✓** | already an `ArtifactsPage` locator |
| File row | `artifacts-file-row` | existing | **on-automation/testids only** | already an `ArtifactsPage` locator |
| Folder row | `artifacts-folder-row` | existing | **on-automation/testids only** | not used by this case (no folder) |
| "+ Artifact Bucket" button | `artifacts-create-bucket-button` | existing | **on-main ✓** | not directly used (bucket seeded via API) but present if a UI-fallback path is ever needed |
| Search buckets button | `artifacts-search-buckets-button` | existing | **on-main ✓** | used to verify post-delete absence (Step 10) |
| Upload path "Upload" button | `artifacts-upload-path-upload-button` | existing | **on-automation/testids only** | confirms the API-seeded files match the same upload pipeline the UI uses; not clicked by this test (files seeded via API) |
| Bucket row (dynamic) | `BUCKET_MENU_BUTTON` / `artifacts-bucket-row-{}` templates already in `artifacts_page.py` | existing | **on-automation/testids only** | reused as-is for Step 10's bucket menu |
| Delete-confirmation "Delete" button | `delete-confirm-button` | existing | **on-automation/testids only** | reusable app-wide; already `ArtifactsPage.delete_confirm_button` |
| Success/error toast (generic) | `toast-message` | existing | **on-main ✓** | already `ArtifactsPage.success_toast_message` |
| **Name column header** | `artifacts-column-header-name` | **testid needed** | **needs-adding** (exists nowhere — confirmed via fresh `git grep` on both refs) | see mechanism note below |
| **Type column header** | `artifacts-column-header-fileType` | **testid needed** | **needs-adding** | field name is `fileType` (camelCase), NOT `type` — the resulting testid literally interpolates `column.field` |
| **Size column header** | `artifacts-column-header-size` | **testid needed** | **needs-adding** | |
| **Last update column header** | `artifacts-column-header-modified` | **testid needed** | **needs-adding** | field name is `modified`, NOT `lastUpdate`/`last-update` |

**Mechanism note (why this is a trivial, proven addition, not new component
work):** `GridTableHeader.jsx` (the shared component `ArtifactTable.jsx`
already renders) **already destructures and wires a generic
`columnTestIdPrefix` prop** (`data-testid={columnTestIdPrefix ?
\`${columnTestIdPrefix}-column-header-${column.field}\` : undefined}`,
confirmed live on `origin/automation/testids` — absent on `origin/main`
entirely, confirmed via `git show origin/main:.../GridTableHeader.jsx`). This
exact mechanism is **already in production use** by the MCP table
(`src/[fsd]/widgets/data-table/ui/DataTable.jsx:446`:
`columnTestIdPrefix={isMCPs ? 'mcp-table' : undefined}`). The ONLY missing
piece for this case is wiring the same prop at `ArtifactTable.jsx`'s own
`<GridTableHeader ...>` call site (currently passes `columns`, `sortConfig`,
`onSort`, `onSelectAll`, `isAllSelected`, `isIndeterminate`,
`gridTemplateColumns`, `selectAllCheckboxTestId` — but not
`columnTestIdPrefix`) — i.e. `add-data-testid` here is a **one-line prop
addition** (`columnTestIdPrefix="artifacts"`), not new JSX/component code.
This is exactly what the case's own "Automation Notes" section already
specifies.

**Side-effect to note, not a scope violation:** `columnTestIdPrefix`, once
wired, generates a testid for **every** column in `ARTIFACT_COLUMNS`
including the non-sortable `Actions` column (`artifacts-column-header-actions`)
— the JSX ternary that sets `data-testid` does not gate on `column.sortable`.
This case's test references exactly the 4 sortable-column testids and never
references `artifacts-column-header-actions`; the extra testid is an
inherent, all-or-nothing side effect of the shared component's existing
mechanism (the MCP table's own `columnTestIdPrefix` usage has the identical
property), not a new choice by this case's implementer to testid an
untouched element — flagging so the reviewer doesn't mis-flag it as a scope
violation under `.agents/role-overrides.md` § locator scope.

**Active-header-state assertion — no new selector needed.** The header
cell's own `sx={styles.headerCell(isActive, ...)}` sets `opacity: isActive ?
1 : 0.7` on the SAME Box element that carries the (once-wired) testid — so
Step 2/4/6/8's "header shows active state" is asserted by reading that
element's own computed `opacity` (`getComputedStyle`/Playwright
`evaluate`), not by adding any new selector or chaining a raw CSS locator off
the testid'd parent (which would violate the "never chain a raw selector off
an existing field" hard rule with no `#579` exception available — the
`SortArrows` icon is an app asset, not third-party). **Do not** attempt to
assert the SortArrows rotation/direction indicator — that WOULD require a new
raw selector chained off the header-cell testid (the icon has no testid of
its own and is not eligible for a `#579` scoped exception since it isn't
third-party); the Pass/Fail criteria doesn't require it, and the row-order
assertion already fully proves ascending vs descending.

## Network Behavior
- API-seeded uploads: `PUT /artifacts/s3/{bucket}/{key}?project_id=399` (same
  endpoint the UI's own upload flow calls — confirmed via ELITEA-1840's prior
  network capture, reused here).
- Sort-header clicks are **pure client-side re-sorts** — `useTableSort` /
  `sortData` operate on the already-fetched `rows` array in memory; confirmed
  live this run that clicking any header fired **zero** new network requests.
  Do not wait on a network condition after a header click — wait on the DOM
  row-order change instead (Playwright's own auto-retrying assertions on
  `get_file_names()`'s result are sufficient; no `wait_for_response` needed
  here, unlike most other Artifacts flows).
- Bucket delete: `DELETE` request via the existing bucket-menu-delete flow
  (already exercised and network-verified by ELITEA-1809/1817's sibling AFS's;
  not re-verified in detail by this run since Step 10 reuses those exact
  existing page-object methods as-is).

## Known Defects Found During Exploration
None found. All 10 steps reproduced exactly as the case describes on the
first live attempt.

## Blocked Steps
None. (The column-header testid gap is a `testid needed:` work order per
§ Concrete Handles, not a blocker — see § Metadata Status rationale.)

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`); page object
  `automation/pages/artifacts_page.py` (extend, don't duplicate) — add 4 new
  `LocatorDescriptor` class fields (`name_column_header`, `type_column_header`,
  `size_column_header`, `last_update_column_header`, each
  `testid="artifacts-column-header-{field}"`) plus a thin
  `click_column_header(locator)` / reuse-as-is-per-field helper. **Do not**
  build a dynamic `{}`-template constant for these four — they are a fixed,
  enumerable set (not runtime-parameterized data), so four static
  `LocatorDescriptor` fields is the correct shape, not
  `ARTIFACTS_COLUMN_HEADER = '[data-testid="artifacts-column-header-{}"]'`.
- Reuse `ArtifactsPage.get_file_names()` (`artifacts_page.py:1244`) as the
  PRIMARY sort-order assertion after every header click — it already returns
  file names in DOM/visual order, exactly what's needed to assert
  `["alpha.txt", "beta.csv", "gamma.json"]`-style expected sequences. No new
  row-reading method needed.
- **Upload spacing — concrete mechanism.** Given the confirmed whole-second S3
  `lastModified` resolution (§ Preconditions), space the three
  `ArtifactAPI.upload_file()` calls so each lands in a strictly later second
  than the last. Two compliant approaches, either acceptable:
  1. **Condition-based** (preferred, matches the project's no-fixed-sleep
     spirit): after each upload, call `ArtifactAPI.get_file_metadata()`
     (`client.py:1318`, already returns `lastModified`) and loop
     (`time.sleep(0.1)` micro-poll) until the wall clock's current second
     differs from the just-uploaded file's `lastModified` second before
     issuing the next upload.
  2. **Fixed, justified delay**: a plain `time.sleep(1.1)` between each of the
     3 upload calls, with a code comment citing this AFS's confirmed
     whole-second S3 timestamp resolution. This is test-data setup asserting
     real backend timestamp uniqueness, not a UI-synchronization wait, so it
     is a scoped, justified exception to the general "no sleep" convention —
     call this out explicitly in the test's docstring/comment so a future
     reader doesn't mistake it for an ordinary anti-pattern.
- Sort-header clicks need **no network wait** (see § Network Behavior) — a
  plain `.click()` + Playwright's own auto-retrying assertion on
  `get_file_names()` is sufficient; do not add a `wait_for_response` or a
  fixed timeout here.
- **Tool-capture caveat (this analyst's own tooling, not the pytest
  framework):** this run used `browser-verify`'s CDP-based CLI, where each
  shell invocation opens/closes its own short-lived CDP session — console and
  network capture is therefore scoped to that single command's connection
  window, not the whole exploration. The pytest/Playwright-MCP-based
  implementation does not share this limitation (`page.on("console", ...)`
  persists for the whole test), so the implementer's own console-error
  assertions should cover the full test lifecycle, not just spot windows —
  don't treat this run's "no errors observed in the windows checked" as
  equivalent to a persistent for the whole flow.
- **Viewport width**: keep the default 1366×768 (headless) / window-fit
  (headed) viewport. `ARTIFACT_COLUMNS`'s `hideBelow` breakpoints collapse
  Type at <550px, Size at <700px, Last update at <900px — all comfortably
  below the project's default viewport, but worth a one-line comment in the
  test so a future viewport change doesn't silently break 3 of the 4 sort
  assertions by hiding their columns instead of failing loudly.
- Browser lane note (analyst-side, not implementer-relevant): the shared
  Playwright MCP browser (lane 0) was occupied by a concurrent process at the
  start of this run (`Browser is already in use for
  .../mcp-chrome-70a4838`) — this analysis was run instead via `browser-verify`
  on a fully isolated Chrome instance (own `--remote-debugging-port=9455`, own
  `--user-data-dir=/tmp/gap035-chrome-profile`), confirmed single-target via
  `list-targets` before driving it. No contamination risk to lane 0 or to any
  other concurrent analyst.
