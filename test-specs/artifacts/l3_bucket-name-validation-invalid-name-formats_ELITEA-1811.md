# Test Case: Bucket Name Validation Rejects Invalid Name Formats (Family)

## Metadata
- **TMS ID (family)**: ELITEA-1811, ELITEA-1814 — `family_afs: true`, this file is
  the single AFS for both cases (parameter table below has one row per case;
  ELITEA-1814 alone contributes 3 rows, one per invalid input it exercises).
- **Linked Story**: none
- **Priority**: l3 (medium — both source cases declare `priority: medium` in
  frontmatter; maps to `l3` per this folder's established convention, e.g.
  sibling ELITEA-1809/1817/1868)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend). Dev server confirmed running and
  responsive at run start (`curl` 200).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login
  via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot (cluster dispatch, one live session for
  both cases)
- **Status**: **ready-for-automation** — both cases executed end-to-end live,
  all 4 invalid-name variants confirmed via direct Python/Playwright scratch
  probes against `http://localhost:5173` (MCP Playwright server was not
  reachable in this session — see § Automation Hints; the project's own
  `ArtifactsPage` methods were used to drive the probe, so the exercised code
  path is identical to what the implementer will write). 0 console errors
  beyond the pre-existing, flow-unrelated Vite `stream.Stream`
  module-externalization warning every sibling artifacts case also reports.
  No blocking defect. One `testid needed:` gap (the inline validation message
  has no `data-testid` at all today) — implementer work, not a blocker.

## Family classification rationale

Per `test-case-analysis` § 3 "differ only in DATA vs. differ in STEPS": both
cases drive the **identical** flow (open New Bucket form → type an invalid
name → click Save → assert the exact inline validation message → confirm no
bucket was created) against the **same** yup validation rule
(`^[a-zA-Z][a-zA-Z0-9-]*$`, confirmed live via
`EliteaUI/src/pages/Artifacts/CreateBucket.jsx:22-30`) and assert the **same**
error string. ELITEA-1811 supplies one invalid value (leading digit);
ELITEA-1814 supplies three more (special char, underscore, space) via an
explicit "repeat steps 1-4 with input X" structure in its own case text — i.e.
the source case itself is already parameterized data, not new steps. One
parameterized spec, 4 data rows total.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / localhost
  `auth_state`).
- No bucket exists (in the current project) with the same name as any Test
  Data value below — none of these are typical existing bucket names, and no
  create ever succeeds for them, so this is a non-issue in practice, but
  worth stating since a stray earlier failed run would leave the same name
  free (the bucket is never created either way).

## Test Data

### Parameter table (one row per source TMS case / sub-case)

| # | Source case | Invalid bucket name | What it violates |
|---|---|---|---|
| 1 | ELITEA-1811 | `1bucket` | starts with a digit, not a letter |
| 2 | ELITEA-1814 (input 1) | `new-bucket$` | contains `$`, a disallowed special character |
| 3 | ELITEA-1814 (input 2) | `bucket_one` | contains `_`, not in the allowed set (letters/numbers/hyphen) |
| 4 | ELITEA-1814 (input 3) | `bucket one` | contains a space |

### reuse-existing
- None — no fixture bucket needed; the whole point of the case is that
  creation is rejected before any bucket exists.

### Shared expected error text (all 4 rows)
- `"Name should start with a letter and contain only letters, numbers, and hyphen"`
  — confirmed live, byte-identical to `CreateBucket.jsx`'s yup `.matches(...)`
  message for all 4 inputs (single shared validation rule, single shared
  message — there is no per-character-class message variant).

## Test Steps

Run once per Test Data row (`${INVALID_NAME}` = the row's value):

1. Navigate to `${BASE_URL}/artifacts` (case ELITEA-1811 step 1 / ELITEA-1814
   step 1). **Verify**: `artifacts-buckets-heading` visible
   (`ArtifactsPage.wait_for_page_load()` already asserts this).
2. Click `artifacts-create-bucket-button` (ELITEA-1811 step 2 / ELITEA-1814
   step 2, and — for rows 3 and 4 — ELITEA-1814's "repeat steps 1-4" re-entry
   into the form). Reuse `click_create_bucket_button()`.
   **Verify**: URL becomes `${BASE_URL}/artifacts/create-bucket`.
3. Fill `artifacts-bucket-name-input` with `${INVALID_NAME}` via
   `fill_bucket_name()` (ELITEA-1811 step 3 / ELITEA-1814 step 3).
   **Verify**: field value equals `${INVALID_NAME}` exactly (confirmed live —
   the field never sanitizes/rejects characters on input; it accepts the
   literal string as typed, for all 4 values).
4. Click `artifacts-bucket-save-button` with a plain `.click()` — **do NOT**
   reuse `ArtifactsPage.click_bucket_save_button()` here (see § Automation
   Hints — that helper blocks on a POST response that never fires for an
   invalid name). (ELITEA-1811 step 4 / the implicit Save click inside
   ELITEA-1814 step 5.)
5. **Verify** (ELITEA-1811 step 5 / ELITEA-1814 step 4+5, folded — see
   § Coverage Map note on step-order):
   - `artifacts-bucket-name-input`'s `aria-invalid` attribute == `"true"`
     (`ArtifactsPage.is_bucket_name_invalid()` — pre-existing method, already
     used by ELITEA-1817's Coverage Map for the *valid*-name inverse case).
   - The inline helper-text element (testid needed — see § Concrete Handles)
     has exact text `"Name should start with a letter and contain only
     letters, numbers, and hyphen"`.
   - `artifacts-bucket-save-button` has no `disabled` attribute — it remained
     clickable through the whole flow (confirmed live for all 4 values;
     explicitly required by ELITEA-1814 step 5's "Save button remains
     active", and true — but unstated — for ELITEA-1811 too, folded in as a
     shared assertion, see Axis 2).
   - No `POST .../artifacts/buckets` request is observed (confirmed live via
     `page.expect_response` timing out after the Save click for all 4
     values — the yup schema blocks `formik.onSubmit` client-side before any
     network call).
   - Current URL is still `${BASE_URL}/artifacts/create-bucket` (the form did
     not navigate away — consistent with no successful creation).
6. Navigate back to Artifacts root via `ArtifactsPage.navigate_to_artifacts()`
   (ELITEA-1811 step 6 "Click 'Artifacts'" / ELITEA-1814 steps 8 and 11 "Click
   to 'Artifacts'" — see § Concrete Handles for why this is a direct URL nav,
   not a sidebar click, same precedent as ELITEA-1809 step 15).
7. **Verify** `${INVALID_NAME}` does NOT appear in the bucket list — assert
   `ArtifactsPage.bucket_exists(INVALID_NAME) == False` (ELITEA-1811 step 7 /
   ELITEA-1814 steps 6, 9, 12).

## Expected Results
- For all 4 `${INVALID_NAME}` values: the inline validation error
  `"Name should start with a letter and contain only letters, numbers, and
  hyphen"` is shown, `aria-invalid="true"` on the Name field, the Save button
  stays enabled/clickable throughout, no bucket-creation `POST` fires, and no
  bucket with that name is ever created or listed.

## Coverage Map

**Axis 1 — Case coverage** (one row per row-1811 element, then per
row-1814 element; disposition `asserted` unless noted):

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| ELITEA-1811 step 1: Navigate to Artifacts | Artifacts page loads | step 1 | `artifacts-buckets-heading` visible | asserted |
| ELITEA-1811 step 2: Click create-bucket icon | "New Bucket" form opens | step 2 | URL == `/artifacts/create-bucket` | asserted |
| ELITEA-1811 step 3: Enter "1bucket" | Field shows "1bucket" | step 3 (row 1) | field value check | asserted |
| ELITEA-1811 step 4: Click Save | Save is attempted | step 4 (row 1) | click fires, no POST observed | asserted |
| ELITEA-1811 step 5: Inline validation error shown | exact message shown | step 5 (row 1) | helper-text exact-text match | asserted |
| ELITEA-1811 step 6: Click "Artifacts" | Nav to Artifacts root | step 6 (row 1) | URL == `/artifacts` (via `navigate_to_artifacts()`, see note below) | asserted *(mechanism substituted — see note)* |
| ELITEA-1811 step 7: "1bucket" not in list | not present | step 7 (row 1) | `bucket_exists("1bucket") == False` | asserted |
| ELITEA-1814 step 1: Navigate to Artifacts | page loads | step 1 (all rows) | same as above | asserted |
| ELITEA-1814 step 2: Click create-bucket icon | form opens | step 2 (all rows) | same as above | asserted |
| ELITEA-1814 step 3: Enter "new-bucket$" | field accepts input | step 3 (row 2) | field value check | asserted |
| ELITEA-1814 step 4: Inline error shown | error shown | step 5 (row 2) | helper-text exact-text match | asserted *(order folded — see note)* |
| ELITEA-1814 step 5: Save stays active, click doesn't create bucket | button active, no creation | step 4+5 (row 2) | no `disabled` attr + no POST | asserted |
| ELITEA-1814 step 6: "new-bucket$" not in list | not present | step 6+7 (row 2) | `bucket_exists(...) == False` | asserted |
| ELITEA-1814 step 7: Repeat 1-4 with "bucket_one" | form re-opens, name entered | steps 1-3 (row 3) | same as row 1's steps | asserted |
| ELITEA-1814 step 8: Click "Artifacts" | nav to root | step 6 (row 3) | via `navigate_to_artifacts()` | asserted *(mechanism substituted)* |
| ELITEA-1814 step 9: Error shown, "bucket_one" not in list | error + absent | step 5+7 (row 3) | helper-text + `bucket_exists == False` | asserted |
| ELITEA-1814 step 10: Repeat 1-4 with "bucket one" | form re-opens, name entered | steps 1-3 (row 4) | same as row 1's steps | asserted |
| ELITEA-1814 step 11: Click "Artifacts" | nav to root | step 6 (row 4) | via `navigate_to_artifacts()` | asserted *(mechanism substituted)* |
| ELITEA-1814 step 12: Error shown, "bucket one" not in list | error + absent | step 5+7 (row 4) | helper-text + `bucket_exists == False` | asserted |

**Notes on dispositions:**
- **Mechanism substitution (both cases' "Click 'Artifacts'" steps).** Live
  source read of `SidebarBody.jsx`/`SidebarMenuItem.jsx` confirms the left
  sidebar's nav entries render via a SHARED component with no `data-testid`
  on any entry (same finding already logged by ELITEA-1809's implementer
  amendments). Adding one would require threading a `testId` prop through
  every sidebar item (Chat, Agents, Skills, ...), a broad shared-component
  change out of proportion to this case. Implemented via the existing
  `ArtifactsPage.navigate_to_artifacts()` (direct URL nav) instead — the SAME
  mechanism the case's own "Navigate to Artifacts" step already uses to reach
  the identical observable (URL becomes `${BASE_URL}/artifacts`). The
  interaction *mechanism* changes; the asserted *outcome* does not.
- **Step-order fold (ELITEA-1814 rows only).** The case text's step 4 ("verify
  inline error") appears to precede step 5's explicit Save click in the
  written numbering, while live exploration confirms the error is NOT visible
  immediately after typing (touched state is false until the field blurs OR
  the form is submitted — confirmed live: `aria-invalid` stays `"false"`
  right after `type()`, and only flips to `"true"` after either a blur or a
  Save click). Two live-confirmed ways reach the same observable: (a) blur
  the field without saving — error already appears; or (b) click Save
  directly (ELITEA-1811's literal order) — same error appears, AND the Save
  click's own no-op-on-invalid-input behavior is exercised in the same step.
  This spec standardizes on (b) for all 4 rows (folds case-1814's steps 4+5
  into one AFS step) because it is simpler, deterministic, and additionally
  exercises the Save-click no-op behavior that both cases care about — no
  observable requirement is lost since the SAME error text is asserted
  either way. **Classification:** case-text ambiguity in step ordering, not a
  product defect (reverse-masking guard) — not filed as a CLARIFICATION
  since no other reader would misautomate a different, wrong behavior from
  it (the ambiguity resolves to the same live outcome under either
  interpretation).

**Axis 2 — Analyst additions** (beyond what either case explicitly asked for):
- `step 5`, all rows: asserted the Save button carries no `disabled` attribute
  — explicitly required by ELITEA-1814 but NOT stated by ELITEA-1811; added
  to ELITEA-1811's row too for consistency, since it is empirically the same
  underlying Save-button-enablement logic in `CreateBucket.jsx` (the
  `disabled` prop only checks `isCreating || isUpdating || !name ||
  name.length === 0 || name.length > 56` — never the regex) and asserting it
  once per row costs nothing extra.
- `step 5`, all rows: asserted no `POST .../artifacts/buckets` fires at all
  (both cases only state "no bucket is created", which is agnostic to
  whether a rejected request even reaches the network) — added because it is
  a stronger, more specific guarantee (client-side validation blocks the
  call entirely, vs. e.g. a server-side 400 that a weaker implementation
  might rely on) and was directly observed during exploration (a
  `page.expect_response` wait timed out for all 4 values).
- `step 3`, all rows: asserted the field accepts the invalid value verbatim
  (no client-side input masking/rejection) — confirmed live and worth
  guarding since a future "reject keystrokes" UX change would otherwise
  silently break this test's premise without any assertion catching it.

## Cleanup
- None required — no bucket is ever successfully created by any of the 4
  Test Data rows; there is nothing to delete.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Artifacts page heading | `artifacts-buckets-heading` (existing `LocatorDescriptor`) | on-automation/testids only (awaiting human promotion to main — same status as all sibling artifacts testids, e.g. ELITEA-1809/1817) | `ArtifactsPage.wait_for_page_load()` already asserts it |
| Create-bucket icon | `artifacts-create-bucket-button` (existing) | on-automation/testids only | `click_create_bucket_button()` |
| Name field | `artifacts-bucket-name-input` (existing) | on-automation/testids only | `fill_bucket_name()`; also reads `aria-invalid` via `is_bucket_name_invalid()` |
| Save button | `artifacts-bucket-save-button` (existing) | on-automation/testids only | plain `.click()` for this flow — **do not** use `click_bucket_save_button()` (see Automation Hints) |
| **Inline validation message** | **`testid needed: artifacts-bucket-name-helper-text`** | **needs-adding** | `CreateBucket.jsx`'s `<TextField>` (line ~222) renders the yup error via its `helperText` prop with NO testid on the rendered `<p class="MuiFormHelperText-root">` today — confirmed live (`.MuiFormHelperText-root` count is 0 while valid, 1 with the exact expected text once invalid). Precedent for the exact fix shape already exists in this repo: `GenerateSkillReviewForm.jsx` wires `slotProps={{ formHelperText: { 'data-testid': 'generate-skill-review-name-helper-text' } }}` on an MUI `TextField`. `CreateBucket.jsx` currently uses the older `inputProps` prop (not `slotProps`) for its own name-input testid, so the same-file-consistent fix is `FormHelperTextProps={{ 'data-testid': 'artifacts-bucket-name-helper-text' }}` alongside the existing `inputProps` — MUI v5 supports both prop shapes on the same `TextField`. Naming follows `{section}-{element}-{type}`: `artifacts` (section) + `bucket-name` (element) + `helper-text` (type), verified unique via grep. |
| Bucket list absence check | `ArtifactsPage.bucket_exists(name)` (existing, pre-testid-policy `get_by_text` — tracked tech debt #25/#42, reused as-is, not newly introduced) | n/a | returns `False` when not present |
| Return-to-Artifacts navigation | `ArtifactsPage.navigate_to_artifacts()` (existing) | n/a | substitutes for the sidebar "Artifacts" click — see Coverage Map note; sidebar nav items carry NO testid at all (shared `SidebarMenuItem.jsx`, confirmed live + matches ELITEA-1809's identical finding) |

## Network Behavior
- **No** `POST {API_BASE}/artifacts/buckets` fires for any of the 4 invalid
  names — confirmed live via `page.expect_response(...)` timing out (5s) on
  every attempt. This is the key technical fact distinguishing this family
  from ELITEA-1809's duplicate-name case (which DOES reach the network and
  gets a 400 back) — here the yup schema blocks `formik.handleSubmit`
  entirely client-side; the implementer must not wait on a response that
  will never arrive.

## Known Defects Found During Exploration
- None found. Live behavior matches both cases' expected results exactly for
  all 4 invalid-name values.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`); page object
  `automation/pages/artifacts_page.py` (`ArtifactsPage`) already has every
  method this family needs except the new helper-text handle.
- **Do not reuse `ArtifactsPage.click_bucket_save_button()` for the invalid-name
  path.** That helper wraps the click in
  `page.expect_response(lambda r: "artifacts/buckets" in r.url and
  r.request.method == "POST", ...)` — correct for the happy path (ELITEA-1808/
  1817), but for an invalid name **no such request ever fires**, so the
  helper will hang for its full timeout and then raise. Use a plain
  `self.bucket_save_button.click()` for this family instead (new
  page-object method, e.g. `click_bucket_save_button_expect_no_request()`,
  or simply call `.click()` directly on the existing `bucket_save_button`
  `LocatorDescriptor` field from the test/spec — the field itself is already
  compliant testid-only).
- Parameterize the 4 Test Data rows via `@pytest.mark.parametrize` (or
  equivalent) over one shared test body implementing the Test Steps above —
  this is exactly the "one parameterized spec" shape the family
  classification calls for.
- **MCP Playwright server unavailable this session** — `ToolSearch` returned
  no `browser_navigate`/`browser_snapshot`/etc. tools despite `.mcp.json`
  declaring the `playwright` server; fell back to a direct Python
  `playwright.sync_api` scratch script (discarded after this run, not
  committed) driving the SAME `ArtifactsPage` methods the implementer will
  use, per `browser-tools.md`'s CLI/scratch-run fallback tier. Every
  handle/behavior above was confirmed against the live DOM this way, not
  guessed from source reading alone (source reading was used only to
  *explain why* the observed behavior occurs, e.g. the `disabled` prop's
  exact condition list).
- Reuse the `${TEST_USER}` / `auth_state` localhost fast-path already used by
  every sibling artifacts spec — no new fixture needed.
