# Test Case: Create Artifact Bucket with a 56-Character Name, Verify the Character Indicator, and Cancel the Delete Confirmation

## Metadata
- **TMS ID**: ELITEA-1818
- **Case snapshot**: `.agents/automation/artifacts-w04/cases/ELITEA-1818.md`
- **Priority**: l3 (source case `priority: medium`, mapped per this folder's convention)
- **Environment explored**: local `http://localhost:5173` (EliteaUI `automation/testids` → DEV
  backend), project `Private` / id `399`. Dev server confirmed responsive (HTTP 200) at run start.
- **User set**: `${TEST_USER}` (on localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot · **Date**: 2026-08-23
- **Status**: **ready-for-automation — SANCTIONED-RED on merge** (see § Classification note).
  Case executed end-to-end live. One **known, already-filed product defect**
  ([#1080](https://github.com/EliteaAI/elitea-testing-public/issues/1080)) makes case step 7
  ("Click Save") fail on a *single* click at exactly 56 characters — deterministic (4/4 at 56
  chars, 0/4 at ≤55), single-cause, root-caused this run. Two CLARIFICATIONs filed
  ([#1682](https://github.com/EliteaAI/elitea-testing-public/issues/1682) — indicator text,
  [#1683](https://github.com/EliteaAI/elitea-testing-public/issues/1683) — 57-char test data);
  one pre-existing CLARIFICATION reused
  ([#666](https://github.com/EliteaAI/elitea-testing-public/issues/666) — menu label/order,
  new occurrence commented, not re-filed). One `testid needed:`
  (`artifacts-bucket-name-character-counter`). 0 console errors across the whole flow.
- **Sibling case analysed in the same session**: ELITEA-1819
  (`l3_bucket-name-field-rejects-more-than-56-characters_ELITEA-1819.md`). Separate AFS — the two
  cases share steps 1-5 but **diverge in steps**, not merely in data (1818 saves the bucket and
  drives a delete-confirmation Cancel; 1819 never saves and asserts `maxLength` rejection).

## Classification note — declared improvisation (analysis-time sanctioned-RED entry)

`.agents/testing.md` § Merge gate → *Analysis-time entry (2026-07-23, #557/ELITEA-1965)*: a
defect discovered during analysis that is (a) deterministic, (b) single-cause, and (c) linked to
an OPEN defect issue is classified **`ready-for-automation`**, not `defect-found`, with the
affected assertion written as the **correct expected behaviour** under `expect.soft()` +
`# Known defect: #1080`. All three criteria hold here, and the defect does **not** block
exploration — a blur-then-click reaches every later step, so the case's own distinguishing
subject (the delete-confirmation **Cancel**, steps 9-15, which no merged spec covers) is fully
automatable today and flips fully green when #1080 ships.

**Consequence the lead must plan for:** a spec carrying one `expect.soft()` failure is a pytest
**FAILED** outcome (`.agents/testing.md` § Merge gate, verified 2026-08-22). This spec therefore
merges **RED** under the sanctioned-RED exception, owes a closure-record entry, and its case
status is **`blocked-on-#1080`, never `automated`**.

## Fidelity declaration

**No substitution of any kind.** Every asserted value is produced by the live system: the bucket
is created through the real form against the real `POST /api/v2/artifacts/buckets/default/{pid}`,
the menu text is read from the live DOM, and the delete-confirmation Cancel is a real click.

One **declared transit note** (not a substitution — it is an ordinary user gesture): to reach
steps 8-15 past defect #1080, the test blurs the Name field (`Tab`) **after** the soft-asserted
single-click assertion, then clicks Save. Nothing is fabricated, injected, or short-circuited;
the workaround is exactly what a real user does when the first click appears to do nothing.

## Overlap check vs existing automation

Read before executing: `automation/pages/artifacts_page.py`, every
`automation/tests/ui/artifacts/test_artifacts_*bucket*.py`, and the sibling AFS files under
`test-specs/artifacts/` (notably ELITEA-1817, 1809, 1811, 1813, 1815, 1816).

- **ELITEA-1817** (`test_artifacts_create_bucket_55char_name_and_delete.py`, merged to
  `origin/automation/base`) is the closest relative: it also creates a bucket at the 56-char
  boundary and also opens the bucket dot-menu's Delete. It is **not** coverage for this case:
  - it asserts *no* character indicator — only `aria-invalid == "false"`
    (`is_bucket_name_invalid()`); the counter element is never located or read;
  - its terminal action is the **opposite** one: it clicks **Delete** in the modal and asserts
    the bucket is **gone**. This case clicks **Cancel** and asserts the bucket **remains** — a
    different observable that cannot be appended to a spec that destroys its own subject
    (`extend-existing` is therefore not the right shape either);
  - it is currently `@pytest.mark.blocked` for defect #1080.
- `grep -rn "maxlength\|characters left\|character.limit" tests/ui/artifacts/ pages/artifacts_page.py -i`
  → only ELITEA-1817's prose. **No existing spec reads the character counter.**
- `delete_confirm_cancel_button` exists and is driven by ELITEA-1845
  (`test_artifacts_delete_single_file_dropdown_cancel`) — but for the **file** delete flow, never
  for a **bucket** delete. Bucket-level delete-cancel is new.

Verdict: **fresh implementation**, `ready-for-automation`.

## Preconditions
- User logged in (localhost: `auth_state` skips login).
- A project is selected (`Private`, id 399 in this run).
- No fixture applies — the bucket is created BY the test (case step 7) and, unlike ELITEA-1817,
  **survives the case** (step 13 cancels the deletion), so the test owns its teardown.

## Test Data

- **Bucket name — generate a UNIQUE 56-character name per run.** Do **not** use the case's own
  literal:
  1. it is **57** characters, not 56 (CLARIFICATION
     [#1683](https://github.com/EliteaAI/elitea-testing-public/issues/1683)) — typing it yields
     `bucket-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y` (56 chars), silently truncated by
     `inputProps.maxLength = 56`;
  2. that truncated value is **byte-identical to ELITEA-1817's literal** — two specs creating the
     same bucket name collide;
  3. this case's bucket is *not* deleted by its own steps, so a fixed name makes the second run
     fail on duplicate-name (cf. ELITEA-1809), aggravated by the known cleanup leak
     [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636).
  Shape used live: `("afs1818" + <6-digit stamp> + "a1b2c3…")[:56]` — must satisfy
  `^[a-zA-Z][a-zA-Z0-9-]*$` and be **exactly 56** characters (assert the length in the test as a
  data sanity check; the whole case is meaningless at any other length).
- **Character indicator expected text**: `0 characters left` — **not** the case's
  `0 of 56 remaining` (CLARIFICATION
  [#1682](https://github.com/EliteaAI/elitea-testing-public/issues/1682)). Source of truth:
  `src/[fsd]/shared/ui/text/CharacterCounter.jsx` → `` `${remaining} characters left` ``; the
  `". You have reached the MAXIMUM character limit"` suffix is suppressed at this call site
  (`hideMaxLimitMessage`).
- **Retention defaults** (untouched, case step 6): `Years` / `1`.
- **Name field default on a fresh form**: `new-bucket`.
- **Bucket-menu expected text** (live): `"Upload filesRenamePin to topDelete"` — case text says
  "Upload files, Pin to top, Edit, Delete"; assert the LIVE contract (CLARIFICATION
  [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666), reverse-masking guard).

## Test Steps

1. **Navigate to Artifacts** (case step 1) — `ArtifactsPage.navigate_to_artifacts()`.
   - Verify `artifacts-buckets-heading` visible (`wait_for_page_load()`).
2. **Click the create-bucket icon** (case step 2) — `click_create_bucket_button()`.
   - Verify URL contains `/artifacts/create-bucket` (full page navigation, not a modal —
     re-confirmed live).
3. **Verify the "New Bucket" form** (case step 3).
   - `artifacts-bucket-form-heading` text == `"New Bucket"`.
   - `artifacts-bucket-name-input` visible, `input_value() == "new-bucket"`.
   - `artifacts-bucket-retention-measure-select-combobox` text == `"Years"`;
     `artifacts-bucket-retention-value-input` value == `"1"`; `artifacts-bucket-save-button`
     visible.
4. **Enter the 56-character name** (case step 4) — `fill_bucket_name(BUCKET_NAME)`
   (click + `select_text()` + `type()`; a bare `fill()` does not drive formik —
   `.claude/rules/mui-patterns.md`).
   - Verify `input_value() == BUCKET_NAME` and `len(...) == 56`.
   - **Leave the field focused** — step 5 depends on it.
5. **Verify the character indicator** (case step 5) — **the case's own subject, and the one
   observable ELITEA-1817 does not assert.**
   - Verify the counter is visible and its text is exactly `"0 characters left"`
     (**testid needed**, see § Concrete Handles).
   - Verify the field is NOT flagged invalid: `is_bucket_name_invalid()` is `False`
     (`aria-invalid == "false"` live) and no `artifacts-bucket-name-helper-text` element exists
     — 56 is valid, the indicator is neutral information, not an error.
   - **Focus gotcha (live-confirmed both directions):** the counter renders only while
     `isFocused('name') && length === 56`. Blur (Tab / click elsewhere) removes it from the DOM;
     re-focus restores it. Never assert it after a blur.
6. **Leave the retention policy at its default** (case step 6).
   - Verify measure still `"Years"`, value still `"1"`.
7. **Click Save** (case step 7) — **two assertions, in this order.**
   - **7a — SOFT, known defect #1080.** A single click on `artifacts-bucket-save-button` while
     the Name field is focused MUST submit the form. Live: it does not — only `mousedown` fires,
     no `click`, no request, the form stays open. Write this as
     `expect.soft` / a collected soft failure asserting the CORRECT behaviour (a creation `POST`
     fires), with `# Known defect: #1080`. Do **not** weaken, skip, or invert it.
     - Mechanism (for the docstring): the counter occupies 16 px of flow; `mousedown` blurs the
       field → counter unmounts → Save button shifts up 16 px → `mouseup` lands off-target → the
       browser emits no `click`.
   - **7b — declared transit** (see § Fidelity declaration): blur the Name field
     (`bucket_name_input.press("Tab")`), then click Save inside
     `click_bucket_save_button()`'s `expect_response`.
     - Verify the response `.status == 200` for
       `POST {api}/artifacts/buckets/default/{project_id}` (live-confirmed).
8. **Verify the bucket appears in the bucket list** (case step 8).
   - `wait_for_bucket_in_list(BUCKET_NAME)` — condition wait on the dynamic
     `artifacts-bucket-row-{name}` testid. Never a bare count read straight after Save (the list
     refetches asynchronously).
9. **Open the bucket's 3-dot actions menu** (case step 9) — `open_bucket_menu(BUCKET_NAME)`
   (hover-gated trigger).
   - Verify `bucket-menu-upload-files-menuitem` visible (proof the dropdown opened).
10. **Verify the dropdown's four options** (case step 10) —
    `get_bucket_menu_items_text(BUCKET_NAME)`.
    - Verify text == `"Upload filesRenamePin to topDelete"` (LIVE label/order, CLARIFICATION
      #666 — not the case's "Upload files, Pin to top, Edit, Delete").
11. **Click "Delete"** (case step 11) — `click_bucket_menu_delete_item()`.
    - Verify `delete-confirm-dialog` becomes visible.
12. **Verify the delete-confirmation modal** (case step 12).
    - `delete-confirm-title` text == `"Delete confirmation"`.
    - `get_delete_confirm_message_text()` ==
      `f"Are you sure to delete the {BUCKET_NAME}? It can't be restored."` (live-confirmed; the
      wording drift vs older case texts is already tracked as
      [#664](https://github.com/EliteaAI/elitea-testing-public/issues/664) — this case's own text
      says only "correct message", so no new clarification is owed).
    - `delete-confirm-button` ("Delete") visible **and** `delete-confirm-cancel-button`
      ("Cancel", text `"Cancel"`) visible.
13. **Click "Cancel"** (case step 13) — `delete_confirm_cancel_button.click()`.
    - Verify **no** `DELETE` request is issued (live-confirmed: zero `/artifacts/buckets`
      requests during the whole cancel window). Assert with a network guard, e.g. a
      `page.on("response")` collector asserted empty for `/artifacts/buckets`, or
      `expect_response`-free negative check over a bounded wait.
14. **Verify the modal is closed** (case step 14).
    - `expect(delete_confirm_dialog).not_to_be_visible()`.
15. **Verify the bucket is still listed** (case step 15).
    - `count_bucket_rows(BUCKET_NAME) == 1` (live-confirmed) — and, stronger, the row is still
      visible: `expect(page.locator(BUCKET_ROW.format(name))).to_be_visible()`.
    - Optional cross-check: a bucket-list `GET` still returns the name (guards against a
      DOM-only survivor).

**Teardown (mandatory — this case leaves a bucket behind by design).** Delete the bucket through
the same UI path (`open_bucket_menu` → `click_bucket_menu_delete_item` → `confirm_delete_bucket`),
live-confirmed `DELETE …?name={bucket}` → 200 with toast
`"The {bucket} bucket has been successfully deleted."`. Wrap in `try/finally`, tolerate failure
(never fail the test on teardown). `ArtifactAPI.delete_bucket()` is **not** a reliable fallback —
known 404 leak [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636).
Note: `count_bucket_rows()` immediately after the DELETE response can still read `1` (the list
refetch trails the response) — use `wait_for_bucket_removed_from_list()` if the teardown asserts.

## Concrete Handles

| Element | Handle | Provenance (fetched 2026-08-23) | Notes |
|---|---|---|---|
| Buckets page heading | `artifacts-buckets-heading` | on-main ✓ | `wait_for_page_load()` |
| Create-bucket icon | `artifacts-create-bucket-button` | on-main ✓ | `click_create_bucket_button()` |
| Form heading | `artifacts-bucket-form-heading` | on-`automation/testids` only (awaiting human promotion to main) | text `"New Bucket"` |
| Name input | `artifacts-bucket-name-input` | on-main ✓ | `maxLength="56"` on the DOM node |
| **Character counter** | `artifacts-bucket-name-character-counter` | **ADDED during implementation** — EliteaAI/EliteaUI@475adcc5 on `automation/testids` (pushed; awaiting human cherry-pick to `main`) | `CreateBucket.jsx:248` `<Text.CharacterCounter>`. Wired prop-only (the component already accepts a `data-testid` prop, `CharacterCounter.jsx:11,20`) — one added line, no DOM node, no hook. **Implementation note:** the host `Box` is `display: contents`, so `bounding_box()` returns `None` while `is_visible()` / `to_be_visible()` still resolve `True` (confirmed live 2026-08-23) — assert visibility/text, never geometry. |
| Name helper text | `artifacts-bucket-name-helper-text` | on-main ✓ | absent in this flow (56 is valid) — assert absence via `to_have_count(0)` |
| Retention measure | `artifacts-bucket-retention-measure-select` (+ `-combobox`) | on-main ✓ | text `"Years"` |
| Retention value | `artifacts-bucket-retention-value-input` | on-main ✓ | value `"1"` |
| Save button | `artifacts-bucket-save-button` | on-main ✓ | enabled at 56 chars (`disabled` only when `length > 56`) |
| Bucket row (dynamic) | `artifacts-bucket-row-{name}` | on-main ✓ | `ArtifactsPage.BUCKET_ROW` template |
| Bucket dot-menu trigger | `bucket-menu-{name}-menu-button` | on-main ✓ | `open_bucket_menu()`, hover-gated |
| Bucket menu container | `bucket-menu-{name}-menu` | on-main ✓ | `get_bucket_menu_items_text()` |
| Menu → Upload files | `bucket-menu-upload-files-menuitem` | on-main ✓ | open-proof |
| Menu → Delete | `bucket-menu-delete-menuitem` | on-main ✓ | added by ELITEA-1817 |
| Delete dialog | `delete-confirm-dialog` | on-main ✓ | shared `DeleteEntityModal` |
| Delete dialog title | `delete-confirm-title` | on-main ✓ | `"Delete confirmation"` |
| Delete dialog message | `delete-confirm-message` | on-main ✓ | `get_delete_confirm_message_text()` |
| Delete (confirm) button | `delete-confirm-button` | on-main ✓ | **not clicked by this case** |
| **Cancel button** | `delete-confirm-cancel-button` | on-main ✓ | this case's terminal action |
| Success toast | `toast-message` | on-main ✓ | teardown only |

All existing page-object methods above already exist in `automation/pages/artifacts_page.py`.
New page-object work needed: a class-level `LocatorDescriptor` for the character counter and a
reader for its text; plus a Save-click variant that does **not** wrap `expect_response` (for
assertion 7a) — `click_bucket_save_button_expect_no_request()` already exists (ELITEA-1811) and
may be reusable, but its semantics ("no request expected") are the *defect's* behaviour, so the
soft assertion must be phrased as "a request SHOULD have fired".

**SHIPPED (implementation, 2026-08-23):** added
`ArtifactsPage.bucket_name_character_counter` + `get_bucket_name_character_counter_text()`
(both additive). Assertion 7a did **not** reuse
`click_bucket_save_button_expect_no_request()`: the spec wraps a plain
`bucket_save_button.click()` in a short `page.expect_response(...)` (5 s) that is EXPECTED to
succeed and currently times out — phrasing the assertion as "a request SHOULD have fired", so
the test flips green by itself when #1080 ships. The soft failure is collected in a
`soft_failures` list and raised by a trailing `pytest.fail()` (the project's established idiom;
Playwright's `expect.soft` takes locators/pages/responses only, and this observable is the
ABSENCE of a request). Spec:
`automation/tests/ui/artifacts/test_artifacts_create_bucket_56char_limit_warning_delete_cancel.py`.

## Network Behavior

| Action | Request | Observed |
|---|---|---|
| Save (single click, 56 chars, field focused) | — | **none** (defect #1080) |
| Save (after blur) | `POST {api}/artifacts/buckets/default/399` | 200 |
| Bucket list | `GET /artifacts/s3/?project_id=399&format=json` | 200 |
| Delete-confirmation **Cancel** | — | **none** (asserted) |
| Teardown delete | `DELETE {api}/artifacts/buckets/default/399?name={bucket}` | 200 |

## Coverage Map

### Axis 1 — every element of the source case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` (localhost bypass) | fixture | covered |
| Step 1 — navigate to Artifacts | page loads | Step 1 | `artifacts-buckets-heading` | covered |
| Step 2 — click create-bucket icon | New Bucket form opens | Step 2 | URL `/artifacts/create-bucket` | covered |
| Step 3 — verify form opens | form visible | Step 3 | heading + 4 field assertions | covered |
| Step 4 — enter 56-char name | field accepts full name | Step 4 | `input_value()` + length 56 | covered (test data corrected — CLARIFICATION #1683) |
| Step 5 — char-limit warning "0 of 56 remaining" | warning shown | Step 5 | counter text `"0 characters left"` | covered, **text corrected** — CLARIFICATION #1682 (reverse-masking guard) |
| Step 6 — retention default Years/1 | unchanged | Step 6 | measure + value | covered |
| Step 7 — click Save | bucket saved | Step 7a (soft) + 7b | soft assert + `POST` 200 | **sanctioned-RED**, known defect #1080 |
| Step 8 — bucket appears in list | listed | Step 8 | `wait_for_bucket_in_list` | covered |
| Step 9 — click 3-dot menu | dropdown appears | Step 9 | `bucket-menu-upload-files-menuitem` | covered |
| Step 10 — four options visible | all four visible | Step 10 | menu container full text | covered, **label/order corrected** — CLARIFICATION #666 |
| Step 11 — click Delete | confirmation modal opens | Step 11 | `delete-confirm-dialog` visible | covered |
| Step 12 — modal message + Cancel/Delete buttons | modal correct | Step 12 | title + message + both buttons | covered |
| Step 13 — click Cancel | closes without deletion | Step 13 | no `DELETE` request fired | covered |
| Step 14 — modal closed | not visible | Step 14 | `not_to_be_visible()` | covered |
| Step 15 — bucket still listed | remains | Step 15 | row visible, count == 1 | covered |
| Expected final state | warning + created + Cancel keeps bucket | Steps 5, 7, 15 | — | covered |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why |
|---|---|
| `aria-invalid == "false"` + helper text absent at 56 chars | the case calls the counter a "warning"; proving the field is **not** in an error state is what makes "56 is valid" a real assertion rather than a guess |
| No network request during Cancel | "closes without deletion" is only meaningful if the client never asked the server to delete; a DOM-only check would pass even if a DELETE fired and failed |
| Creation `POST` status 200 | step 7's "bucket is saved" is otherwise inferred from the list, which lags |
| Form field defaults in step 3 | the case says "form is visible"; the defaults are what make the later "left at default" assertion (step 6) meaningful |
| Console-error side channel across the whole flow | project convention; 0 errors observed live |

## Known Defects Found

| # | Severity | Summary |
|---|---|---|
| [#1080](https://github.com/EliteaAI/elitea-testing-public/issues/1080) (**pre-existing, OPEN — root cause added this run, not re-filed**) | Major | Save silently does nothing on a single click at exactly 56 characters. Root cause: the focus-gated character counter occupies 16 px of flow; `mousedown` blurs the field → counter unmounts → Save button shifts up 16 px → `mouseup` lands off-target → no `click` event → `onSave` never runs. Blur-then-click works (POST 200). ≤55 chars unaffected. Reproduced 4/4. Real users hit this identically. |

Clarifications (case-text drift, NOT defects — reverse-masking guard):
[#1682](https://github.com/EliteaAI/elitea-testing-public/issues/1682) (indicator text /
focus-gating), [#1683](https://github.com/EliteaAI/elitea-testing-public/issues/1683) (57-char
test data), [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666) (menu
label/order — pre-existing, new occurrence commented).

## Blocked Steps

None. Step 7 is degraded by #1080 but reachable; every other step executed cleanly.

## Automation Hints

- **Markers**: `ui`, `regression`, `p2`, `artifacts`.
- Wrap every step in `with allure.step("Step N — …"):`.
- Locators: testid-only `LocatorDescriptor` class fields; the counter needs a new testid via
  `add-data-testid` (prop already supported — pass `data-testid` at the `CreateBucket.jsx` call
  site; do NOT add a wrapper element).
- The soft-assert must use the project's established `expect.soft`/collected-failure shape with
  `# Known defect: #1080` in the test body, and the docstring must name the workaround used to
  continue (declared transit).
- Timeouts: 10 s UI elements, 15-25 s navigation / bucket-list refetch, 25 s create-POST.
- Zero console errors expected (only the pre-existing Vite `stream.Stream` externalization
  **warning**, which is not an error).

## Cleanup

`try/finally` UI deletion of the created bucket (see § Test Steps teardown). Do not rely on
`ArtifactAPI.delete_bucket()` (#636).

## Evidence

- `test-results/screenshots/ELITEA-1818-step-05-counter.png`
- `test-results/screenshots/ELITEA-1818-step-12-delete-dialog.png`
- `test-results/screenshots/ELITEA-1818-step-15-bucket-remains.png`
