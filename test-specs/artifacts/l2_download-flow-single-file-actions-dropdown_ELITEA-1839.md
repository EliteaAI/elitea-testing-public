# Test Case: Download Flow – Download Single File via Actions Dropdown

## Metadata
- **TMS ID**: ELITEA-1839
- **Linked Story**: [EliteaAI/elitea-testing-public#211](https://github.com/EliteaAI/elitea-testing-public/issues/211) (tracking issue)
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399). Every code
  citation below was verified against a **fresh `git fetch origin`** in `../EliteaUI`
  and confirmed present on `origin/main` too (not just `automation/testids`) —
  provenance recorded per-handle in § Concrete Handles.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end **twice**
  (2/2 identical runs, fresh page navigation each run), all 10 case steps pass,
  no product defects found. Not already-covered and not extend-existing — see
  § Overlap check below. Two `testid needed:` gaps block full policy-compliant
  automation of the dropdown's menu-item click and the "no ZIP dialog" assertion
  until the implementer adds them (see § Concrete Handles) — this does **not**
  downgrade the status to `blocked`: the gaps are additive, well-precedented
  frontend changes (same mechanism already used elsewhere in this app), not an
  environment/access/data blocker.

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_multi_file.py`
(`TestArtifactMultiFileDownload`, ELITEA-1327) and `automation/pages/artifacts_page.py`
were read before this run. That test is a **data-loss regression check** (an agent
creates 6 files across bucket root + a sub-path in one tool call; the test verifies
none of the 6 are silently lost) that happens to call the existing
`ArtifactsPage.download_file(filename)` twice as a throwaway "spot-check the
mechanism still works" step, nested deep inside a much larger agent-chat flow. Its
only assertion on the download itself is `path.stat().st_size > 0`. It never
asserts: the dropdown shows exactly "Download" + "Delete", immediate-no-ZIP
semantics, absence of a progress modal, or exact downloaded-filename equality.

Verdict: **zero behavioral overlap** with ELITEA-1839 (the single-file
dropdown-**download UX contract** itself — menu content, immediacy, no ZIP
packaging, filename fidelity, content integrity) vs ELITEA-1327 (data isn't lost
across a multi-file agent write). The two tests exercise the same UI *action*
(clicking Download in the dot-menu) but assert **disjoint observables** — the
same distinction sibling case ELITEA-1832 drew against this same legacy test.
Fresh scenario, `ready-for-automation`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing a subfolder with exactly one file in it.
  **This bucket does not pre-exist as a stable fixture — `bucket-1`/`a1` are
  case-text placeholders**, not literal fixture names. Confirmed by the sibling
  ELITEA-1832 run (searched all 5 available projects live, including the in-app
  "Search buckets" feature for the literal string `bucket-1` — zero matches
  anywhere) and re-confirmed in this run: the same `bucket-1` name still does not
  exist in any project.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the existing `artifact_bucket` pytest fixture
  (`automation/fixtures/data_fixtures.py:455`) — function-scoped, creates a
  uniquely-named bucket via `ArtifactAPI.create_bucket()` and deletes it via
  `ArtifactAPI.delete_bucket()` in teardown. Do **not** hardcode `bucket-1`.
- **Subfolder + file**: seed `a1/sample.txt` directly via
  `ArtifactAPI.upload_file(bucket_name, "a1/sample.txt", content, content_type="text/plain")`
  (`automation/api/client.py:1282`) — **confirmed live in this run**: uploading to a
  nested key auto-creates the `a1` folder node in both the left-panel bucket tree
  and the right-panel breadcrumb; no separate "create folder" call exists or is
  needed. This is faster and browser-independent vs. driving the upload UI.
- **Content constant**: use a small, fixed byte string as both the seed content
  AND the "not corrupted" comparison baseline (content-equality is a strictly
  stronger signal than `size > 0` — this run used
  `b"Sample content for ELITEA-1839 download test.\n"`, 46 bytes, confirmed
  byte-identical between the seeded upload and the downloaded file across both
  runs).

No `reuse-existing` fixture applies — same reasoning as ELITEA-1832: a bucket in
this specific state (exactly one file, inside a named subfolder) isn't safe to
share across parallel/serial runs.

## Test Steps

1. Navigate directly to `${BASE_URL}/artifacts?bucket={bucket_name}&folder=a1`
   (folds case steps 1–2: Artifacts page load + bucket-and-subfolder selection
   into one navigation).
   - **Verify**: right-panel breadcrumb shows `{bucket_name} > a1`; file table
     shows exactly one row, `sample.txt`, `"1 - 1 of 1"` pagination — confirmed
     live via `.playwright-mcp/page-2026-07-19T01-13-04-455Z.yml` and screenshot
     `ELITEA-1839-step3-file-row-before-hover.png`.
   - **Note (technique, not a case requirement)**: this is more reliable than
     `navigate_to_bucket()` + a separate `navigate_into_folder()` left-panel-tree
     click (ELITEA-1832's own reasoning for preferring direct URL nav over
     left-panel clicks) — confirmed live the `folder` query param composes with
     `bucket` in a single navigation.
2. Verify `sample.txt` is listed with correct Type ("Text") and Size ("46 B" in
   this run — matches the exact byte count of the seeded content) (case step 3).
3. Locate the dot-menu trigger for `sample.txt` via the dynamic testid
   `artifact-actions-sample.txt-menu-button` and click it (case step 4).
   - **Verify**: dropdown menu opens showing **exactly two** items, "Download"
     and "Delete" (case step 5) — confirmed live via
     `page.evaluate` reading `[role="menuitem"]` text content:
     `["Download", "Delete"]`, and screenshot `ELITEA-1839-step4-5-dropdown-open.png`.
   - **Drift note (not a defect)**: the trigger button is visible (`opacity: 1`,
     in the accessibility tree, not hover-gated) BEFORE any hover in the current
     live app — confirmed via `browser_evaluate` computed-style check
     (`offsetParent !== null`, `opacity: "1"`). This contradicts the existing
     legacy `ArtifactsPage.download_file()` method's own docstring/comment
     ("hidden until row is hovered" + a 500ms CSS-transition wait). Do not carry
     that hover-then-wait assumption into this case's implementation; a bare
     click on the testid suffices. (Whether the legacy method's comment is stale
     or ELITEA-1327's flow differs is out of this case's scope — not changed
     here.)
4. Click "Download", wrapped in `page.expect_download()` with a short timeout
   (case step 6).
   - **Verify**: the download event fires **immediately** — no intervening
     "Preparing ... .zip" dialog, no progress modal (case steps 7 + 10, folded —
     same observable, confirmed by the same screenshot). Confirmed live 2/2 runs:
     screenshot taken immediately after the click
     (`ELITEA-1839-step6-7-10-immediate-download-no-dialog.png`) shows the
     dropdown closed, file table unchanged, **zero** dialog/modal elements
     present.
5. Verify `download.suggested_filename == "sample.txt"` exactly (case step 8).
   - Confirmed live 2/2 runs: `Downloaded file sample.txt to ".playwright-mcp/sample.txt"`.
6. Verify the downloaded file's bytes are byte-identical to the seeded content
   constant (case step 9 — "accessible and not corrupted").
   - Confirmed live 2/2 runs: downloaded file = 46 bytes,
     `cat`-verified content `"Sample content for ELITEA-1839 download test.\n"`,
     matching the seed exactly both times.
7. *(Axis 2 addition)* Verify no NEW console errors attributable to this flow.
   - Confirmed live 2/2 runs: 0 errors both times. The only console entry present
     (both runs) was a pre-existing, unrelated Vite module-externalization
     warning (`stream.Stream` / `@eigenpal_docx-js-editor.js`) — present on page
     load regardless of this flow, not caused by it.

## Expected Results
- Clicking the dot-menu trigger for a single file shows a menu with exactly
  "Download" and "Delete" — no other items.
- Clicking "Download" starts the browser download **immediately**: no ZIP
  packaging, no "Preparing ... .zip" dialog, no progress modal — confirmed via
  the underlying request itself:
  `GET /api/v2/artifacts/artifact/default/{project_id}/{bucket}/{url-encoded-key}`
  → `200 OK`, fired the instant "Download" is clicked (§ Network Behavior).
- The downloaded file's suggested filename is exactly `sample.txt` (the base
  name, not the full `a1/sample.txt` key).
- The downloaded file's content is byte-identical to what was uploaded — not
  corrupted.
- No console errors during the flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket "bucket-1" with subfolder "a1" containing "sample.txt" | Precondition state exists | Test Data + Test Step 1 | Fresh bucket + subfolder seeded via `ArtifactAPI.upload_file`; precondition state proven by Test Step 2's `file_exists(sample.txt)` + `get_total_file_count_from_pagination() == 1` — the implementation parses only the pagination label's total-count suffix (`"of N"`), not the literal `"1 - 1 of 1"` string the analyst observed live | asserted |
| Step 1: Navigate to Artifacts section | Artifacts page loads | Test Step 1 | No direct assertion inside Test Step 1 itself (pure navigation, no `expect()`/assert) — page-load success is proven indirectly via Test Step 2's `file_exists(sample.txt)` + `file_count == 1` proxy; zero breadcrumb assertion exists anywhere in the shipped test (confirmed via `grep -in breadcrumb` → no hits) | asserted *(proxy assertion in Test Step 2, not a literal breadcrumb/page-load check)* |
| Step 2: Click bucket-1, navigate to subfolder a1 | Subfolder a1 selected | Test Step 1 | Implementation asserts via Test Step 2's `file_exists(sample.txt)` + `file_count == 1` proxy, not a literal breadcrumb assertion — `sample.txt` exists only under `{bucket}/a1`, so this equally proves correct-folder-landing (breadcrumb text was observed live during analyst exploration but not carried into the implemented assertion) | asserted *(decomposed — folded into one direct navigation; proxy assertion, not breadcrumb)* |
| Step 3: Verify file table shows sample.txt | sample.txt visible | Test Step 2 | `file_exists(sample.txt)` (row present) + `get_total_file_count_from_pagination() == 1` — Type ("Text") and Size ("46 B") are NOT asserted anywhere in the shipped test; those were analyst-observed live values not carried into the implementation | asserted *(file-presence + count only — Type/Size not checked in code)* |
| Step 4: Hover row, click 3-dot actions icon | Dropdown menu appears | Test Step 3 | Menu opens after click on `artifact-actions-sample.txt-menu-button` | asserted *(hover not required live — see Test Step 3 drift note)* |
| Step 5: Verify dropdown shows Download + Delete | Both options visible | Test Step 3 | `expect(download_menu_item).to_be_visible()` + `expect(delete_menu_item).to_be_visible()` — two independent visibility checks, not an exact list-match of menu contents (would still pass if an unexpected third menu item were present); the analyst's live `[role="menuitem"]` text-content check (`["Download", "Delete"]`) was the exploration-time proxy, not the shipped assertion | asserted *(two independent visibility checks — weaker than an exact-list match)* |
| Step 6: Click Download | File download initiates | Test Step 4 | `page.expect_download()` fires | asserted |
| Step 7: Verify download starts immediately, no ZIP | No ZIP-prep dialog | Test Step 4 | `expect(artifacts_page.zip_download_progress_dialog).to_have_count(0, timeout=DIALOG_ABSENCE_TIMEOUT)` — a defensive/regression guard (the dialog is architecturally unreachable from this download path, per AFS); the analyst's live screenshot evidence (zero dialog elements observed 2/2 runs) was the exploration-time proxy, not the shipped assertion mechanism | asserted *(decomposed — same observable as step 10, folded)* |
| Step 8: Verify downloaded filename matches sample.txt | Filename = "sample.txt" | Test Step 5 | `assert download.suggested_filename == FILE_NAME` — matches the analyst's live confirmation (2/2 exploration runs) | asserted |
| Step 9: Verify file is accessible and not corrupted | Content intact | Test Step 6 | `assert downloaded_bytes == FILE_CONTENT` (byte-identical content vs. seed) — matches the analyst's live confirmation (2/2 exploration runs) | asserted |
| Step 10: Verify no progress modal/zip dialog for single file | No progress modal | Test Step 4 | Same evidence as step 7 (folded) | asserted |
| Expected Final State: immediate download, no ZIP, file accessible/not corrupted | Composite pass condition | Test Steps 4–6 | Combination of download-timing, filename, and content-equality checks | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | `assert not console_errors` — a `page.on("console", ...)` listener capturing only `msg.type == "error"` (warnings excluded by type filter, not a special exclusion rule); matches the analyst's live confirmation of a clean console across both exploration runs (one pre-existing, flow-unrelated Vite warning was present but is naturally excluded since it is type "warning", not "error") | asserted |

### Axis 2 — Observables asserted beyond the case
- **Content byte-equality (not just `size > 0`)** — *added: the case's own step 9
  asks for "not corrupted"; a bare size check (the legacy ELITEA-1327 test's
  approach) cannot actually detect truncation/corruption that preserves length.
  Byte-equality against the known seed is the strongest available signal.*
- **Console-message check immediately after Download** — *added: standard
  silent-error guard, consistent with ELITEA-1832's precedent.*
- **2/2 identical reproduction**, each run starting from a fresh page navigation
  (not just a fresh interaction in the same DOM state) — *added: rules out
  session/DOM-state carryover before handing off as `ready-for-automation`.*
- **Bonus, optional, NOT part of the required case steps**: the toolbar bulk
  `artifacts-download-files-button`, when exactly **one** non-folder file is
  checkbox-selected, was confirmed live to ALSO download immediately with no ZIP
  dialog (`ArtifactTable.jsx` `onDownloadFiles`, ~line 399: `if (selectedFiles.length
  === 1 && selectedFiles[0].type !== ARTIFACT_TYPES.FOLDER)` skips
  `startZipDownload` entirely). This means the ZIP-vs-immediate split is a
  **selection-count/type semantic**, not a "dropdown vs. toolbar" semantic — useful
  context for anyone contrasting this case against a future bulk-ZIP-download
  case, but out of THIS case's scope to assert as a required step (no case text
  asks for it). Not added to Test Steps; noted here and in § Automation Hints only.

## Cleanup
1. Delete the seeded bucket via `ArtifactAPI.delete_bucket(bucket_name)` in the
   `artifact_bucket` fixture's own teardown (invoked automatically if that
   fixture is reused). **Known pre-existing defect, already filed
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)):**
   this delete call 404s on both URL-format attempts in the current dev
   environment, so the fixture's teardown silently logs a warning and the
   bucket actually leaks — do not treat "the bucket disappeared" as verified
   just because the fixture ran; this is not new to this case and is out of
   scope to fix here (route any fix to #636, not this case's PR).
2. No other entities are created by this case (no Agent, no Toolkit, no
   Credential).
3. **This exploration run's artifacts** (not part of the automated test): bucket
   `autotest-elitea1839-download-423548` was created via direct API call in the
   `Private` project (id 399) to verify the case live, containing `a1/sample.txt`
   (46 B) at time of hand-off. Left in place — matches existing project
   convention (~84 buckets already present in `Private`, many un-deleted
   `autotest-*` from prior runs); safe for the implementer or lead to delete at
   any time via `ArtifactAPI.delete_bucket("autotest-elitea1839-download-423548")`.
4. Local exploration screenshots (repo root, untracked): 
   `ELITEA-1839-step3-file-row-before-hover.png`,
   `ELITEA-1839-step4-5-dropdown-open.png`,
   `ELITEA-1839-step6-7-10-immediate-download-no-dialog.png` — attached as
   evidence for this AFS; safe to leave per this repo's existing pattern of
   untracked case-evidence screenshots at repo root.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's
locator policy (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`
§ Analyst slot) is **testid-only, no fallback ladder**. An element without a
testid is specced below as `testid needed: {name}` — not softened into a note,
not resolved via role/text. Every row's Provenance was checked against a fresh
`git fetch origin` in `../EliteaUI` (both `origin/main` and `automation/testids`
give identical results for every row below — the gaps are NOT `automation/testids`
drift, they are present on `main` too).

| Element | testid | Provenance | Status | Notes |
|---|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | on-main ✓ | existing | left panel |
| Bucket file list container | `artifacts-file-list` | on-main ✓ | existing | scopes file/folder rows |
| File row | `artifacts-file-row` | on-main ✓ | existing | one per file |
| Folder row (right panel) | `artifacts-folder-row` | on-main ✓ | existing, **not used** by this case | right-panel row; navigation uses direct URL `?folder=` param instead (Test Step 1), not this row nor the left-panel-tree click `navigate_into_folder()` uses |
| Toolbar "Download files" (bulk) button | `artifacts-download-files-button` | on-main ✓ | existing, **not used** by this case's required steps | separate bulk/checkbox-select flow; confirmed live it also skips ZIP for exactly 1 selected file (§ Axis 2) — noted for context only |
| Per-file dot-menu trigger | `artifact-actions-{filename}-menu-button` | on-main ✓ | existing | **dynamic testid**, confirmed live for a file INSIDE a subfolder as `artifact-actions-sample.txt-menu-button` — the value is the **base filename only** (`row.id = item.name` in `ArtifactTable.jsx:167`), never the full path/key, even for nested files. Root-level files use the identical code path (not independently re-verified live in this run, since the case's own precondition is a subfolder file — architecturally guaranteed identical per the shared `existingRows.map()` construction). Follow the project's class-constant templating pattern (`.agents/testing.md` § Locator policy "Dynamic testids") — do NOT inline `get_by_test_id(f"...")` in a method body. |
| **"Download" menu item** | `testid needed: artifacts-file-download-menuitem` | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | Root cause (confirmed live via `document.querySelectorAll('[role="menuitem"]')` — both items' `data-testid` attribute is `null`): `DotMenu.jsx`'s `BasicMenuItem` only renders `data-testid="${testId}-menuitem"` when `testId` (= `item.key`) is truthy; `ArtifactRowActions.jsx`'s `menuItems` array pushes `{label: 'Download', icon, onClick: handleDownload}` with **no `key`**. Fix (additive, well-precedented — the exact mechanism every other `DotMenu` consumer in this app already uses for its own menu items): add `key: 'artifacts-file-download'` to this entry (`ArtifactRowActions.jsx`, `menuItems` useMemo, the `items.push({ label: 'Download', ... })` block) — `DotMenu` auto-derives `data-testid="artifacts-file-download-menuitem"` from it, no other change needed. |
| **"Delete" menu item** | `testid needed: artifacts-file-delete-menuitem` | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | Same root cause and fix mechanism as the Download row above: add `key: 'artifacts-file-delete'` to the `items.push({ label: 'Delete', ... })` block in the same file. This case only needs the Delete item's **visibility** asserted (case step 5) — it is never clicked — so the testid unblocks a compliant visibility assertion, nothing more. |
| ZIP-download progress dialog ("Preparing ... .zip") | `testid needed: artifacts-zip-download-progress-dialog` | **confirmed missing on both `origin/main` and `automation/testids`** | **needs-adding** | `ZipDownloadProgressDialog.jsx`'s `<BaseModal>` (line 56) does not pass the `data-testid` prop `BaseModal` already supports (same mechanism ELITEA-1832 used to add `artifacts-upload-path-dialog` / `artifacts-resolve-duplicates-dialog`). Needed so case step 10 ("no progress modal") can be asserted via a stable handle instead of a raw `[role="dialog"]` check (forbidden — testid-only policy). **Architecturally unreachable from THIS case's own action**: the dropdown's `onDownload` callback (`ArtifactTable.jsx:329`) never calls `startZipDownload` — confirmed via code read, both `origin/main` and `automation/testids`. The assertion is therefore a defensive/regression guard (same rationale as ELITEA-1832's "no success toast" check), not expected to ever fire for this flow — but the case explicitly asks for it (step 10), so per the Analyst-slot override this is specced, not silently dropped. |
| Delete-confirmation dialog's Delete button | `delete-confirm-button` | on-main ✓ (per ELITEA-1832) | existing, **not used** | this case never clicks Delete — visibility-only via the Delete menu item above |

## Network Behavior
- Opening the bucket/subfolder: `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id={id}&format=json`
  → `200 OK`. Fires once per navigation, before the file table renders.
- **The download itself**: `GET {ELITEA_URL}/api/v2/artifacts/artifact/default/{project_id}/{bucket}/{url-encoded-key}`
  → `200 OK`. Confirmed live 2/2 runs, fired the instant "Download" is clicked —
  e.g. `GET /api/v2/artifacts/artifact/default/399/autotest-elitea1839-download-423548/a1%2Fsample.txt`.
  This is the exact same endpoint `ArtifactAPI.get_file()` (`automation/api/client.py`)
  already wraps, so it doubles as an independent-channel cross-check for the
  content-equality assertion (Test Step 6) if the implementer wants a second
  confirmation path beyond the browser download itself.
- **No other network request fires between the "Download" click and the download
  completing** — confirmed live 2/2 runs via `browser_network_requests` filtered
  on `artifact`: exactly one GET, no POST/PUT, no ZIP-related endpoint. This is
  the strongest evidence for "no ZIP packaging happens" (§ Expected Results).
- No console errors either run (one pre-existing, flow-unrelated Vite warning
  present both times — see Test Step 7).

## Known Defects Found During Exploration
None found at the analyst pass (2/2 identical runs). Live product behavior
matched the case's expected behavior exactly: the dropdown shows exactly
Download + Delete, Download fires an immediate single GET with no ZIP
packaging and no progress modal, the downloaded filename is exactly
`sample.txt`, and the content is byte-identical to the seed. No CLARIFICATION
filed either — the case's `bucket-1`/`a1` placeholder naming was already
established as intentional TMS-authoring shorthand by the sibling ELITEA-1832
run, not a case-text drift needing correction.

**Addendum — found during implementation (amended in PR #639 round 2, per
reviewer finding; not present at the analyst pass):** implementing this case's
Test Step 1 direct-URL navigation
(`${BASE_URL}/artifacts?bucket={bucket_name}&folder=a1`) surfaced an
intermittent product race, filed as
[#638](https://github.com/EliteaAI/elitea-testing-public/issues/638) —
*"Artifacts: direct bucket+folder URL navigation can silently land on the
wrong bucket (project-id resolution race)."* On a fresh page load, `Artifacts.jsx`
can still be resolving the selected project id from Redux
(`useSelectedProjectId()`) when the navigation lands; if that resolution
completes a render after mount, a `selectedProjectId !== queryParams.projectId`
effect fires `setSearchParams({})`, silently stripping the `bucket`/`folder`
query params before the auto-select-bucket effect ever reads them. The app
then falls back to the most-recently-used bucket with **no error shown** —
not even the existing "Bucket not found" dialog. Reproduced live ~2/5 local
runs; confirmed present on both `origin/main` and `automation/testids`
(byte-identical `Artifacts.jsx`), so it is not a testids-branch drift.

This is a **navigation/setup-path issue, not one of this case's own required
assertions** — it affects reaching the precondition state (Test Step 1), not
the dropdown/download/content-integrity observables the case actually tests.
Per the No-Defect-Masking rule this is handled as infrastructure, not
suppressed: the shipped test mitigates it test-side in
`ArtifactsPage.navigate_to_bucket_folder()`, which re-checks the live URL's
`bucket` query param after navigating and retries the navigation **exactly
once** (`_retry` flag, no loop) if the param was stripped, logging a
`logger.warning(...)` on the retry path so CI history shows how often the
race actually occurs; if the second attempt also fails to land on the target
bucket it raises `AssertionError` rather than silently proceeding on the
wrong bucket. The underlying application bug remains **open and unfixed** —
this mitigation only keeps the test from failing on the same known race the
real product still has; it does not fix #638.

## Blocked Steps
None. The two `testid needed:` rows in § Concrete Handles are implementer work
items (per `.agents/role-overrides.md` § Analyst slot: "not softened into a MINOR
defect or a note; it is implementer work, and the AFS is its work order"), not
analyst-side blockers — they do not require access, data, or environment fixes,
just an additive `add-data-testid` pass on `ArtifactRowActions.jsx` (one `key`
line each) and `ZipDownloadProgressDialog.jsx` (one `data-testid` prop).

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`). The
  **existing `download_file()` method (lines 480–536) is NOT testid-compliant**
  — it opens the dot-menu via raw CSS (`button[aria-haspopup="true"]`) and clicks
  the item via a raw role locator (`page.get_by_role("menuitem", name="Download")`).
  This is pre-policy tech debt (used by ELITEA-1327's test) — do not copy it into
  this case's implementation, and do not cite it as precedent (`.agents/role-overrides.md`:
  "the surrounding code is NOT precedent"). Once the two menu-item testids land,
  add compliant class-level `LocatorDescriptor`s: a dynamic template constant for
  the dot-menu trigger (e.g. `ARTIFACT_ACTIONS_MENU_BUTTON =
  '[data-testid="artifact-actions-{}-menu-button"]'`, per testing.md's dynamic-testid
  pattern) plus static fields for `artifacts-file-download-menuitem` and
  `artifacts-file-delete-menuitem`. Consider a new method (e.g.
  `download_file_via_dropdown()`) rather than overloading `download_file()` —
  ELITEA-1327's test depends on the current method's behavior/signature and this
  case needs additional assertions (menu-content check, immediate-no-dialog
  timing, exact filename equality) the legacy spot-check doesn't need. Implementer's
  call whether to extend or add.
- The dot-menu trigger is visible without hovering in the current live app
  (Test Step 3 drift note) — do not port `download_file()`'s hover-then-500ms-wait
  sequence into this case's new method; a direct click on the testid is sufficient
  and was confirmed sufficient live, 2/2 runs.
- Fixtures: reuse `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`)
  and `ArtifactAPI.upload_file()` (`automation/api/client.py:1282`) to seed
  `a1/sample.txt` — no browser-driven upload needed, no separate folder-creation
  call needed (confirmed live, § Test Data).
- Navigation: `${BASE_URL}/artifacts?bucket={bucket_name}&folder=a1` in one
  direct navigation is faster and more reliable than
  `navigate_to_bucket()` + `navigate_into_folder()`'s left-panel-tree click
  (confirmed live, Test Step 1) — consider adding an optional `folder` kwarg to
  `navigate_to_bucket()`, or a lighter subfolder-deep-link helper, rather than
  reusing `navigate_into_folder()` (which stays as-is for callers that need the
  actual UI-click path).
- Wait strategy: wrap the "Download" click in `page.expect_download(timeout=...)`
  with a **short** timeout (e.g. 5s, well under the default) — a genuinely
  blocking ZIP-prep flow would exceed it, so the timeout itself is a meaningful
  assertion, not just a wait. Do not add a fixed `page.wait_for_timeout()` — none
  is needed (confirmed live, no animation/settle delay between click and download
  event).
- "Not corrupted" assertion: compare `download.path()`'s bytes to the exact
  seeded content constant (byte-for-byte), not `size > 0` (§ Test Data, § Axis 2).
  Optional second channel: `ArtifactAPI.get_file(bucket_name, "a1/sample.txt")`
  hits the identical endpoint the browser download uses (§ Network Behavior) for
  an independent confirmation.
- Optional follow-up (out of this case's scope): a true ZIP-dialog **positive**
  control (≥2 files or a folder selected via the toolbar bulk-download button)
  would need its own case — this case only proves the single-file dropdown path
  never shows it, not that the ZIP dialog exists and works at all.
