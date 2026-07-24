# Test Case: Credential — Duplicate/Mismatch Validation

## Metadata
- **TMS ID**: ELITEA-1978
- **Linked Story**: none
- **Priority**: l2 (case frontmatter: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual` — same gap already flagged by ELITEA-1971/1975's
  AFS (no documented TMS case-gate exclusion list in `.agents/testing.md`);
  proceeded and executed the case end-to-end per the skill's default.
- **Browser lane note**: the shared Playwright MCP browser (lane 0) was
  contended by another concurrent session at dispatch time (`Error: Browser
  is already in use for .../mcp-chrome-70a4838`). Fell back to an isolated
  `browser-verify` (CDP) Chrome instance (own `--remote-debugging-port`, own
  `--user-data-dir`) per team practice — same fallback pattern already
  logged in qa-engineer memory for ELITEA-2219.
- **Testid note (per dispatch instruction):** every locator this AFS uses
  already exists live — landed via ELITEA-1962/1971/1975's `add-data-testid`
  work — and is used directly instead of being flagged as a gap. **One NEW
  gap was found and must be added**: the duplicate-name error banner has no
  testid at all (see Concrete Handles).
- **Classification note (declared improvisation, `.agents/testing.md` §
  Merge gate "Analysis-time entry", 2026-07-23):** a defect was found during
  this analysis (Known Defects #1, filed as
  [#1004](https://github.com/EliteaAI/elitea-testing-public/issues/1004)).
  It is classified `ready-for-automation`, not `defect-found`, because it
  sits at the tail of the case (Step 5-6) and does not block completing or
  asserting the rest of the case (Steps 1-4 pass exactly as specified). The
  affected assertion is written as the correct (buggy) live behavior via
  `expect.soft()` + `# Known defect: #1004`, per this bullet.

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state` fixture).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Credentials section is reachable and the project already has at least
  one credential (avoids the known `CredentialsList.jsx` zero-credential
  auto-redirect — same precondition note as ELITEA-1962's AFS; live-confirmed
  the project already has 3 pre-existing credentials, so no seed is needed
  for THIS case, unlike ELITEA-1962's throwaway-seed pattern).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Duplicate credential display name: `autotest_duplicate_cred_${timestamp}`
  — **NOT** the case's literal, unsuffixed `autotest_duplicate_cred`. Every
  sibling credential test in this suite timestamps its display names to
  avoid cross-run collisions on re-runs (`test_credential_create.py`,
  `test_credential_required_fields_validation.py`, etc.) — the SAME
  timestamped name is deliberately reused for BOTH the first (successful)
  and second (duplicate-rejected) creation attempts within one test run, so
  the "same Display Name twice" invariant the case tests is preserved while
  the value itself stays run-unique.
- Second, unrelated display name for the empty-required-field scenario:
  `autotest_reqfields_emptytoken_${timestamp}` (GitHub type, Token auth,
  Access Token deliberately left empty — this credential DOES get
  persisted, per Known Defects #1, and must be deleted in teardown).
- Credential type: `github` (case's own Test Data table; `Base Url` ships
  with a live default `https://api.github.com`, so only Display Name is
  needed to enable Save for the duplicate-name scenario — same
  type-selection nuance already documented in ELITEA-1975's AFS
  Preconditions note, not re-litigated here since it doesn't affect this
  case's own steps).

## Test Steps

1. Navigate to the credential creation form for type `github`
   (`${BASE_URL}/credentials/create-credential/github`, direct URL per
   `CredentialCreatePage.navigate_to_type()` — avoids the zero-credential
   card-click auto-redirect quirk documented in that method's docstring).
   - **Verify**: form renders with Display Name empty, Save disabled.
2. Fill Display Name with `autotest_duplicate_cred_${timestamp}`.
   - **Verify**: Save (`credential-form-save-button`) becomes enabled
     (Base Url pre-filled, Anonymous is the default auth method — confirmed
     live via `document.querySelector(...).disabled === null`).
3. Click Save.
   - **Verify**: `POST /configurations/configurations/{project_id}` returns
     200; UI redirects to `/credentials/all`; a card with exactly this
     Display Name appears in the list (`entity_card_name` filtered by text,
     count 1) — confirmed live (credential id `1916` in this run, deleted
     via API afterward as this run's own cleanup).
4. Navigate to the credential creation form for type `github` again (fresh
   navigation, same URL as step 1).
   - **Verify**: form renders empty again (new instance, no residual state
     from step 2's created credential).
5. Fill Display Name with the **same** value used in step 2
   (`autotest_duplicate_cred_${timestamp}`).
   - **Verify**: Save becomes enabled — confirmed live
     (`disabled === null`); the client performs **no** ahead-of-time
     duplicate-name check, matching the case's own Step 2 expected result
     ("Credential creation form is submitted").
6. Click Save.
   - **Verify — case's central assertion, PASSES exactly as specified.**
     - The POST is rejected; the UI does **not** redirect — it stays on
       `/credentials/create-credential/github`.
     - An error message reading **exactly**
       `Credential with ID 'autotest_duplicate_cred_${timestamp}' already
       exists` appears on the page — confirmed live via
       `document.body.innerText` containing that literal string, matching
       the case's Step 3 expected result verbatim (only the injected
       timestamp differs from the case's literal example name).
     - Confirmed via DOM query that the rendering element is a bare
       `<div class="MuiTypography-root ...">` with **no `data-testid`**
       (`el.getAttribute('data-testid') === null`) — this is the ONE new
       testid gap this AFS surfaces (see Concrete Handles).
     - The disabled "ID" field (`toolkit-field-elitea_title-input`) stays
       disabled (its `disabled` attribute unchanged) — confirms the
       backend's error response's `field` was NOT `elitea_title` for this
       error shape (the `onEnableEditTitle()` branch in
       `CredentialTabBar.jsx`'s `doSave()` did not fire); the message
       instead surfaces via the generic `apiError` banner path.
     - **Implementer correction (2026-07-24, Phase 2 amend-in-PR):** the
       bullet above is **WRONG** — re-verified via a direct API probe
       (bypassing the UI: POST the same duplicate-name payload twice
       through `CredentialAPI` directly) that the backend's actual error
       body for this exact error IS
       `{"error": "Credential with ID '...' already exists", "field":
       "elitea_title"}`. This DOES match
       `CredentialsTabBar.jsx`'s `doSave()` gate
       (`result.error?.data?.field === 'elitea_title'`), firing
       `onEnableEditTitle()` → `enableEditEliteaTitle: true` →
       `ToolBase.jsx`'s `disabled = ... || (k === 'elitea_title' &&
       !enableEditEliteaTitle)` evaluates to **false** — the ID field
       becomes **editable**, not disabled, immediately after the rejection.
       Live-reproduced via the actual Playwright test (not just the probe)
       on this same run — `create_page.id_input.is_disabled()` is `False`
       post-rejection. The message-surfacing-via-generic-banner half of the
       original claim still holds (the error text itself doesn't route to
       a per-field validation message — that's a separate, correct
       observation); only the ID-field-disabled-state half was wrong. Not
       filed as a product defect — this is the CORRECT, arguably-intended
       UX (unlock the ID field so the user can change the conflicting
       value) — just an analyst observation error, corrected here per the
       reverse-masking guard (`.agents/testing.md`/`implementer-contract.md`
       § Hard Rules → 2). The implementer's test asserts the live-verified
       contract (`not is_disabled()`), not the original claim.
     - Console: clean (no error/warning-level messages) at the moment of
       observation — this is a handled, expected-path error, not a thrown
       exception.
     - Exactly ONE credential with this Display Name exists in the list
       afterward (re-verified via `list_all_credentials()` / list-page
       re-navigation) — the duplicate attempt did not create a second
       record.
7. (Separate fresh navigation — empty-required-field scenario, case Steps
   5-6.) Navigate to the credential creation form for type `github` again;
   leave every field at its initial (empty/default) state.
   - **Verify**: Save is disabled — `disabled` attribute present (`""`),
     confirming the general "empty required field blocks Save" mechanism
     works at baseline (matches the case's own generic Step 5 wording; the
     mechanism itself — for `label`/`base_url`/`api_key`/`username`-style
     statically-required fields — is already proven end-to-end by the
     MERGED `l1_create-credential-required-fields-validation_ELITEA-1975.md`
     spec and its `test_credential_required_fields_validation.py`
     implementation; not re-derived here, only load-bearing enough to
     confirm the baseline still holds on this credential type before
     Step 8 isolates the specific defect).
8. Fill Display Name with `autotest_reqfields_emptytoken_${timestamp}`,
   then select the **Token** auth-method radio
   (`toolkit-field-auth-radio-token`) — the case's own literal example field
   ("empty Client Id or **Token**"). Leave the resulting "Access Token"
   field (`toolkit-field-access_token-input-field`) empty.
   - **Verify — DEFECT, filed as
     [#1004](https://github.com/EliteaAI/elitea-testing-public/issues/1004).**
     Expected (case Step 6): a required-field validation indicator appears
     next to "Access Token" and Save remains disabled. Actual: the "Access
     Token" label carries **no asterisk** (confirmed via
     `document.body.innerText` — `"...Access TokenSecretPassword..."`, no
     `*`, unlike `"Display Name * *ID * *Base Url * *"` earlier in the same
     dump) and Save's `disabled` attribute stays `null` throughout —
     reproduced twice (fresh page loads, native CDP input events, no
     synthetic dispatch — pristine-gesture gate satisfied). Use
     `expect.soft()` + `# Known defect: #1004` for this specific assertion
     so the rest of the test still runs and stays RED until the fix ships.
9. Click Save (Access Token still empty).
   - **Verify — DEFECT, same #1004, functional (not just cosmetic)
     dimension.** The POST is accepted (200); the UI shows "The credential
     has been created successfully"; a follow-up
     `GET /configurations/configuration/{project_id}/{id}` shows the
     persisted record with `"data": {"access_token": "", ...}` and
     `"status_ok": false` — a listed, nameable, but non-functional
     credential now exists. `expect.soft()` this too (backend-accepts-empty
     is part of the same filed defect, not a second ticket — see Known
     Defects #1's "Impact" note).
   - **Implementer correction (2026-07-24):** live-verified via the real
     Playwright test (not just re-reading the analyst's claim) that the
     persisted `data.access_token` reads back as **`None`/key-absent**, not
     the literal empty string `""` the AFS states above — same underlying
     defect (a falsy/absent access_token was accepted and persisted), just
     a JSON-shape difference from this bullet's exact wording. The
     implementer's test treats any falsy value (`None` or `""`) as the
     confirmed defect signature. `status_ok: false` matched exactly as
     stated.

## Expected Results
- Steps 1-6 (duplicate Display Name): pass exactly as the case specifies —
  the second Save attempt is rejected with the literal error message
  `Credential with ID '<name>' already exists`, no duplicate record is
  created, no console errors.
- Steps 7-9 (empty required field): the GENERAL mechanism (Step 7, no
  fields filled) passes; the SPECIFIC case-named example (Step 8-9, empty
  Token with Token auth selected) fails — filed as #1004, asserted with
  `expect.soft()` so this doesn't block reporting the rest of the case as
  green.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture (localhost dev token) | asserted |
| Precondition: project + Credentials section accessible | — | AFS Preconditions | project `399`, `/credentials/create-credential/github` loads | asserted |
| 1 Create credential "autotest_duplicate_cred" (Github) | created successfully | steps 1-3 | step 3: POST 200 + card appears in list, count 1 | asserted *(name timestamped — see Test Data)* |
| 2 Attempt to create another credential, same Display Name | form is submitted | steps 4-5 | step 5: Save enabled, no client-side pre-check | asserted |
| 3 Click Save | error "Credential with ID '...' already exists" shown | step 6 | step 6: `document.body.innerText` contains the literal message | asserted |
| 4 Verify duplicate error/warning visible (or save prevented) | error visible to user | step 6 | step 6 (same observation as case element 3 — case's steps 3-4 describe the same single event from two angles) | asserted *(decomposed: same AFS step covers both)* |
| 5 Attempt to save with empty required fields (e.g. Client Id or Token) | Save disabled or validation triggers | steps 7-9 | step 7: baseline (all empty) correctly disables Save; steps 8-9: the case's own named example (Token) does NOT disable Save | **step 7 asserted; steps 8-9 FAILED — defect, see Known Defects #1** |
| 6 Verify required-field validation indicators appear, Save disabled | indicators shown, Save not allowed | step 8 | step 8: no asterisk appears next to "Access Token"; Save stays enabled | **FAILED — defect, see Known Defects #1** |
| Expected Final State: duplicate names prevented; empty required fields block saving | — | steps 1-9 | steps 1-9 jointly | **partially asserted — duplicate-detection (steps 1-6) fully correct; empty-required-field blocking (steps 7-9) correct only for statically-required fields, not for the auth-conditional Access Token field named by the case's own example** |

### Axis 2 — Analyst additions

- step 6 additionally asserts the `elitea_title`/ID field's state changes
  to editable (**corrected post-analysis, see the Step 6 implementer
  correction note above** — the `onEnableEditTitle()` field-specific error
  branch DOES fire for this error, per a direct API probe of the backend's
  actual error body) and that the error also renders via the generic
  `apiError` banner (both can be true simultaneously — the banner surfaces
  the message text, the field-specific branch independently unlocks the ID
  field) — *added: pins down exactly which of `CredentialTabBar.jsx`'s
  error-handling branches this error shape takes, useful context for
  whoever eventually fixes/tests #1004's sibling scenarios (Password/App
  private key auth).*
- step 6 asserts exactly one card with the duplicate name exists afterward
  — *added: the case's Pass criteria explicitly names "Duplicate credential
  is saved without error" as a Fail condition; a list-level count is the
  most direct way to rule that out, not just the absence of a redirect.*
- step 9 asserts the backend-persisted record's `data.access_token` and
  `status_ok` fields via a direct API GET — *added: distinguishes a
  cosmetic-only gap (missing asterisk) from a functional one (backend also
  accepts the empty value) — the case's own Fail criteria ("empty required
  fields allow saving") is about the functional outcome, not just the
  indicator, so this confirms the failure is real, not merely visual.*
- step 8's console-clean check — *added: standard side-channel discipline;
  confirms this is a silent logic gap, not a thrown/logged error.*
- "zero console errors/warnings across the whole flow" — *added: same
  standard discipline as every sibling credential AFS in this feature.*

## Cleanup
1. Delete both credentials created during this run via the API
   (`credential_api.delete_credential(id)`), in a `finally` block: the
   step-3 successful duplicate-name-source credential, and the step-9
   empty-Access-Token defect credential. The duplicate SAVE attempt at
   step 6 is rejected server-side — nothing to clean up for that attempt
   itself.
2. No route interception or mocked network needs explicit teardown beyond
   the normal per-test browser context lifecycle.

## Concrete Handles (discovered during exploration)

All handles below were verified live against `http://localhost:5173` AND
cross-checked in EliteaUI source (`git fetch origin` run in `../EliteaUI`
immediately before this check). **PROVENANCE for every existing handle:
on `automation/testids` only — awaiting human promotion to `main`** (the
literal rendered testid strings never appear in source as bare strings —
each is a template composition; the TEMPLATE PATTERNS were verified absent
from `origin/main` and present on `origin/automation/testids` / local
working tree, which are identical, HEAD `043ea101`).

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Credential type card (create-form entry, `CategoryItemCard.jsx:14`) | `page.get_by_test_id("toolkit-type-card-github")` — dynamic template `` `toolkit-type-card-${itemKey}` `` — **existing, class field `CredentialCreatePage.TYPE_CARD_SELECTOR`** | automation/testids only | `page.get_by_text("Github", exact=True)` scoped to the type grid (not needed — direct-URL nav bypasses this card per `navigate_to_type()`) |
| Display Name field (`ToolBaseProperty.jsx:615`, generic path, `k === 'label'`) | `page.get_by_test_id("toolkit-field-label-input")` — **existing, `CredentialFormFieldsMixin.display_name_input`** | automation/testids only | `page.get_by_role("textbox", { name: "Display Name" })` |
| ID field, disabled (`ToolBaseProperty.jsx:615`, `k === 'elitea_title'`) | `page.get_by_test_id("toolkit-field-elitea_title-input")` — **existing, `CredentialFormFieldsMixin.id_input`** | automation/testids only | `page.get_by_role("textbox", { name: "ID" })` |
| Save button (`CredentialsTabBar.jsx:222`, static string) | `page.get_by_test_id("credential-form-save-button")` — **existing, `CredentialFormFieldsMixin.save_button`** | automation/testids only | `page.get_by_role("button", { name: "Save" })` |
| Auth-method radio, "Token" option (`ToolSection.jsx:291` base `` `toolkit-field-${sectionKey}-radio` `` + `RadioButtonGroup.jsx:37` `` `${testId}-${item.value...}` `` suffix — two-hop composition) | `page.locator(CredentialCreatePage.AUTH_METHOD_RADIO.format("token"))` → `[data-testid="toolkit-field-auth-radio-token"]` — **existing, `CredentialCreatePage.AUTH_METHOD_RADIO` template constant** | automation/testids only | `page.get_by_role("radio", { name: "Token" })` scoped to the Auth `radiogroup` |
| Access Token field (`ToolBaseProperty.jsx:340` base `` `toolkit-field-${k}-input` `` + `SecretField.jsx:77` `` `${...}-field` `` suffix — three-hop composition, GitHub's "Access Token" is the same underlying rendered field family as Jira's "Api Key" per ELITEA-1975's AFS) | `page.get_by_test_id("toolkit-field-access_token-input-field")` — **existing, `CredentialCreatePage.access_token_input`** | automation/testids only | `page.get_by_role("textbox", { name: "Access Token" })` scoped away from the Secret/Password toggle buttons |
| Duplicate-name / generic API-error banner (`CredentialForm.jsx:352-359`, `{apiError && <Typography>{apiError}</Typography>}`) | **testid needed** — `credential-form-api-error-message`, e.g. `<Typography data-testid="credential-form-api-error-message">{apiError}</Typography>`. Shared between Create and Edit flows (same `CredentialForm.jsx` component, both `CreateCredential.jsx` and `EditCredential.jsx` pass `apiError`/`setApiError` into it) — belongs on the SHARED `CredentialFormFieldsMixin`, not `CredentialCreatePage`-only, matching how `display_name_input`/`save_button`/`id_input` are already placed there. **Confirmed live: currently renders as a bare `<div class="MuiTypography-root ...">` with `data-testid === null`.** | **needs-adding** (genuine gap — no testid exists on either branch) | `page.get_by_text("already exists")` (fragile — couples to the exact backend error string; use only until the testid lands) |

## Network Behavior
- `POST /configurations/configurations/{project_id}` — fires on each Save
  click. Step 3: 200, returns the created credential's `id`/`label`/`type`/
  `elitea_title` (same shape as ELITEA-1962's AFS). Step 6: non-200 (exact
  status not asserted by the case; the case's Pass/Fail criteria are about
  the surfaced message, not the wire status code — if the implementer
  wants it, capture it via `page.expect_response()` around the click, same
  pattern as `test_credential_create.py`'s Step 7), response body's
  `message` field is the literal string rendered in the `apiError` banner
  (`buildErrorMessage()` in `src/common/utils.jsx` returns `err.data.message`
  verbatim when present — confirmed via source, not just inference). Step
  9: 200 despite the empty `access_token` (see Known Defects #1).
- `GET /configurations/configuration/{project_id}/{id}` — used only by
  this AFS's own verification (Step 9) and cleanup lookups, not part of the
  case's own UI flow.

## Known Defects Found During Exploration

1. **[MAJOR — filed as GitHub issue
   [#1004](https://github.com/EliteaAI/elitea-testing-public/issues/1004)]
   Create Credential form: empty Access Token is not validated as required
   when "Token" auth method is selected (GitHub credential type) — no
   asterisk indicator, Save never disables, and the backend independently
   accepts the empty value, persisting a non-functional credential
   (`status_ok: false`).**
   Root cause (source-confirmed): `EliteaUI/src/[fsd]/features/toolkits/lib/
   helpers/toolBase.helpers.js`'s `validateRequiredFields()` only iterates
   the credential type's static `schema.required` array. `access_token` is
   necessarily absent from GitHub's base `schema.required` (only ONE of
   `access_token` / `username`+`password` / `app_private_key` is actually
   needed, depending on which `auth` radio is selected), and nothing adds a
   conditional required-check based on the currently-selected `auth` value.
   This is a distinct manifestation of the same underlying gap as
   [#526](https://github.com/EliteaAI/elitea-testing-public/issues/526)
   (`label`/Display Name never being in `schema.required` at all) — same
   root helper function, different field/scenario (auth-conditional vs.
   universally-excluded) — filed separately per this repo's strict-per-bug
   policy. Reproduced twice (fresh page loads, native CDP input events, no
   synthetic dispatch). Console clean throughout. Both test credentials
   created during reproduction were deleted via the API afterward
   (`DELETE /configurations/configuration/399/{id}` → 204), no orphaned
   data left in the shared DEV project. **Not filed as case-text drift /
   reverse-masking** — the case's own wording explicitly names "Token" as
   the required-field example that should block Save; the live product
   diverges from that, so the product is the outlier, not the case.
   **Does not block the rest of the case** — Steps 1-4 (duplicate-name
   detection) were fully executed and pass exactly as specified before
   this defect was found at the case's tail (Steps 5-6); classified
   `ready-for-automation` per `.agents/testing.md` § Merge gate
   "Analysis-time entry", with the affected assertions written as
   `expect.soft()` + `# Known defect: #1004`.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`); reuse
  `CredentialCreatePage` (`automation/pages/credential_create_page.py`),
  `CredentialsListPage` (`automation/pages/credentials_list_page.py`), and
  the `credential_api` fixture (`automation/fixtures/api_fixtures.py`) —
  same trio `test_credential_create.py` and
  `test_credential_required_fields_validation.py` already use. No new page
  object needed beyond adding the one new `api_error_message` locator
  (Concrete Handles) to `CredentialFormFieldsMixin`
  (`automation/pages/credential_form_fields.py`), alongside the existing
  `display_name_input`/`save_button`/`id_input` fields it already shares
  between create and edit flows.
- Suggested test file: `automation/tests/ui/toolkits/
  test_credential_duplicate_mismatch_validation.py` (naming consistent with
  sibling `test_credential_*.py` files in the same directory).
- Wait strategy: wait on the Save POST response (`page.expect_response()`,
  same pattern as `test_credential_create.py` Step 7) rather than a fixed
  timeout, for both the successful create (step 3) and the rejected
  duplicate (step 6) — the UI does NOT navigate away on step 6's rejection,
  so `page.wait_for_url()` is not the right signal there; wait for the
  error banner text to appear instead
  (`expect(error_locator).to_contain_text(...)`, once the testid lands —
  or `page.get_by_text("already exists")` as the interim fallback per
  Concrete Handles).
- Timestamp the duplicate Display Name (`f"autotest_duplicate_cred_{ts}"`)
  — see Test Data note; do NOT use the case's literal unsuffixed string,
  it will collide across CI re-runs against the same shared DEV project.
