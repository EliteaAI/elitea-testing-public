# Test Case: Create Artifact Bucket with 55-Character Name and Delete It

## Metadata
- **TMS ID**: ELITEA-1817
- **Linked Story**: [EliteaAI/elitea-testing-public#252](https://github.com/EliteaAI/elitea-testing-public/issues/252) (tracking issue)
- **Priority**: l3 (medium — as authored in the source TMS case frontmatter, `priority: medium`;
  maps to `l3` per this folder's established convention, e.g. sibling ELITEA-1809/1832/1868)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch →
  DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399). Dev server confirmed running and
  responsive at run start (`curl` 200). One JSX file was edited directly on `automation/testids` and
  pushed this run — see § Concrete Handles for the exact commit.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live, **2/2 clean runs** (once with
  the case's own literal 55/56-char name, once with a short throwaway name used specifically to
  verify the new Delete-menuitem testid and the dropdown's full-text read), 0 console errors either
  run (only the same pre-existing, flow-unrelated Vite `stream.Stream` module-externalization
  warning every sibling artifacts case also reports). No blocking defect.
  One genuine `testid needed:` gap (the bucket dot-menu's "Delete" item carried **zero**
  `data-testid` — confirmed absent on both `origin/main` and `origin/automation/testids`) — **fixed
  live this run** (additive, well-precedented: a single `key` field added to an existing menu-items
  array entry, identical mechanism to the sibling "Upload files" fix from ELITEA-1808). Four
  CLARIFICATIONs (case-text/case-data drift, reverse-masking guard applied — **not** defects) were
  filed for four departures between the live product/case data and the case's own text:
  [#664](https://github.com/EliteaAI/elitea-testing-public/issues/664) (delete-confirmation dialog
  wording), [#665](https://github.com/EliteaAI/elitea-testing-public/issues/665) (success-toast
  wording), [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666) (dot-menu item
  label/order), [#667](https://github.com/EliteaAI/elitea-testing-public/issues/667) (the case's own
  "55-character" test-data label is actually 56 characters).
  Not `already-covered` / not `extend-existing` — see § Overlap check below.

## Overlap check vs existing automation

`automation/pages/artifacts_page.py` (1257+ lines) was read in full before this run, plus the
existing artifacts test files
(`test_artifacts_create_bucket_upload_file.py`/ELITEA-1808,
`test_artifacts_delete_subfolder_checkbox.py`/ELITEA-1847,
`test_artifacts_download_multiple_files_zip.py`/ELITEA-1840,
`test_artifacts_download_single_file_dropdown.py`/ELITEA-1839,
`test_artifacts_duplicate_bucket_name.py`/ELITEA-1809,
`test_artifacts_multi_file.py`/ELITEA-1327,
`test_artifacts_upload_duplicate_cancel.py`/ELITEA-1832,
`test_artifacts_upload_multiple_files.py`/ELITEA-1826,
`test_artifacts_upload_three_options_verify_selection.py`/ELITEA-1824) and their matching AFS files
under `test-specs/artifacts/`.

- `ArtifactsPage` already has the full "New Bucket" form flow
  (`click_create_bucket_button()`/`fill_bucket_name()`/`click_bucket_save_button()`/
  `wait_for_bucket_in_list()`, ELITEA-1808) and the bucket-row dot-menu opener
  (`open_bucket_menu()`, ELITEA-1808) — **but no existing test creates a bucket at the 55/56-char
  boundary length**, and `grep -rn "56\|max.*char\|char.*limit" tests/ui/artifacts/*.py` returns zero
  hits — no existing test exercises the character-limit boundary at all.
- No existing test drives bucket-level **deletion via the UI**. `open_bucket_menu()` is used by
  ELITEA-1808/1824 to click "Upload files" only — `grep -rn "open_bucket_menu\|bucket_menu_delete"
  tests/ui/artifacts/*.py` shows zero callers ever proceeding to "Delete". Bucket deletion elsewhere
  in the suite is exclusively `ArtifactAPI.delete_bucket()` in test teardowns (API-only, a
  completely different code path — see § Known Defects Found for why this matters).
- `ArtifactsPage.delete_confirm_dialog`/`delete_confirm_message`/`delete_confirm_button` already
  exist (added by ELITEA-1847) and are already driven by
  `test_artifacts_delete_subfolder_checkbox.py` — but **only for the file/folder bulk-delete flow**
  (toolbar icon → `DeleteEntityModal`). This case is the first to drive the SAME shared
  `DeleteEntityModal` component from the **bucket** dot-menu's "Delete" entry point — confirmed live
  this run (see § Known Defects Found) that it is genuinely the same component/testids, reused from
  a different call site with a different underlying DELETE endpoint.

Verdict: **zero behavioral overlap** — the 55/56-char boundary-length bucket creation and the
bucket-level dot-menu delete (as distinct from file/folder delete) are both fresh scenarios.
`ready-for-automation`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### generate-per-test (in test setup; no teardown deletion needed — see § Cleanup)
- **Bucket name**: use the case's own literal value verbatim —
  `bucket-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y`. Unlike ELITEA-1808/1832/1839 (where the
  case's bucket name is a placeholder to be replaced with a generated unique name), **this case's
  name IS the test subject** — its exact character count is what's under test, and the delete
  confirmation message in the case's own Test Data table embeds this identical literal string. Do
  **not** generate a fresh/unique variant; use the literal value as authored.
  - **Data-accuracy note (CLARIFICATION filed,
    [#667](https://github.com/EliteaAI/elitea-testing-public/issues/667))**: the case labels this
    string "(55 chars)" but `len(...)` on the literal value is **56**, confirmed via
    `python3 -c "print(len('bucket-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y'))"` → `56`.
    This means the case is actually exercising the exact **max-length boundary**
    (`CreateBucket.jsx`'s yup schema: `.max(56, 'Name should not exceed 56 characters')`), not "one
    character below max" as its own framing implies. This does not change the case's pass/fail
    semantics (56 ≤ 56 still triggers no warning, confirmed live — see Test Step 5) — assert against
    the string's actual length (56), not the case's "55" label.
- **Bucket name validation** (confirmed live via `CreateBucket.jsx`'s yup schema, unchanged since
  ELITEA-1808): `^[a-zA-Z][a-zA-Z0-9-]*$`, max 56 chars. The case's literal name satisfies this
  exactly at the boundary.
- **Retention policy default** (confirmed live, unchanged since ELITEA-1808,
  `EliteaUI/src/common/constants.js:480-481`): `expiration_measure` defaults to `"years"`,
  `expiration_value` defaults to `1` — i.e. exactly "Years, 1" as the case expects, no action needed
  (case step 6 — leave as default).
- **Name field's own default value**: confirmed live, unchanged since ELITEA-1808 — pre-filled with
  the literal string `"new-bucket"` on a fresh (non-edit) form load. This run's exploration used a
  plain `.fill()` (via the Playwright MCP tool, which replaced the value correctly in this case) —
  the implementer should still use the project's own established, defect-free method,
  `ArtifactsPage.fill_bucket_name()` (already implemented via `click()` + `select_text()` + `type()`
  per the ELITEA-1808 fix), not re-derive a new approach.

No `reuse-existing` fixture applies — same reasoning as ELITEA-1808: a bucket in a
freshly-created, single-purpose state isn't safe to share across parallel/serial runs, and this
case's own actions (UI-driven creation AND UI-driven deletion) make a pre-seeded fixture actively
wrong to use.

## Test Steps

1. Navigate to `${BASE_URL}/artifacts` (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible (existing testid,
     `ArtifactsPage.wait_for_page_load()` already does this).
2. Click `artifacts-create-bucket-button` (case step 2). Reuse `click_create_bucket_button()`.
   - **Verify**: URL becomes `${BASE_URL}/artifacts/create-bucket` (confirmed live, unchanged full
     page navigation since ELITEA-1808).
3. Verify the "New Bucket" form is visible with all required fields (case step 3):
   - `artifacts-bucket-name-input` visible, pre-filled with `"new-bucket"`.
   - `artifacts-bucket-retention-measure-select-combobox` visible, text `"Years"`.
   - `artifacts-bucket-retention-value-input` visible, value `"1"`.
   - `artifacts-bucket-save-button` visible.
4. Fill `artifacts-bucket-name-input` with the literal 56-char bucket name via
   `fill_bucket_name(BUCKET_NAME)` (case step 4).
   - **Verify**: field displays the name exactly; `.input_value()` length == 56 (see § Test Data
     data-accuracy note — do not assert `== 55`).
5. Verify no character-limit warning is displayed (case step 5).
   - **Verify**: `artifacts-bucket-name-input`'s `aria-invalid` attribute == `"false"` (confirmed
     live this run — MUI/formik renders NO helper-text DOM element at all when
     `formik.errors.name` is falsy; there is nothing to assert "invisible", only the input's own
     validity state). This is a state-read off the already-testid'd input, matching this page
     object's established `is_bucket_selected()`/`is_tree_item_selected()` attribute-read pattern —
     no new testid needed.
6. Do not touch the retention fields (case step 6 — "leave as default").
   - **Verify**: still `"Years"` / `"1"`.
7. Click `artifacts-bucket-save-button` via `click_bucket_save_button()` (case step 7).
   - **Verify**: response object's `.status == 200` for
     `POST ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}` (confirmed live,
     § Network Behavior).
8. Verify the bucket appears in the left-panel bucket list (case step 8).
   - **Verify**: `wait_for_bucket_in_list(BUCKET_NAME)` — the bucket's own dynamic
     `artifacts-bucket-row-{name}` testid becomes visible (existing method, ELITEA-1808 — absorbs
     the known transient "bucket list mid-fetch" race, confirmed re-observed this run at the exact
     same shape as ELITEA-1808 documented: a `browser_network_requests` read immediately after Save
     briefly reported the URL's `bucket` param as the previously-selected bucket before settling to
     the new one a moment later).
9. Hover the bucket's row, then click its 3-dot actions menu trigger via `open_bucket_menu(BUCKET_NAME)`
   (case step 9, existing method, ELITEA-1808 — hover-gated trigger, unchanged).
   - **Verify**: dropdown menu opens (existing method already waits on the "Upload files" item
     rendering as proof of open).
10. Verify the dropdown shows 4 items (case step 10).
    - **Verify**: read the FULL text content of the already-testid'd dropdown container
      (`[data-testid="bucket-menu-{name}-menu"]` — see § Concrete Handles for provenance) via a new
      `get_bucket_menu_items_text(bucket_name)` method (same "read the whole testid'd container's
      text, no new per-item testid needed" pattern this page object already established with
      `get_file_row_text()`). Confirmed live this run: full text is
      `"Upload filesRenamePin to topDelete"` — **4 items, all present** (satisfies the case's own
      "all four options are visible" pass condition), but **CLARIFICATION filed
      ([#666](https://github.com/EliteaAI/elitea-testing-public/issues/666))**: label/order differ
      from the case's literal text — assert the LIVE label (`"Rename"`, not "Edit") and LIVE order
      (Upload files, Rename, Pin to top, Delete — not "Upload files, Pin to top, Edit, Delete"), not
      the case's stale wording (reverse-masking guard). "Share"/"Manage access" are correctly absent
      (personal project, unchanged since ELITEA-1808 — not part of this case's asserted 4).
11. Click `bucket-menu-delete-menuitem` (case step 11 — **testid added live this run**, see
    § Concrete Handles).
    - **Verify**: `[data-testid="delete-confirm-dialog"]` becomes visible.
12. Verify the "Delete confirmation" modal with correct message + Cancel/Delete buttons (case step 12).
    - **Verify**: heading text is `"Delete confirmation"` (matches the case's literal expectation
      exactly — confirmed live).
    - **Verify (CLARIFICATION, not a defect — filed
      [#664](https://github.com/EliteaAI/elitea-testing-public/issues/664))**: message text
      (`delete_confirm_message`, existing testid, ELITEA-1847) reads
      **`"Are you sure to delete the {bucket_name}? It can't be restored."`** — confirmed live via
      `[data-testid="delete-confirm-message"]`'s `textContent` both runs. The case's own text says
      `"Are you sure to delete {bucket_name}? It can't be restored."` (no "the") — assert the LIVE
      text, not the case's stale wording (reverse-masking guard; same root string/component
      ELITEA-1847 already flagged for a sibling wording drift, [#659](https://github.com/EliteaAI/elitea-testing-public/issues/659) — this is the bucket-delete
      call site of the identical shared `DeleteEntityModal` default).
    - **Verify**: `delete_confirm_button` (existing testid) visible; Cancel button visible (no
      testid, out of this case's asserted scope — never clicked).
13. Click `delete_confirm_button` (case step 13). **Note**: the existing `confirm_delete()` method
    (ELITEA-1847) wraps `expect_response` matching `"artifacts/artifacts" in r.url` — that is the
    FILE/FOLDER delete endpoint, **not** the bucket-delete endpoint this case needs (see § Network
    Behavior). A new sibling method is needed — see § Automation Hints.
    - **Verify**: response object's `.status == 200` for
      `DELETE ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}?name={bucket_name}`
      (confirmed live both runs, § Network Behavior — this is the UI's OWN delete call, a
      **query-parameter** shape, notably different from `ArtifactAPI.delete_bucket()`'s
      path-segment shape — see § Known Defects Found).
14. Verify success notification (case step 14).
    - **Verify (CLARIFICATION, not a defect — filed
      [#665](https://github.com/EliteaAI/elitea-testing-public/issues/665))**: `success_toast_message`
      (existing testid `toast-message`) fires with the LIVE text
      **`"The {bucket_name} bucket has been successfully deleted."`** — confirmed live both runs. The
      case's own text says `"The bucket has been deleted successfully"` (generic, no bucket name,
      different word order) — assert the LIVE text, not the case's stale wording (reverse-masking
      guard; same root pattern as ELITEA-1847's own toast-wording CLARIFICATION,
      [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660)). Use a short polled
      presence check (the toast is short-lived — this run used a `MutationObserver` installed before
      the delete-confirm click, same technique ELITEA-1847 already established), never a single
      instantaneous DOM read.
15. Verify the bucket is no longer listed (case step 15).
    - **Verify**: `count_bucket_rows(BUCKET_NAME) == 0` (existing method, ELITEA-1809 — the dynamic
      `artifacts-bucket-row-{name}` testid's DOM absence). Confirmed live both runs.

## Expected Results
- The "New Bucket" form opens as a full page at `/artifacts/create-bucket`, pre-filled with
  `"new-bucket"` / `"Years"` / `"1"`.
- The case's literal 56-character name (mislabelled "55 chars" in the case text — see
  [#667](https://github.com/EliteaAI/elitea-testing-public/issues/667)) is accepted with no
  character-limit warning (`aria-invalid="false"`, no helper-text element rendered).
- `POST /artifacts/buckets/default/{project_id}` creates the bucket; it appears in the left-panel
  bucket list.
- The bucket-row dot-menu shows 4 items ("Upload files", "Rename", "Pin to top", "Delete" — live
  label/order, see [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666)). Clicking
  "Delete" opens the shared `DeleteEntityModal` (`delete-confirm-dialog`), whose message reads "Are
  you sure to delete the {name}? It can't be restored." (live wording, see
  [#664](https://github.com/EliteaAI/elitea-testing-public/issues/664)).
- Confirming deletion fires `DELETE /artifacts/buckets/default/{project_id}?name={bucket_name}` → 200
  (query-param shape — see § Known Defects Found), a toast fires with the live text "The {name}
  bucket has been successfully deleted." ([#665](https://github.com/EliteaAI/elitea-testing-public/issues/665)), and the bucket is removed from the
  left-panel list.
- No console errors during the flow (0 errors both runs; only the same pre-existing, flow-unrelated
  Vite `stream.Stream` warning every sibling artifacts case also reports).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture (skips login on localhost) | asserted |
| Test Data: bucket name "(55 chars)" | — | Test Data | `len()` check confirms literal value is 56 chars, not 55 | clarification *([#667](https://github.com/EliteaAI/elitea-testing-public/issues/667) — case's own data label is wrong, doesn't affect pass/fail)* |
| Step 1: Navigate to Artifacts | Artifacts page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Click create-bucket icon | "New Bucket" form opens | Test Step 2 | URL becomes `/artifacts/create-bucket` | asserted |
| Step 3: Verify form opens | Form visible | Test Step 3 | 4 testid visibility checks | asserted |
| Step 4: Enter 55-char name | Name field accepts full name | Test Step 4 | `artifacts-bucket-name-input` value check, length 56 | asserted *(literal name is 56 chars — see data-accuracy clarification)* |
| Step 5: Verify no char-limit warning | No warning appears | Test Step 5 | `aria-invalid="false"` on the name input | asserted |
| Step 6: Leave retention as default | Retention remains Years/1 | Test Step 6 | value checks unchanged | asserted |
| Step 7: Click Save | Bucket saved | Test Step 7 | `POST .../buckets/...` → 200 | asserted |
| Step 8: Verify bucket appears in list | Bucket listed | Test Step 8 | `wait_for_bucket_in_list()` | asserted |
| Step 9: Click 3-dot menu | Dropdown menu appears | Test Step 9 | `open_bucket_menu()` | asserted |
| Step 10: Verify dropdown shows Upload files/Pin to top/Edit/Delete | All 4 visible | Test Step 10 | full-text read of `bucket-menu-{name}-menu` container | asserted *(labels/order are CLARIFICATION [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666) — live label "Rename" + live order asserted, not case's stale wording)* |
| Step 11: Click Delete | Delete confirmation modal opens | Test Step 11 | `delete-confirm-dialog` becomes visible | asserted |
| Step 12: Verify "Delete confirmation" modal + message + buttons | Modal shows correct message, both buttons | Test Step 12 | heading text + `delete-confirm-message` text + button visibility | asserted *(message wording is CLARIFICATION [#664](https://github.com/EliteaAI/elitea-testing-public/issues/664) — live text asserted, not case's stale wording)* |
| Step 13: Click Delete button in modal | Deletion completes | Test Step 13 | `delete-confirm-button` click → `DELETE .../buckets/...?name=...` → 200 | asserted |
| Step 14: Verify success notification | Notification appears | Test Step 14 | `toast-message`, `MutationObserver`-confirmed | asserted *(text is CLARIFICATION [#665](https://github.com/EliteaAI/elitea-testing-public/issues/665) — live text asserted, not case's stale wording)* |
| Step 15: Verify bucket no longer listed | Bucket removed | Test Step 15 | `count_bucket_rows() == 0` | asserted |
| Expected Final State: bucket created without warning, then deleted | Composite pass condition | Test Steps 5, 7, 8, 13, 15 | combination of the above | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | console-error check (0 errors both runs) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Bucket-creation and bucket-deletion network calls verified directly** (`POST
  /artifacts/buckets/default/{id}` → 200, `DELETE
  /artifacts/buckets/default/{id}?name={bucket}` → 200) rather than only inferring success from UI
  state — *added: stronger signal than a DOM-only check, consistent with sibling cases' network-level
  verification pattern.*
- **Query-param vs path-segment DELETE URL-shape mismatch confirmed live, independent of this
  case's own pass/fail** — *added: directly informs the suspected root cause of
  [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)'s "delete returns 404" — see
  § Known Defects Found. Not filed as a new bug (out of this case's scope, a test-client-only issue),
  flagged here for the orchestrator.*
- **2/2 clean reproductions, each via a different bucket name** (the case's own literal 56-char
  name once, a short throwaway name once — the second pass exclusively via the newly-added
  `bucket-menu-delete-menuitem` testid, to independently confirm the fix works via a real native
  click, not just a role/text lookup) — *added: rules out the testid fix being a fluke of the
  specific name length, and confirms the fix survives a fresh page load / HMR reload.*
- **Console-message check after every delete completes** — *added: standard silent-error guard,
  consistent with every sibling artifacts case's precedent.*

## Cleanup
1. **No teardown deletion needed** — unlike ELITEA-1808 (where bucket creation is the subject and
   deletion is a teardown concern), **this case's own core subject IS the deletion** (Test Steps
   11–15). The bucket is already gone by the time the test's own assertions complete. Only a
   fail-safe is warranted: if an assertion fails mid-test (e.g. after creation but before the
   delete-confirm click), the bucket may be left behind — wrap the delete steps in a
   `try`/`finally` that calls `ArtifactAPI.delete_bucket(bucket_name)` as a fail-safe, tolerating a
   404 (this call is known to 404 regardless per
   [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636) — do not treat a 404 here as
   proof the bucket is gone OR as a test failure; it is a pre-existing, out-of-scope defect in the
   Python API test client, not this case's concern).
2. No other entities are created by this case (no Agent, no Toolkit, no Credential).
3. **This exploration run's artifacts** (not part of the automated test, already cleaned up live
   during this run): the literal-name bucket
   (`bucket-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y`) was created and deleted via the live
   UI flow **twice** (once for the primary pass, once for the testid-fix confirmation pass) — both
   times fully deleted, zero residual. A third, short-named throwaway bucket
   (`elitea1817-menucheck`, used only to read the dot-menu's full text content for Test Step 10) was
   also created and deleted live, zero residual. Net bucket count in `Private` returned to its
   pre-run baseline (268) after this run.
4. Local exploration screenshots (repo root, untracked; three uploaded + embedded per
   `.agents/role-overrides.md` § screenshot evidence — **upload to the `evidence` release
   temporarily failed with repeated GitHub-side 502/503 errors during this run; issues
   [#664](https://github.com/EliteaAI/elitea-testing-public/issues/664)/[#665](https://github.com/EliteaAI/elitea-testing-public/issues/665)/[#666](https://github.com/EliteaAI/elitea-testing-public/issues/666)
   reference the filenames but are not yet embedded — orchestrator/embed-evidence follow-up
   needed**):
   `ELITEA-1817-step9-10-bucket-dotmenu-open.png`,
   `ELITEA-1817-CLARIFICATION-confirm-dialog-wording.png`,
   `ELITEA-1817-step9-10-menu-4-items-text-check.png`,
   `ELITEA-1817-step12-13-delete-modal-testid-verified.png`,
   `ELITEA-1817-step17-bucket-removed-from-list.png`.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator policy
(`.agents/testing.md` § Locator policy) is **testid-only, no fallback ladder**. Every row below
carries a PROVENANCE column verified this run via a **fresh `git fetch origin`** in `../EliteaUI`,
checked independently against both `origin/main` and `origin/automation/testids` (`git grep`/`diff`
of the two refs, not just a single-branch read).

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | on-main ✓ | existing, unchanged |
| "+ Artifact Bucket" button | `artifacts-create-bucket-button` | on-main ✓ | existing, unchanged |
| New Bucket form — Name input | `artifacts-bucket-name-input` | on-automation/testids only (awaiting promotion) | existing (ELITEA-1808 fix), reused via `fill_bucket_name()`; also reused this run for the `aria-invalid` attribute read (Test Step 5) |
| New Bucket form — Retention measure combobox | `artifacts-bucket-retention-measure-select-combobox` | on-automation/testids only | existing, unchanged |
| New Bucket form — Retention value input | `artifacts-bucket-retention-value-input` | on-automation/testids only | existing, unchanged |
| New Bucket form — Save button | `artifacts-bucket-save-button` | on-automation/testids only | existing, unchanged |
| Bucket row container (hover target) | `artifacts-bucket-row-{bucketName}` (dynamic) | on-automation/testids only | existing (`BUCKET_ROW` template, ELITEA-1808); reused via `wait_for_bucket_in_list()`/`count_bucket_rows()` |
| Bucket-row 3-dot menu trigger | `bucket-menu-{bucketName}-menu-button` (dynamic) | on-automation/testids only | mechanism (`DotMenu.jsx`'s `data-testid={id ? \`${id}-menu-button\` : undefined}`) is on-main ✓, but the TEMPLATED `id={`bucket-menu-${name}`}` value that makes it unique-per-bucket lives only in `BucketItem.jsx` on `automation/testids` — confirmed via `diff` of the two refs: `origin/main`'s `BucketItem.jsx` still passes the OLD static `id="bucket-menu"` (the pre-ELITEA-1808-fix bug), so this handle only resolves correctly on `automation/testids` |
| **Bucket-row dot-menu dropdown container (whole menu)** | `bucket-menu-{bucketName}-menu` (dynamic) | on-automation/testids only | same templated-`id` provenance as the trigger above (`DotMenu.jsx`'s `<Menu data-testid={id ? \`${id}-menu\` : undefined}>`). **Used this run (new usage, not previously exercised by any test) to read the FULL 4-item dropdown text via `.text_content()`** for Test Step 10 — confirmed live: `"Upload filesRenamePin to topDelete"`. Same "read the whole testid'd container, no per-item testid needed" pattern this page object already established with `get_file_row_text()` — no new testid required for "Rename"/"Pin to top" individually. |
| "Upload files" bucket-menu item | `bucket-menu-upload-files-menuitem` | on-automation/testids only | existing (ELITEA-1808), unchanged — this case never clicks it, only counts it as part of the 4-item text read |
| **"Delete" bucket-menu item** | `bucket-menu-delete-menuitem` | **on-automation/testids only — NEW this run** | `BucketItem.jsx`'s `menuItems` array — was previously the one item ELITEA-1808 explicitly left as "follow-up for whichever case first exercises them" (no `key` field at all, confirmed via source read: `git show origin/automation/testids:.../BucketItem.jsx` showed the Delete object with `label`/`alertTitle`/`onConfirm`/etc. but no `key`). Fixed live this run: added `key: 'bucket-menu-delete'` to the object (same mechanism as the sibling `key: 'bucket-menu-upload-files'` fix) — the shared `DotMenu`/`BasicMenuItem` component auto-derives `testId: item.key` → `${testId}-menuitem`. Committed + pushed to `automation/testids` (`EliteaAI/EliteaUI@457f5f44`, `test: [EL-0000] add data-testid for bucket dot-menu Delete item (ELITEA-1817)`). Confirmed live via a SECOND, pristine pass (fresh page load, real Playwright hover+click, not the first pass's exploratory click) that the testid works and fires the identical confirmation flow, 0 console errors. |
| "Rename"/"Pin to top" bucket-menu items | *(no dedicated testid — read via the whole-container text content above)* | — | Confirmed live: neither has a `key` field in `menuItems`. Not flagged as `testid needed:` for THIS case, since the whole-container `.text_content()` read (already-testid'd parent, no chained raw selector) satisfies Test Step 10's visibility requirement without one — matching the `get_file_row_text()` precedent, not the rejected "raw id/CSS selector chained off a testid'd parent" anti-pattern ELITEA-1847 already ruled out. If a future case needs to CLICK "Rename" or "Pin to top" specifically, add per-item `key` fields then (same one-line mechanism used here for Delete). |
| Delete-confirmation dialog (root) | `delete-confirm-dialog` | on-automation/testids only (awaiting promotion) | existing (ELITEA-1847). **Confirmed live this run the bucket dot-menu's "Delete" reuses this EXACT same shared `DeleteEntityModal` component** — `DotMenu.jsx`'s `activeDialog.props.entityName` check renders `Modal.DeleteEntityModal` whenever `entityName` is set (true here: `entityName: name` on `BucketItem.jsx`'s Delete config), the identical code path ELITEA-1847 already put testids on. Zero new testid needed for the modal itself. |
| Delete-confirmation dialog message | `delete-confirm-message` | on-automation/testids only (awaiting promotion) | existing (ELITEA-1847), reused via `get_delete_confirm_message_text()` — confirmed live returns `"Are you sure to delete the {bucket_name}? It can't be restored."` for the bucket-delete call site (see [#664](https://github.com/EliteaAI/elitea-testing-public/issues/664)). |
| Delete-confirmation "Delete" (confirm) button | `delete-confirm-button` | on-automation/testids only (awaiting promotion) | existing (ELITEA-1847). **Note**: the existing `confirm_delete()` method wraps a response-wait scoped to `"artifacts/artifacts" in r.url` (the FILE/FOLDER delete endpoint) — NOT reusable as-is for the bucket-delete endpoint this case needs; see § Automation Hints for the required new sibling method. |
| Delete-confirmation "Cancel" button | *(no testid)* | confirmed absent both branches | unchanged from ELITEA-1847's finding; this case's own required steps never click it, out of scope. |
| Success toast (generic, app-wide) | `toast-message` | on-main ✓ | existing (`success_toast_message`), reused — live text for the bucket-delete path confirmed this run: `"The {bucket_name} bucket has been successfully deleted."` (see [#665](https://github.com/EliteaAI/elitea-testing-public/issues/665)). |

## Network Behavior
- **Bucket creation**: `POST ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}` with body
  `{name, expiration_measure, expiration_value}` → `200 OK`. Confirmed live both runs:
  `POST http://localhost:5173/api/v2/artifacts/buckets/default/399`. Byte-identical to ELITEA-1808's
  already-documented shape — unchanged.
- **Bucket deletion (this case's own new coverage)**: **`DELETE
  ${ELITEA_API_BASE}/artifacts/buckets/default/${PROJECT_ID}?name={bucket_name}` → `200 OK`**.
  Confirmed live both runs, e.g.
  `DELETE http://localhost:5173/api/v2/artifacts/buckets/default/399?name=bucket-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y`.
  **This is a QUERY-PARAMETER shape** (`?name=...`) — notably different from
  `automation/api/client.py`'s `ArtifactAPI.delete_bucket()`, whose `_buckets_url(bucket_name)`
  builds a **path-segment** shape (`DELETE .../artifacts/buckets/default/{project_id}/{bucket_name}`,
  with a `p--{project_id}.{bucket_name}` fallback also as a path segment) — see § Known Defects
  Found for why this matters.
- No unexpected requests observed between any click and its corresponding network call; 0 console
  errors across both runs (only the pre-existing Vite `stream.Stream` warning every sibling case
  reports).

## Known Defects Found During Exploration

**None found as a NEW product defect.** Four CLARIFICATIONs were filed for case-text/case-data drift
(reverse-masking guard — live product/case-data is correct, the case's own text/label is stale or
inaccurate):
[#664](https://github.com/EliteaAI/elitea-testing-public/issues/664) (confirm-dialog wording),
[#665](https://github.com/EliteaAI/elitea-testing-public/issues/665) (toast wording),
[#666](https://github.com/EliteaAI/elitea-testing-public/issues/666) (dot-menu label/order),
[#667](https://github.com/EliteaAI/elitea-testing-public/issues/667) (case's "55-char" data label is
actually 56 chars). None of these affect the case's own pass/fail semantics.

**Independently useful finding for [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)
("Artifact bucket cleanup fails silently — delete returns 404"), not filed as a new bug (out of this
case's scope — a test-client fix, not a product defect), flagged here for the orchestrator's
awareness:** this run's live network capture confirms the UI's own bucket-delete call uses a
**query-parameter** URL shape (`DELETE .../artifacts/buckets/default/{project_id}?name={bucket}`),
completely different from `ArtifactAPI.delete_bucket()`'s **path-segment** shape
(`DELETE .../artifacts/buckets/default/{project_id}/{bucket_name}`). Since the case's own delete flow
(driven entirely through the real UI button, confirmed 200 OK both runs) is unaffected by #636, this
strongly supports the hypothesis already recorded in this case's dispatch brief: **#636 is most
likely a wrong-URL-format bug in the project's own Python API test client** (used only for OTHER
cases' teardown cleanup), not a real backend defect. Recommend the orchestrator add this network
evidence as a comment on #636 rather than reopen investigation here.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`). This case needs
  **minimal new surface** — almost everything already exists from ELITEA-1808/1847/1809:
  1. **New** `bucket_menu_delete_menuitem = LocatorDescriptor(testid="bucket-menu-delete-menuitem")`
     — mirrors the existing `bucket_menu_upload_files_menuitem` field exactly.
  2. **New** class-level template constant for the whole dropdown container (Test Step 10), same
     shape as the existing `BUCKET_MENU_BUTTON`:
     ```python
     BUCKET_MENU_CONTAINER = '[data-testid="bucket-menu-{}-menu"]'
     ```
     plus a method `get_bucket_menu_items_text(bucket_name: str) -> str` that returns
     `self.page.locator(self.BUCKET_MENU_CONTAINER.format(bucket_name)).text_content()`. Call
     `open_bucket_menu()` first (existing).
  3. **New** `click_bucket_menu_delete_item(bucket_name)` — call `open_bucket_menu(bucket_name)`
     (existing, already waits for the menu to open), then click `bucket_menu_delete_menuitem`, then
     wait for `delete_confirm_dialog` to become visible. Mirrors the shape of the existing
     `click_bucket_menu_upload_files_item()` but without the file-chooser step.
  4. **New** `confirm_delete_bucket(timeout=15000)` — **cannot reuse the existing `confirm_delete()`
     as-is** (it wraps `expect_response` matching `"artifacts/artifacts" in r.url`, the file/folder
     delete endpoint). This case needs a sibling matching `"artifacts/buckets" in r.url and
     r.request.method == "DELETE"` instead — same `expect_response` idiom, different URL substring.
     Reuse `delete_confirm_button` (existing).
  5. **Reuse as-is, zero changes needed**: `click_create_bucket_button()`, `fill_bucket_name()`,
     `click_bucket_save_button()`, `wait_for_bucket_in_list()`, `open_bucket_menu()`,
     `get_delete_confirm_message_text()` (already reads `delete_confirm_message`),
     `success_toast_message` (`toast-message`), `count_bucket_rows()` (post-delete `== 0` check).
  6. **New** helper for Test Step 5 — `is_bucket_name_invalid(timeout=5000) -> bool` reading
     `bucket_name_input.get_attribute("aria-invalid") == "true"` (or inline in the test if a single
     call site).
- Fixtures: no bucket-creation fixture needed (unlike sibling cases, this case's own subject IS the
  UI creation flow) — use the literal case bucket name directly, no `request.node.name`/timestamp
  generation (see § Test Data — this case's name is not a placeholder).
- Wait strategy: Test Step 8 needs the same condition-based wait ELITEA-1808 already documented
  (`wait_for_bucket_in_list()`, not a fixed sleep, not an immediate assertion right after Save) — the
  same transient race was re-observed this run. Test Step 14's toast needs a short polled
  presence/`MutationObserver` check (ELITEA-1847 precedent), not a single-shot DOM read.
- Both new response-wait methods (`click_bucket_save_button()` reused as-is; `confirm_delete_bucket()`
  new) should use `page.expect_response()`/`expect_response()`, NOT
  `BasePage.capture_requests_matching()` — ELITEA-1808 already found the latter unreliable for
  positive-assertion cases (async listener can still read `status: None` after the click resolves).
