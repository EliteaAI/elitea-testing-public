# Test Case: Create Artifact Bucket via Folder Icon (Path 2) and Verify Retention Policy Edit and Persistence

## Metadata
- **TMS ID**: ELITEA-1810
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend), project `Private` / project_id `399` (967 buckets present at run time)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot · **Date**: 2026-08-23
- **Status**: **ready-for-automation** — all 27 case steps executed live end-to-end. One
  step (13) diverges from the case's expected result because of a **real, deterministic
  product defect** filed as
  [#1677](https://github.com/EliteaAI/elitea-testing-public/issues/1677); it is isolated
  (does not block later steps — steps 14–27 all executed and passed), single-cause and
  linked, so per `.agents/testing.md` § Merge gate → *Analysis-time entry* this is
  `ready-for-automation` with a **sanctioned-RED** assertion, **not** `defect-found`.
  One case-text drift (steps 12/19/26 say "Edit", the product's menu item is "Rename")
  is an already-tracked CLARIFICATION — commented on
  [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666), not re-filed.
- **AMENDED BY IMPLEMENTER 2026-08-23 — this case DOES add testids.** The original
  "zero new testids needed" claim was made against the analyst's own *uncommitted*
  working tree in `../EliteaUI`: three attribute additions (`key: 'bucket-menu-rename'`,
  `data-testid="artifacts-bucket-cancel-button"`, and the form heading) were sitting
  as unstaged edits, so they greped as "present" but existed on no branch. They are
  now committed and pushed as EliteaAI/EliteaUI@c91c2aac on `automation/testids`
  (3 added lines, 0 removals, no hooks, no new DOM nodes). See § Concrete Handles.

## Overlap check vs existing automation

Not `already-covered`, not `extend-existing`. Checked, by behaviour, before executing:

- `test-specs/artifacts/l2_create-bucket-path1-and-upload-file_ELITEA-1808.md` +
  `automation/tests/ui/artifacts/test_artifacts_create_bucket_upload_file.py` — creates a
  bucket through the same form but **leaves retention at its `Years / 1` default**
  ("Do not touch … case step 5 — leave as default"). It never opens the dropdown, never
  edits an existing bucket, and never re-opens the form to check persistence.
- `test_artifacts_create_bucket_55char_name_and_delete.py` (ELITEA-1817) and
  `test_artifacts_duplicate_bucket_name.py` (ELITEA-1809) drive the same form for **name
  validation**; retention is untouched in both.
- `grep -ril retention test-specs/` / `grep -rn retention automation/tests/` — no spec
  anywhere asserts a **non-default retention value**, a retention **edit**, or retention
  **persistence across a save/reopen**. `automation/pages/artifacts_page.py` has the
  `bucket_retention_measure_combobox` / `bucket_retention_value_input` descriptors but
  **no method that changes either**, and no method that opens the bucket's Rename/edit
  form (`click_bucket_menu_rename_item` does not exist — only `…delete_item`,
  `…upload_files_item`, `…pin_item`).

Verdict: the whole retention edit/persistence axis is fresh. `ready-for-automation`.

## Preconditions
- User logged in (localhost: `auth_state` fixture skips login).
- A project is selected (`Private`, id 399 in this run).
- No pre-seeded bucket — **creating the bucket is Test Steps 2–8 of this case**, so do NOT
  reuse the `artifact_bucket` API fixture (it would substitute the subject under test).

## Test Data

### generate-per-test
- **Bucket name**: the case's literal `bucket-2` is a **case-text placeholder**, same
  established convention as ELITEA-1808/1832/1839. Generate a fresh unique name
  (`f"autotest-1810-{ts}"` shape, matching `automation/fixtures/data_fixtures.py:455`).
  Must satisfy the form's yup schema: starts with a letter, `[a-zA-Z0-9-]`, ≤ 56 chars.
  *(A leftover `autotest-1810-b2-2251` bucket was found in project 399 — an earlier run's
  leak. Unique names per run are mandatory; see § Cleanup.)*
- **Retention values (from the case, used verbatim live)**: create `Months / 10`,
  edit to `Weeks / 20`, cancel-edit `Days / 1`.
- **Form defaults on a fresh (create) load** — confirmed live: name `new-bucket`,
  measure `Years`, value `1` (`CreateBucket.jsx`, `RETENTION_MEASURES[3]` +
  `DEFAULT_RETENTION_VALUE`).

## Test Steps

Every step below was executed live in this order; the "observed" values are what the
running system produced.

1. **(case 1)** Navigate to `${BASE_URL}/artifacts`; wait for `artifacts-buckets-heading`.
   - Observed: page loads, footer `Buckets:967`.
2. **(case 2)** Click `artifacts-create-bucket-button` — this **is** the folder icon above
   the bucket list (`BucketHeader.jsx` renders a `NewFolder` icon inside it; tooltip
   "Create bucket"). See § Known Defects/Clarifications on "Path 2".
   - Verify: `page.url` ends with `/artifacts/create-bucket` (full page nav, not a modal).
3. **(case 3)** Verify the New Bucket form:
   - `artifacts-bucket-name-input` visible, value `new-bucket`
   - `artifacts-bucket-retention-measure-select-combobox` visible, text `Years`
   - `artifacts-bucket-retention-value-input` visible, value `1` (input `type="number"`)
   - `artifacts-bucket-save-button` **and** `artifacts-bucket-cancel-button` visible
4. **(case 4)** Set the name via the established MUI workaround — `click()` +
   `select_text()` + `type()` (`ArtifactsPage.fill_bucket_name()` already does exactly
   this; `fill()` / `Control+A` do **not** work on this field).
   - Verify: `input_value() == <generated name>`.
5. **(case 5)** Click `artifacts-bucket-retention-measure-select-combobox`.
   - Verify: the option list renders 4 options — `select-option-days`, `-weeks`,
     `-months`, `-years` (texts `Days` / `Weeks` / `Months` / `Years`).
6. **(case 6)** Click `select-option-months` (`BasePage.SELECT_OPTION.format("months")` —
   the existing class constant; do **not** build an inline locator).
   - Verify: combobox text == `Months`.
7. **(case 7)** Set `artifacts-bucket-retention-value-input` to `10` — same select-all +
   type shape as step 4 (the field pre-holds `1`; a bare type would produce `110`).
   - Verify: `input_value() == "10"`.
8. **(case 8)** Click `artifacts-bucket-save-button` inside
   `page.expect_response(POST …/artifacts/buckets/default/{project_id})`
   (`ArtifactsPage.click_bucket_save_button()` already wraps this).
   - Verify: response status `200`; URL returns to `/artifacts?bucket=<name>` (the form
     auto-selects the freshly created bucket via `PENDING_BUCKET_SESSION_KEY`).
9. **(case 9)** Verify `artifacts-bucket-row-<name>` is present in the bucket list.
   - Observed live: present.
10. **(case 10)** Record the bucket's **position** = its 0-based index among
    `[data-testid^="artifacts-bucket-row-"]` (the list is alphabetically sorted; the new
    bucket landed at index 3 of 967). This index is the "position/ID" the case's step 17
    re-checks. *(There is no user-visible bucket ID in this UI — see Coverage Map.)*
11. **(case 11)** Hover `artifacts-bucket-row-<name>` **first** (the dot-menu trigger is
    hidden until row hover — a bare click times out with "element is not visible"), then
    click `bucket-menu-<name>-menu-button`.
    - Verify: `bucket-menu-<name>-menu` visible; its items are
      `Upload files` / **`Rename`** / `Pin to top` / `Delete`.
12. **(case 12)** Click `bucket-menu-rename-menuitem` (case text says "Edit" — the live
    label is "Rename"; tracked clarification #666/#650).
    - Verify: URL `/artifacts/create-bucket`, form heading text `Edit bucket`,
      `artifacts-bucket-name-input` value == the bucket name.
13. **(case 13) — SANCTIONED RED, `expect.soft()` + `# Known defect: #1677`.**
    Assert the case's **correct** expectation: combobox text == `Months` and value == `10`.
    - **Observed live: `Days` / `304`.** The product stores retention as a calendar-day
      count (10 months → 304 days) and rebuilds the unit with
      `convertDaysToMeasure()` (`src/utils/retentionPolicy.js`), whose `months` branch
      requires `days % 30 === 0` — unreachable for a real month policy. Confirmed twice
      (10 months → 304 days; 3 months → 92 days). Weeks are unaffected (exact ×7).
    - Write it as a soft assertion so the rest of the case still runs and the test flips
      green when #1677 is fixed. **Do not weaken it to match the buggy value.**
    - **IMPLEMENTER AMENDMENT:** the step needs **two** soft assertions (measure text
      AND value), so the spec's gate signature is an `ExceptionGroup` of exactly **2
      sub-exceptions from ONE cause** (`'Months' != 'Days'` and `'10' != '304'`),
      not "exactly one soft failure". Confirmed 2026-08-23: every other step —
      1-12 and 14-27, including both hard persistence assertions and the
      no-PUT-on-Cancel check — passed in the same run.
14. **(case 14)** Open the measure dropdown, click `select-option-weeks`.
    - Verify: combobox text == `Weeks`.
15. **(case 15)** Set the value field to `20` (select-all + type; it holds `304`).
    - Verify: `input_value() == "20"`.
16. **(case 16)** Click Save inside `page.expect_response(PUT …/artifacts/buckets/default/{project_id})`
    — an **edit is a PUT**, not a POST (`src/api/artifacts.js:55`). The existing
    `click_bucket_save_button()` waits for a POST, so the implementer needs a
    PUT-accepting variant (see § Automation Hints).
    - Verify: status `200`; URL returns to `/artifacts?bucket=<name>`.
17. **(case 17)** Verify the bucket is still listed under the same name **and the same
    index** recorded in step 10.
    - Observed live: name unchanged, index still 3.
18. **(case 18)** Hover the row, click `bucket-menu-<name>-menu-button` again.
19. **(case 19)** Click `bucket-menu-rename-menuitem`.
20. **(case 20)** Verify combobox text == `Weeks` **and** value == `20` — the save
    persisted. **Observed live: `Weeks` / `20` — PASSES** (hard assertion; this is the
    case's central claim and it holds).
21. **(case 21)** Open the measure dropdown, click `select-option-days`.
    - Verify: combobox text == `Days`.
22. **(case 22)** Set the value field to `1`.
    - Verify: `input_value() == "1"`.
23. **(case 23)** Click `artifacts-bucket-cancel-button`.
    - Verify: URL returns to `/artifacts?bucket=<name>` (Cancel is `navigate(-1)`), and
      **no** `PUT …/artifacts/buckets/default/*` fired — assert this with a request
      listener armed before the click (see § Automation Hints), not by absence of a toast.
24. **(case 24)** Verify the bucket list is visible again (`artifacts-bucket-row-<name>`).
25. **(case 25)** Hover the row, open `bucket-menu-<name>-menu-button`.
26. **(case 26)** Click `bucket-menu-rename-menuitem`.
27. **(case 27)** Verify combobox text == `Weeks` and value == `20` — Cancel did not
    overwrite the saved policy. **Observed live: `Weeks` / `20` — PASSES.**

## Expected Results

- Bucket created through the folder icon with a custom retention policy; `POST` 200.
- Retention edit persists across save + reopen (`Weeks / 20`, backend `retentionDays: 140`).
- Cancel neither fires a `PUT` nor changes the stored policy.
- **Known divergence**: a **Months** policy reopens as **Days** (#1677) — step 13 only.

## Coverage Map

### Axis 1 — Case element → Coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | setup | covered (setup) |
| Step 1 Navigate to Artifacts | page loads | Test Step 1 | `artifacts-buckets-heading` visible | covered |
| Step 2 Click folder icon above bucket list | New Bucket form opens | Test Step 2 | URL == `/artifacts/create-bucket` | covered (see clarification: only ONE create entry point exists) |
| Step 3 Form has Name + Retention | form visible | Test Step 3 | 5 element assertions | covered |
| Step 4 Enter bucket name | field accepts it | Test Step 4 | `input_value()` | covered (generated name, not literal `bucket-2`) |
| Step 5 Open retention dropdown (default Years) | options appear | Test Steps 3, 5 | default text `Years`; 4 options present | covered |
| Step 6 Select Months | Months selected | Test Step 6 | combobox text | covered |
| Step 7 Set value 10 | field shows 10 | Test Step 7 | `input_value()` | covered |
| Step 8 Save | bucket saved | Test Step 8 | `POST` → 200 | covered |
| Step 9 Bucket appears in list | listed | Test Step 9 | row testid present | covered |
| Step 10 Note name + position/ID | noted | Test Step 10 | index among bucket rows | covered (position; **no user-visible ID exists** — see Axis-1 note below) |
| Step 11 Open 3-dot menu | menu appears | Test Step 11 | menu container + 4 item texts | covered |
| Step 12 Select "Edit" | edit form opens | Test Step 12 | `Rename` item → `Edit bucket` form | covered, with **clarification** (#666) — label is "Rename" |
| Step 13 Retention shows 10 Months | `10 Months` | Test Step 13 | soft assert, `# Known defect: #1677` | **sanctioned-RED** — product shows `304 Days` |
| Step 14 Select Weeks | Weeks selected | Test Step 14 | combobox text | covered |
| Step 15 Set value 20 | field shows 20 | Test Step 15 | `input_value()` | covered |
| Step 16 Save | changes saved | Test Step 16 | `PUT` → 200 | covered |
| Step 17 Same name + same position | unchanged | Test Step 17 | name + list index vs step 10 | covered |
| Step 18 Open 3-dot menu again | menu appears | Test Step 18 | menu container visible | covered |
| Step 19 Select "Edit" | edit form opens | Test Step 19 | `Edit bucket` form | covered (same clarification) |
| Step 20 Retention now 20 Weeks | `20 Weeks` | Test Step 20 | hard assert on both fields | covered — **passes live** |
| Step 21 Select Days | Days selected | Test Step 21 | combobox text | covered |
| Step 22 Set value 1 | field shows 1 | Test Step 22 | `input_value()` | covered |
| Step 23 Click Cancel | closes without saving | Test Step 23 | URL back to list **and** no `PUT` fired | covered |
| Step 24 Back at bucket list | list visible | Test Step 24 | row testid present | covered |
| Step 25 Open 3-dot menu | menu appears | Test Step 25 | menu container visible | covered |
| Step 26 Select "Edit" | edit form opens | Test Step 26 | `Edit bucket` form | covered |
| Step 27 Retention still 20 Weeks | `20 Weeks` | Test Step 27 | hard assert on both fields | covered — **passes live** |
| Pass criterion: "retention persists after each Save, Cancel does not overwrite" | — | Test Steps 20, 27 | hard assertions | covered |

*Axis-1 note on step 10:* the Artifacts UI exposes **no bucket ID** anywhere in the DOM —
buckets are keyed by name (`bucket-menu-{name}-…`, `?bucket={name}`). "Position/ID" is
therefore automated as the list **index**, which is the only observable half of that step.

### Axis 2 — Observables asserted beyond the case

| Observable | Why |
|---|---|
| `POST`/`PUT` status 200 on each save | the case says "saved successfully" with no UI receipt to read (no toast fires on bucket save — verified live); the response is the only honest oracle |
| No `PUT` fires on Cancel | step 23's "without saving" is otherwise only provable indirectly at step 27; asserting the absent request localises a Cancel regression to step 23 |
| Cancel/Save button both present at step 3 | step 23 depends on Cancel existing; asserting it at form-open time makes a missing control fail early with a clear message |
| No unexpected console errors across the run | project convention; verified live — the run produced **zero** product console errors (only Vite's `stream` externalisation warning) |

## Cleanup

Delete the created bucket in teardown. **Confirmed live this run that the UI delete path
works**: row hover → `bucket-menu-<name>-menu-button` → `bucket-menu-delete-menuitem` →
`delete-confirm-button`, after which the bucket is gone from
`GET /artifacts/s3/?project_id=<id>&format=json`. (Issue
[#636](https://github.com/EliteaAI/elitea-testing-public/issues/636) records API deletes
404-ing silently — that did **not** reproduce through the UI today. Prefer
`ArtifactAPI.delete_bucket()` for teardown as the suite already does, but if it leaks,
the UI path above is a working fallback.)

## Concrete Handles (discovered during exploration)

All verified live 2026-08-23 on `automation/testids`. Provenance column checked with a
fresh `git fetch origin` in `../EliteaUI`.

| Element | Handle (testid) | Source | Provenance | Notes |
|---|---|---|---|---|
| Create-bucket folder icon | `artifacts-create-bucket-button` | `Components/BucketHeader.jsx:59` | exists (already in page object) | renders a `NewFolder` icon; tooltip "Create bucket" |
| Buckets heading | `artifacts-buckets-heading` | `BucketHeader.jsx` | exists | page-load anchor |
| Name input | `artifacts-bucket-name-input` | `CreateBucket.jsx:240` (`inputProps`) | exists | on the real `<input>`, so `input_value()` works |
| Retention measure select | `artifacts-bucket-retention-measure-select-combobox` | `CreateBucket.jsx:258` (SingleSelect derives `-combobox`) | exists | read its **textContent**, not `input_value()` |
| Retention measure options | `select-option-days` / `-weeks` / `-months` / `-years` | shared `SingleSelect` | exists | use `BasePage.SELECT_OPTION.format(<measure>)` |
| Retention value input | `artifacts-bucket-retention-value-input` | `CreateBucket.jsx:285` (`inputProps`) | exists | `type="number"`; holds the previous value — select-all before typing |
| Save button | `artifacts-bucket-save-button` | `CreateBucket.jsx:291` | exists | create → POST, edit → PUT |
| Cancel button | `artifacts-bucket-cancel-button` | `CreateBucket.jsx:307` | **ADDED this case** — EliteaAI/EliteaUI@c91c2aac (was an uncommitted local edit at analysis time) | page object: `bucket_cancel_button` |
| Bucket form heading | `artifacts-bucket-form-heading` | `CreateBucket.jsx:209` (Typography) | **ADDED this case** — EliteaAI/EliteaUI@c91c2aac | *(implementer addition)* the ONLY observable separating the create form from the edit form — the same route serves both, rendering `currentBucket ? 'Edit bucket' : 'New Bucket'`. One stable testid, state read from the TEXT (never a state-switched testid pair). Steps 12/19/26 assert on it. |
| Bucket row | `artifacts-bucket-row-{name}` | `BucketItem.jsx` | exists | hover target; also the list-index source |
| Bucket dot-menu trigger | `bucket-menu-{name}-menu-button` | `DotMenu.jsx:376` | exists | **hidden until the row is hovered** |
| Bucket dot-menu container | `bucket-menu-{name}-menu` | `DotMenu.jsx:393` | exists | |
| **Rename menu item** | `bucket-menu-rename-menuitem` | `BucketItem.jsx:165` key + `DotMenu.jsx:58` | **ADDED this case** — EliteaAI/EliteaUI@c91c2aac (the `key: 'bucket-menu-rename'` field was an uncommitted local edit at analysis time, on no branch) | page object: `bucket_menu_rename_menuitem` + `click_bucket_menu_rename_item()` |
| Delete menu item | `bucket-menu-delete-menuitem` | `BucketItem.jsx:205` | exists | teardown fallback |
| Delete confirm button | `delete-confirm-button` | shared delete dialog | exists | teardown fallback |
| Buckets footer count | `artifacts-buckets-footer-count` | `BucketsPanel.jsx` | exists | text shape `Buckets:967` |

**AMENDED: this case adds 3 testid-wiring lines** (all pure attribute additions,
EliteaAI/EliteaUI@c91c2aac): the `bucket-menu-rename` key, the cancel button's testid,
and the new `artifacts-bucket-form-heading`. Two of the three were present only as
uncommitted edits in the analyst's working tree.

## Network Behavior

| Action | Request | Observed |
|---|---|---|
| Save (create) | `POST {API}/artifacts/buckets/default/{project_id}` body `{name, expiration_measure, expiration_value}` | `200` |
| Save (edit) | `PUT {API}/artifacts/buckets/default/{project_id}` same body shape (`src/api/artifacts.js:55`) | `200` |
| Cancel | *(none)* | verified: no bucket request fires |
| List oracle | `GET /artifacts/s3/?project_id={id}&format=json` → `buckets[].retentionDays` | `10 Months` → `304`; `3 Months` → `92`; `20 Weeks` → `140` |

The `retentionDays` field is a useful independent tie-breaker if a UI read looks stale —
`140` is the ground truth behind "20 Weeks".

## Known Defects Found During Exploration

1. **[#1677](https://github.com/EliteaAI/elitea-testing-public/issues/1677) — BUG,
   filed this run.** A Months retention policy reopens as Days
   (`10 Months` → `304 Days`, `3 Months` → `92 Days`). Deterministic (2/2 + arithmetic
   proof: the backend stores calendar-accurate days, `convertDaysToMeasure()` needs
   `days % 30 === 0`). Isolated to case step 13; Weeks and Years are unaffected.
   → soft assert + `# Known defect: #1677`; **sanctioned-RED per `.agents/testing.md`
   § Merge gate**. This spec's gate signature is: exactly one soft failure at step 13.

2. **CLARIFICATION (not re-filed — commented on
   [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666), sibling
   [#650](https://github.com/EliteaAI/elitea-testing-public/issues/650)):** case steps
   12/19/26 say "Select **Edit**"; the live menu item is **Rename**. Same object, same
   trigger, same expected/actual as those two open clarifications → duplicate, so the new
   occurrence was consolidated as a comment rather than a third ticket. The AFS asserts
   the live label.

3. **CLARIFICATION on the case's premise — "Path 2 / second path" (worth a human's eye,
   NOT filed as a bug):** the case is written as if bucket creation had two entry points,
   with ELITEA-1808 covering "Path 1 (+ Artifact Bucket button)" and this case covering
   "Path 2 (folder icon above the bucket list)". **Live, there is exactly one:**
   `BucketHeader.jsx:59` renders a single `NewFolder`-icon button
   (`artifacts-create-bucket-button`), and it is the same control ELITEA-1808's AFS
   already drives (`grep -rn "create-bucket" ../EliteaUI/src` returns that one call site
   plus the route constant). The empty-state panel's own "Create" button (shown only when
   the project has zero buckets) calls the same handler. So this case's step 2 and
   ELITEA-1808's step 2 exercise the **same** element — the two cases remain distinct
   because everything after step 8 (retention edit + persistence + Cancel) is unique to
   this one. Left to the lead: whether to file a case-text clarification asking the TMS
   author to drop the "second path" framing. Not filed to avoid a third near-identical
   clarification ticket in this batch.

## Blocked Steps

None — all 27 steps executed.

## Automation Hints

- **File**: new `automation/tests/ui/artifacts/test_artifacts_bucket_retention_edit_persistence.py`
  (one class, one test). Markers: `p1`/`p2` per the case's `high` priority + `artifacts`,
  `ui`, `regression`. Every step wrapped in `with allure.step("Step N — …"):`.
- **Page-object work (all in `automation/pages/artifacts_page.py`)**:
  - add `bucket_cancel_button = LocatorDescriptor(testid="artifacts-bucket-cancel-button", …)`
  - add `bucket_menu_rename_menuitem = LocatorDescriptor(testid="bucket-menu-rename-menuitem", …)`
    plus `click_bucket_menu_rename_item()` mirroring the existing
    `click_bucket_menu_delete_item()`
  - add `select_retention_measure(measure: str)` — clicks
    `bucket_retention_measure_combobox`, then
    `self.page.locator(self.SELECT_OPTION.format(measure))` (the constant is inherited
    from `BasePage`; do **not** inline a new selector)
  - add `set_retention_value(value: str)` — `click()` + `select_text()` + `type()`
    (the field is pre-populated; a bare `type()` concatenates)
  - add `get_retention_measure_text()` / `get_retention_value()` readers
  - add a **PUT-waiting** save, e.g. `click_bucket_save_button(method="PUT")` or a
    sibling `click_bucket_save_button_expect_put()` — the existing method's
    `expect_response` predicate hardcodes `r.request.method == "POST"` and will hang on
    an edit save.
  - add `get_bucket_row_index(name) -> int` for the step 10/17 position check (there is
    already `get_rendered_bucket_names()` — index into it).
- **Cancel's "no request" assertion**: arm a listener before the click, e.g.
  ```python
  puts: list[str] = []
  self.page.on("request", lambda r: puts.append(r.url)
               if r.method == "PUT" and "artifacts/buckets" in r.url else None)
  ```
  then assert `puts == []` after the navigation settles. (Page-object-side helper
  preferred over raw listener code in the spec.)
- **Hover before the dot menu, always.** `bucket-menu-{name}-menu-button` exists in the
  DOM but is invisible until the row is hovered — a direct click fails with
  *"element is not visible"*. `open_bucket_menu()` already hovers; reuse it.
- **Never poll with a busy `while` loop inside `page.evaluate`.** A JS spin-loop blocks
  the main thread, so React can never render the 967-row bucket list and the poll reads
  `0 rows` forever (cost ~65 s of false "the list never loads" during this analysis).
  Use Playwright's own waits (`expect(...).to_have_count`, `locator.wait_for`).
- **IMPLEMENTER-DISCOVERED (2026-08-23) — the measure Select's own backdrop blocks
  a second combobox click.** MUI renders an invisible `MuiBackdrop` for the open
  `menu-expiration_measure` popover, sitting OVER the combobox. So a
  `select_retention_measure()` called right after `open_retention_measure_dropdown()`
  (case Step 5 -> Step 6) times out on `Locator.click` if it unconditionally clicks
  the combobox. `ArtifactsPage.select_retention_measure()` therefore only issues the
  open-click when `aria-expanded != "true"`, and waits for the option to reach
  `hidden` afterwards so the closing backdrop cannot race the next click (into the
  retention-value field).
- **IMPLEMENTER-DISCOVERED (2026-08-23) — the bucket-list refetch needs far more than
  15 s in this project.** With ~970 buckets, the left panel's post-save refetch
  regularly exceeded the 15 s `NAVIGATION_TIMEOUT` the sibling artifacts specs use,
  producing a false "bucket never appeared" at case Step 9. The spec uses a dedicated
  `BUCKET_LIST_TIMEOUT = 45_000` for every bucket-list condition wait (Steps 9/17/24
  and the teardown's removal wait). Still a condition wait on the row's own testid —
  no sleeps. Sibling specs on smaller flows may hit this as the project grows.
- **Teardown: the UI delete path works; `ArtifactAPI.delete_bucket()` 404s (#636).**
  Confirmed again this run — the API fallback returns 404 every time, the UI path
  (hover row -> dot-menu -> Delete -> confirm) removes the bucket cleanly once the
  removal wait is given `BUCKET_LIST_TIMEOUT`.
- **Read the measure as text, the value as `input_value()`** — the measure is a MUI
  Select (a `div`), the value is a real `<input type="number">`.
- Retention units that round-trip cleanly (useful if the case data is ever rewritten):
  `weeks` (×7) and `years` (×365) survive; `months` does not (#1677).
