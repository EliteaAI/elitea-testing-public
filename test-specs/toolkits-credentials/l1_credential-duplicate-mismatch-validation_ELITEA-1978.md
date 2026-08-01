# Test Case: Credential — Duplicate/Mismatch Validation

## Metadata
- **TMS ID**: ELITEA-1978
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high`, same convention as
  ELITEA-1976/1979 in this batch)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`)
- **User set**: `${TEST_USER}` (nominal — `auth_state` no-op on localhost)
- **Analyst**: qa-engineer (agent), 2026-08-02
- **Status**: ready-for-automation

## Classification note — one KNOWN, already-filed defect affects Steps 5-6

Live-reconfirmed: **`elitea-testing-public#1004`** (OPEN) — on the GitHub
credential create form, once "Token" auth is selected, the Access Token
field is NOT enforced as a required field: Save stays **enabled** with the
field empty, the click succeeds (`POST` → 200), and the backend persists a
credential with `data.access_token: null`. This directly contradicts the
case's own Step 5-6 wording ("Attempt to save a credential with empty
required fields (e.g., empty Client Id or Token)" / "Save button remains
disabled"). Per `.agents/testing.md` § Merge gate's sanctioned-RED exception
(deterministic, single-cause, linked to an OPEN defect): the empty-Token
half of steps 5-6 is written as a REAL assertion (Save should stay disabled)
wrapped in `expect.soft()` with `# Known defect: #1004`, so the test stays
honestly RED for this one cause until the product fix ships — never masked,
never weakened. The Display-Name-empty half of steps 5-6 (baseline
required-field gating, unaffected by #1004) is a hard, non-soft assertion.
No new ticket filed — `#1004` already covers this exact object, trigger, and
expected/actual (it was filed "Found while working #112", the tracking
board issue for this very TMS case).

## Preconditions
- User authenticated (`auth_state` fixture — no-op on localhost).
- Credentials section accessible (`/credentials/create-credential/github`
  reachable directly — no zero-credential-project redirect concern since
  this test never lands on `/credentials/all` mid-flow).

## Test Data
### generate-per-test (created in test, cleaned up in its own teardown)
- **Duplicate credential name**: `autotest_duplicate_cred_${timestamp}` —
  case pins the literal `autotest_duplicate_cred`; timestamped per this
  feature's established collision-avoidance convention (same reasoning as
  ELITEA-1976's AFS).
- **Credential type**: Github, Token auth, `${GIT_HUB_TOKEN}` for the FIRST
  (seed) credential only — the duplicate-attempt credential's token content
  is irrelevant (the 400 fires on the `elitea_title` collision before any
  token validation), and the empty-required-field probe (steps 5-6)
  deliberately never provides a token at all.

## Test Steps
1. Create a credential named `autotest_duplicate_cred_${ts}` (type Github,
   Token auth, `${GIT_HUB_TOKEN}`) via `credential_api.create_github_credential(
   display_name=name, elitea_title=name, ...)` — API seed, not UI, since the
   case's own object under test is the SECOND (duplicate) attempt.
   - **Verify**: 200, credential id returned.
2. Navigate to `/credentials/create-credential/github`. Fill Display Name
   with the SAME name as step 1, select Token auth, fill Access Token with
   `${GIT_HUB_TOKEN}`.
   - **Verify**: ID field mirrors the Display Name (`toolkit-field-elitea_title-input`
     shows the same colliding value) — this is WHY the collision fires on
     `elitea_title`, not a separate "name" field.
3. Click Save.
   - **Verify**: `POST /configurations/configurations/{project_id}` returns
     400 with body `{"error": "Credential with ID '<name>' already exists",
     "field": "elitea_title"}`.
4. Verify the error is visible to the user: the exact string `Credential
   with ID '<name>' already exists` renders on the page (currently via a
   plain, non-testid `<Typography>` — see Concrete Handles); the form does
   NOT navigate away (`page.url` still contains
   `/credentials/create-credential/github`).
5. Start a fresh create-credential form (`/credentials/create-credential/github`).
   Fill Display Name only (a fresh, non-colliding name) — leave Base Url at
   its default-prefilled value (Anonymous auth, GitHub-specific baseline).
   - **Verify (baseline, non-soft)**: with ONLY Display Name filled and
     Anonymous auth (the default), Save becomes enabled — establishes the
     control case before probing the defect.
6. Select "Token" auth, leave Access Token EMPTY.
   - **Verify (soft — `# Known defect: #1004`)**: Save should be disabled
     (or clicking it should be blocked / show inline validation) with Access
     Token empty. **Live-confirmed this currently FAILS**: Save stays
     enabled and clicking it succeeds (200), persisting `access_token: null`.
     Assert `expect.soft(save_button).to_be_disabled()`, and separately
     assert (hard) that clicking it does NOT silently corrupt the required-
     field baseline established in step 5 — i.e. this is a real, reported
     regression signal, not swallowed.

## Expected Results
- Duplicate `elitea_title` is rejected with the exact backend message; no
  duplicate credential record is created (verify via
  `credential_api.list_all_credentials()` — exactly one credential with
  that `elitea_title` exists, or use the seed credential's own `id` as the
  positive control).
- Empty Display Name blocks Save (pre-existing, already covered by
  `test_credential_required_fields_validation.py` for Jira type — this case
  doesn't re-assert that half for GitHub since it's the same generic
  `ToolBase.jsx` validation, not credential-type-specific; see Coverage Map
  Axis 1 disposition).
- Empty Access Token (once Token auth selected) does NOT currently block
  Save — known defect `#1004`, asserted soft.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create credential "autotest_duplicate_cred" | created successfully | step 1 | API 200 + id | asserted |
| 2 Attempt second credential, same Display Name | form submitted | step 2 | fields filled, mirror confirmed | asserted |
| 3 Click Save | error "Credential with ID '...' already exists" | step 3 | POST 400 body match | asserted |
| 4 Verify error/warning visible | error visible to user | step 4 | visible page text match | asserted |
| 5 Attempt save with empty required fields (Client Id or Token) | Save disabled or validation triggers | steps 5-6 | step 5: Display-Name-only baseline (hard); step 6: empty-Token (soft, `#1004`) | asserted *(step 5 hard-asserted; step 6's Token half is a KNOWN DEFECT, soft-asserted per Classification note)* |
| 6 Verify validation indicators + Save disabled | indicators shown, Save not allowed | step 6 | Save-disabled soft assertion; no separate "indicator" element was found rendered for the empty-Token case specifically (see Axis 2) | asserted *(partially — the "validation indicators appear" half of the case's own wording was NOT observed live: no inline error/red-outline appears on the empty Access Token field itself, only Save's enabled state is wrong; noted as part of the same #1004 defect, not a second bug)* |
| desc: "Client Id" named as an example empty field | n/a | — | — | out-of-scope *(GitHub's fields are Display Name/Base Url/Access Token — there is no "Client Id" field on this credential type; the case's example is generic/copied from a different credential type's wording, not GitHub-specific — case-text looseness, not a defect)* |

### Axis 2 — Analyst additions

- Step 4 asserts NO navigation away from the create form after the 400 —
  *added: observed live that the form correctly stays put; guards against a
  regression where a failed save silently redirects, which would be a much
  worse UX defect than the current one.*
- Step 6 additionally verifies no separate inline field-level error renders
  on the empty Access Token input itself (only Save's state is affected) —
  *added: distinguishes "Save-gating bug" from "no error surfaced at all,"
  which matters for how the implementer scopes the `#1004` soft-assertion
  (Save-state only, not also asserting an absent inline indicator that
  would always spuriously pass).*
- Verified via `list_all_credentials()` that the duplicate attempt (step 3)
  created no second record — *added: the case's Pass criteria implies this
  ("no duplicate is created") but the case's own step list never explicitly
  says to check the list; making it an explicit assertion.*

## Cleanup
1. Delete the step-1 seed credential.
2. Delete the step-5/6 credential (it WILL exist server-side due to
   `#1004` — the empty-Token save succeeds — so cleanup must account for
   this, not assume the object was never created).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Provenance |
|---|---|---|
| Display Name input | `toolkit-field-label-input` (`CredentialFormFieldsMixin.display_name_input`) | on-main ✓ |
| ID (mirror) input | `toolkit-field-elitea_title-input` (`CredentialFormFieldsMixin.id_input`) | on-main ✓ |
| Token auth radio | `toolkit-field-auth-radio-token` (`CredentialCreatePage.AUTH_METHOD_RADIO`) | on-main ✓ |
| Access Token input | `toolkit-field-access_token-input-field` (`CredentialCreatePage.access_token_input`) | on-main ✓ |
| Save button | `credential-form-save-button` (`CredentialFormFieldsMixin.save_button`) | on-main ✓ |
| Duplicate-name error text | **testid needed**: `credential-form-api-error-message` — source pointer `EliteaUI/src/pages/Credentials/CredentialForm.jsx` ~line 352-360 (`{apiError && <Typography sx={styles.errorMessage}>{apiError}</Typography>}`) | needs-adding (re-verified: absent from both `main` and `automation/testids` today; a dangling, unreachable local commit from a prior session claims this SHA already exists — it does not, see `_surface.md`) |

## Network Behavior
- `POST /configurations/configurations/{project_id}` — the duplicate
  attempt returns 400 with `{"error": "...", "field": "elitea_title"}`; the
  empty-Token attempt (step 6, `#1004`) returns 200.

## Known Defects Found During Exploration
- **`#1004`** (OPEN, pre-existing) — Access Token not enforced as required
  once Token auth is selected on the GitHub create form. Directly affects
  this case's steps 5-6. Asserted via `expect.soft()` per the sanctioned-RED
  merge-gate exception; no new ticket filed (dedup: exact match, same
  object/trigger/expected-actual, already OPEN).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest.
- Reuse `CredentialCreatePage` unmodified for both the duplicate-attempt and
  empty-field flows.
- Reuse `CredentialAPI.create_github_credential()` /
  `list_all_credentials()` / `delete_credential()` for the seed +
  verification + cleanup.
- Follow `test_credential_required_fields_validation.py`'s
  `expect.soft()` + `# Known defect: #NNN` idiom exactly (it already
  implements this pattern for a sibling defect, `#526`, on the same page
  object family) — do not invent a different masking-avoidance shape.
