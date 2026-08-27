# Test Case: Secret name must be unique within the project

## Metadata
- **TMS ID**: ELITEA-2341
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2341.md` (intake snapshot)
- **Priority**: l2 (case frontmatter `priority: high`) → **pytest marker `@pytest.mark.p1`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: none — the product matches the case text on every step.

## Preconditions
- Project `Private` (399).
- The case's step 2 says "note the name of any existing secret". The test **creates its
  own** existing secret first: colliding on a REAL project secret would mean typing a
  live secret's name into a create form and depending on shared data that any other run
  may delete. The created secret is the "existing" one for the collision, and is removed
  in teardown.

## Test Data
### generate-per-run
- `secret_name`: `autotest_unique_<uuid4-hex[:8]>` — created once, then re-used as the
  duplicate.
- `original_value`: `unique-original-<uuid4-hex[:8]>`
- `duplicate_value`: `unique-duplicate-<uuid4-hex[:8]>` — deliberately DIFFERENT, so the
  test can prove the rejected attempt did not silently overwrite the original value.

## The product's actual uniqueness contract (source + live confirmed 2026-08-27)

- **No client-side uniqueness check exists.** `EditSecretInputGridTable.jsx` validates only
  the character class, so with a duplicate name typed the Save (✓) is **enabled** and no
  `secret-name-error` renders — live-confirmed
  (`saveDisabled: false`, `nameErrorText: null`, `helperTexts: []`).
- Uniqueness is enforced **server-side**: clicking ✓ fires
  `POST /api/v2/secrets/secrets/default/399` → **400 Bad Request** (live-confirmed; the
  browser also logs the usual `Failed to load resource … 400` console line for it).
- `useSecretRowUpdate.hooks.js` returns the row untouched on `responseResult.error`, so the
  pending row **stays in edit mode** with the typed name still in the input — live:
  `stillEditing: true`, `editingNameValue: "<name>"`.
- `SecretsTable.jsx`'s `isAddingError` effect raises an **error toast** via
  `buildErrorMessage(addingError)`; live text captured verbatim:

  ```
  Secret "autotest_w05_base_a1b2c3d4" already exists
  ```

  (`toastError` ⇒ `data-severity="error"`, `TOAST_DURATION_DEFAULTS.error` = **10 s**.)
- **No duplicate row is created**: the name-cell count for that name stayed **1**
  throughout, and the pagination total did not grow beyond the +1 the *pending* row
  contributes client-side (digest § Inline create flow).

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`; verify the page title is `Secrets`.

2. **(Case step 2 — made deterministic)** Create the run-unique secret via the inline "+"
   flow with `original_value`.
   - **Verify**: the create `POST` resolves **201 Created**; the row exists (count 1);
     this is the "existing secret" whose name step 3 will collide with.

3. **(Case step 3)** Click **+** again and enter the SAME name in the new inline row, plus
   `duplicate_value`.
   - **Verify**: the inputs hold exactly those values.
   - **Verify (Axis 2)**: `secret-row-save-button` is **enabled** and `secret-name-error`
     is absent — the product's real contract is *server-side* uniqueness, and recording it
     here is what stops a future reader from "fixing" the test toward a client-side error
     that does not exist.

4. **(Case step 4)** Click the ✓ checkmark to save, watching the network.
   - **Verify**: the create `POST` to `/secrets/secrets/default/{project_id}` resolves
     **400 Bad Request** (the rejection is a system-produced observable, not a UI guess).

5. **(Case step 5)** Verify a validation error is shown.
   - **Verify**: `toast-alert` is visible with `data-severity="error"` and `toast-message`
     text is exactly `Secret "<secret_name>" already exists`.

6. **(Case step 6)** Verify no duplicate secret is created.
   - **Verify**: after cancelling the still-open pending row, the number of rows whose
     `secret-name-cell` equals `secret_name` is exactly **1** (search-filtered to that
     name, so the count is unambiguous across the 121-secret project).
   - **Verify (Axis 2)**: reload the page and re-assert the count is 1 — a genuine server
     round-trip, so a client-side-only "no duplicate" cannot pass.
   - **Verify (Axis 2)**: the surviving secret still holds the **original** value — reveal
     it via the row eye toggle and assert the revealed text == `original_value` (≠
     `duplicate_value`). "No duplicate created" would still be satisfied by a silent
     overwrite; this is the assertion that distinguishes rejection from upsert.

7. **(Axis 2)** Verify the rejected pending row stayed in edit mode with the typed name
   intact after the 400 (the user's input is not destroyed by the failure).

8. **(Axis 2)** No unexpected console errors — **the 400's own
   `Failed to load resource … 400` line is EXPECTED here** and is filtered by URL +
   status, exactly as `#1203` is filtered by text. Anything else still hard-fails.

**Teardown (mandatory, not a case step):** API
`DELETE /secrets/secret/default/{project_id}/{name}` → 204.

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title / add button | `secrets-page-title` / `secrets-add-button` | on-`automation/testids` | existing fields |
| Name / value inputs | `secret-name-input` / `secret-value-input` | on-`automation/testids` | existing fields |
| Save (✓) / Cancel (✗) | `secret-row-save-button` / `secret-row-cancel-button` | on-`automation/testids` | existing fields |
| Inline name error (asserted ABSENT) | `secret-name-error` | on-`automation/testids` | existing field |
| Row / name cell | `secret-row` / `secret-name-cell` | on-`automation/testids` | existing fields |
| Search input | `secrets-search-input` | on-`automation/testids` (EliteaAI/EliteaUI@249c0186) | existing field |
| Eye toggle + revealed value cell | `secret-row-visibility-toggle-button` / `secret-value-cell` | on-`automation/testids` | existing fields (ELITEA-2343) |
| Toast container / message | `toast-alert` (+ `[data-severity="error"]`) / `toast-message` | on-`main` — generic `Toast.jsx` | **new `LocatorDescriptor`s on `SecretsPage`** (shared with ELITEA-2335) |

**Zero new testids needed.**

## Assertion shape / Fidelity
The oracles are all system-produced: the 201 and the 400 on the wire, the toast the
product rendered, the row count after a real reload, and the revealed plaintext from a
fresh `GET …/secret/default/{pid}/{name}`. No `page.route`, no `route.fulfill`, no
injected state, no mocked client.

## Implementer notes
- Page-object additions on `SecretsPage`: the `toast_alert` / `toast_message` descriptors
  + `TOAST_ALERT_SEVERITY` constant (shared with ELITEA-2335), and a
  `click_save_button_expect_error()`-shaped helper **or** reuse of `click_save_button()`
  with a status assertion — the existing `click_save_button()` already waits on the create
  `POST` response and returns it, so **check whether it asserts 201 internally**; if it
  does, add an additive variant rather than changing it (it has merged callers).
- The error toast lives **10 s**, so it is comfortably assertable — but still use
  web-first `expect(...).to_have_text(...)`, never a one-shot read.
- The pending row must be cancelled before counting rows: while it is open the name
  appears in an *input*, not in a `secret-name-cell`, so the count is unaffected — but
  leaving it open blocks the "+" button and the reveal toggle.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → Secrets | page loads | Step 1 | `secrets-page-title` == "Secrets" | asserted |
| Step 2: note the name of an existing secret | a known existing name (created run-unique) | Step 2 | create `POST` 201 + row count 1 | asserted |
| Step 3: click "+" and enter the same name | accepted client-side (no uniqueness check) | Step 3 | input values + Save enabled + no inline error | asserted |
| Step 4: click ✓ to save | create `POST` → 400 | Step 4 | response status == 400 | asserted |
| Step 5: a validation error is shown | error toast `Secret "<name>" already exists` | Step 5 | `toast-alert[data-severity="error"]` + exact `toast-message` | asserted |
| Step 6: no duplicate secret is created | exactly one row with that name | Step 6 | filtered name-cell count == 1,re-asserted after reload | asserted |
| Expected Final State: no duplicate created | as step 6, and the original is unmodified | Step 6 | count == 1 + revealed value == `original_value` | asserted |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| the surviving secret still holds the ORIGINAL value | "no duplicate created" is also satisfied by a silent overwrite — the far worse outcome, and the case never checks it |
| Save is enabled / no inline error with a duplicate name | records the real (server-side-only) contract so nobody later "repairs" the test toward a client-side error the product does not implement |
| the count survives a page reload | server round-trip, not client cache |
| the rejected row keeps the typed name in edit mode | the user's input must survive a rejected save |
| console-error axis filters the expected 400 by URL+status, not blanket | keeps a genuinely new console error hard-failing |

## Known Defects / Clarifications
- **#1203 (OPEN)** — React "Maximum update depth exceeded" on mount; isolated soft failure.
- Case-text wording: the case illustrates the error as "e.g. 'Secret with this name
  already exists'"; the live text is `Secret "<name>" already exists`. The "e.g." makes it
  an illustration, not a contract ⇒ **no clarification filed**; the AFS asserts the live
  text exactly.

## Blocked Steps
None.
