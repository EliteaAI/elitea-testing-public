# Test Case: Credential — Error States

## Metadata
- **TMS ID**: ELITEA-1980
- **Linked Story**: none
- **Priority**: l2 (case frontmatter: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`),
  project 399 "Private" (`Test Bot`)
- **User set**: `${TEST_USER}` (nominal — `auth_state` no-op on localhost)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), 2026-08-22
- **Status**: ready-for-automation

## Relationship to ELITEA-1970 (Test connection) — why this is a NEW spec, not an extension

ELITEA-1970 (`tests/ui/toolkits/test_credential_test_connection.py`, merged on
the batch trunk) proves the **success ⇄ failure contrast** of Test connection on
a **Jira** credential: a valid secret raises the OK toast, an invalid one lights
the **secret** field inline. ELITEA-1980 is a different subject — three *error*
surfaces, only one of which 1970 touches, and on a different vehicle:

| ELITEA-1980 asks for | 1970 already proves? |
|---|---|
| invalid token → specific failure reason (Github, **pre-save**, on the create form) | partly — 1970 does it on Jira, post-save, on the detail page |
| unreachable Base Url → connection/timeout error | **no** |
| bad credential id in the URL → not-found state | **no** |
| no raw stack traces in any of the above | **no** |

Extending 1970 would mean folding a second credential type, a second lifecycle
and a route-level 404 into a spec whose whole point is one type's success/failure
contrast. New spec; the shared machinery is reused through the same page objects
and mixin.

## Case-text divergence #1 (non-blocking) — which FIELD the invalid-token error lands on

The case (step 2) asks only that "an error message appears with a specific
failure reason" — it names no field, so nothing here contradicts the case; this
is recorded because it is surprising and the spec asserts against it.

Live on **Github** with `access_token = invalid_token_xyz`:
`POST /configurations/check_connection/399/github` → **400**
`{"success": false, "message": "Authentication failed: Invalid credentials"}`,
and the message renders inline under **Base Url**
(`toolkit-field-base_url-input`, `aria-invalid="true"`), *not* under Access
Token. That is deliberate product code, not a glitch —
`credentialError.helpers.js#extractInformationFromCredentialError`:

1. per-key substring match (title / description / `settings[key]` / key name) —
   `"authentication failed: invalid credentials"` matches none of Github's keys;
2. `authentication` + `isSecretField(key)` — does not fire for Github's
   `access_token` (it does for Jira's `api_key`, which is why 1970 sees the
   inline error on the secret field);
3. `url`-in-message + `*url*`-in-key — the message carries no "url";
4. **fallback**: nothing mapped ⇒ *every* `*url*` key gets the message.

Branch 4 is what fires. The spec therefore asserts the message on the Base Url
field's helper text **and names this code path in a comment**, so a future
mapping change fails loudly at a documented place rather than mysteriously.

## Case-text divergence #2 (non-blocking) — "timeout or connection refused"

Case step 4 expects "Timeout or connection refused". The live product returns a
**fast, explicit** connection error rather than a hung timeout (~1.1 s):
`{"success": false, "message": "Connection error: Unable to reach GitHub API"}`
(Jira's wording is `Connection error: Unable to reach Jira server - check URL
and network connectivity`). Same category — the backend reached the DNS-invalid
host and reported it — so the case's intent is met. The spec asserts the
**carry-through invariant** (the inline text equals the response body's own
`message`) plus a `Connection error` category check, never a hardcoded sentence.

## Case-text divergence #3 (informational) — step 5's not-found state is DELAYED

`/credentials/all/99999` renders `Page404` ("Page not found. Try Home page") —
but only **after** `GET /configurations/configuration/399/99999` resolves 404.
Until then the route renders an **empty, editable credential form** with Save /
Discard / three-dot controls. Read too early (measured: a snapshot taken
immediately after `page.goto` saw the blank form) this looks like a missing
not-found state. It is not: `EditCredential.jsx:160` computes
`shouldShowNotFoundPage = isError && isNotFoundError(error)` and returns
`<Page404 />`. **Not filed as a defect** — the transient is a loading state, and
the case's expected result is satisfied. The spec waits on the 404 response, not
on a timer.

## Preconditions
- User authenticated (`auth_state` fixture — no-op on localhost).
- Credentials section accessible; the create form is reachable directly at
  `/credentials/create-credential/github`.
- **No external test data needed.** Github's schema requires only `base_url`
  (pre-filled `https://api.github.com`), and both error scenarios need
  *invalid* inputs — so, unlike ELITEA-1970, this case has **no `pytest.skip`
  path** and is immune to `#1673` (the expired `GIT_HUB_TOKEN`).

## Test Data
### generate-per-test (created in the test, deleted in teardown via the API)
- **Display Name**: `autotest_cred_err_${timestamp}` — 28 chars, deliberately
  under the Display Name field's real `maxLength = MAX_NAME_LENGTH = 32`
  (`ToolBaseProperty.jsx:589`), which **silently truncates** a longer name and
  makes every later lookup-by-name miss (cost ELITEA-1970 a run).
- **Credential type**: `github`, auth method **Token**.
- **Invalid token value**: `invalid_token_xyz` — the literal from the case's Test Data.
- **Unreachable Base Url**: `http://unreachable.example.invalid` — the literal
  from the case's Test Data (`.invalid` is RFC 2606 reserved, so it can never
  resolve; the failure is a property of the address, not of the network).
- **Non-existent credential URL**: `/credentials/all/99999` — the case's literal.
  Verified non-existent live: `GET /configurations/configuration/399/99999`
  → 404 `{"error": "Configuration not found"}`.

## Test Steps
1. Open `/credentials/create-credential/github`, set Display Name to
   `autotest_cred_err_${ts}`, select the **Token** auth method, and type
   `invalid_token_xyz` into Access Token.
   - **Verify** (case step 1 — "the form accepts the input"): the Display Name
     input reads back the full generated name (the 32-char truncation guard);
     the Access Token native input's value equals `invalid_token_xyz`; the Base
     Url input carries the schema default `https://api.github.com`; Save is
     enabled.
2. Click **Test connection**.
   - **Verify** (case step 2): `POST /configurations/check_connection/{project}/github`
     → **400** with `success == false` and a non-empty `message`; the Base Url
     field goes `aria-invalid="true"` and its
     `toolkit-field-base_url-input-helper-text` is visible with text **equal to
     that response body's `message`** (the product is the oracle — see
     divergence #1 for why Base Url and not Access Token); the message names a
     specific reason (matches `Authentication failed`); no **success** toast is
     raised.
3. Replace Base Url with `http://unreachable.example.invalid` and click **Save**.
   - **Verify** (case step 3 — "credential is saved"):
     `POST /configurations/configurations/{project}` → **200** whose body carries
     a numeric `id` and `label == elitea_title == ${name}`; the app lands back on
     `/credentials/all` and the credential's card is present in the list.
4. Open the saved credential's detail page (click its card) and click
   **Test connection**.
   - **Verify** (case step 4): the detail URL carries the created id;
     `POST /configurations/check_connection/{project}/github` → **400**,
     `success == false`, `message` non-empty and matching `Connection error`
     (the category the case's "timeout or connection refused" names — see
     divergence #2); Base Url is `aria-invalid="true"` and its helper text
     equals that `message` verbatim; no success toast.
5. Navigate to `/credentials/all/99999`.
   - **Verify** (case step 5): `GET /configurations/configuration/{project}/99999`
     → **404**; the shared not-found state `page-not-found` becomes visible with
     text containing `Page not found`; the credential form is **gone**
     (`credential-form-save-button` count 0) — i.e. the app does not leave a
     blank editable form behind (see divergence #3).
6. Assert the three error strings collected in steps 2, 4 and 5 are
   user-friendly.
   - **Verify** (case step 6): each is non-empty, single-line, ≤ 200 characters,
     and contains **none** of the raw-stack-trace markers
     (`traceback`, `file "`, `, line `, ` at 0x`, `<class '`, `raise `,
     `most recent call last`, `\n  at `). Asserted over the strings the PRODUCT
     produced in this run — not over a fixed list.

## Expected Results
- Every error state the case names is surfaced by the product with a specific,
  human-readable reason: an auth failure and a connection failure land inline on
  a form field carrying the backend's own message verbatim; a non-existent
  credential id resolves to the app's shared not-found page.
- No error surface leaks an implementation dump (stack trace, exception repr).

## Coverage Map

### Axis 1 — Case coverage
| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: user logged in | precondition | `auth_state` fixture (no-op on localhost) |
| Precondition: project + Credentials section accessible | precondition | Step 1 navigation succeeds (form renders) |
| Test Data: invalid token `invalid_token_xyz` | used | Step 1 |
| Test Data: unreachable Base Url | used | Step 3 |
| Test Data: `/credentials/all/99999` | used | Step 5 |
| Step 1 — create a credential with an invalid token → form accepts the input | asserted | Step 1: Access Token input value equality + Display-Name read-back + Save enabled |
| Step 2 — Test connection → error with a specific failure reason | asserted | Step 2: 400 `success=false`, inline helper text == body `message`, `aria-invalid=true`, `Authentication failed` category, no success toast |
| Step 3 — save a credential with an unreachable Base Url → credential is saved | asserted | Step 3: create `POST` 200 + `id`/`label`/`elitea_title` + redirect + card present in the list |
| Step 4 — Test connection on it → timeout / connection-refused error | asserted | Step 4: 400 `success=false`, `Connection error` category, inline helper text == body `message` (see divergence #2) |
| Step 5 — bad id in the URL → appropriate error / not-found state | asserted | Step 5: detail `GET` 404 + `page-not-found` visible + form absent |
| Step 6 — messages user-friendly, no raw stack traces | asserted | Step 6: stack-trace-marker + shape assertions over the three strings this run produced |
| Expected Final State: clear messages, no internal details | asserted | Steps 2/4/5 (the messages) + step 6 (the no-leak check) |
| Fail criterion: unexpected crash / unhandled error | asserted | Every step asserts the expected status code + a rendered state; an unhandled error fails the step it happens in |
| Fail criterion: messages contain stack traces / are not user-friendly | asserted | Step 6 |

### Axis 2 — Analyst additions
| Addition | Why grounded |
|---|---|
| Assert each inline message **equals the response body's `message`** | The honest oracle for a backend-authored string; catches the UI dropping or mangling the reason without pinning a wording (same discipline as ELITEA-1970) |
| Assert the *category* of each message (`Authentication failed` / `Connection error`) | The case's "specific failure reason" and "timeout or connection refused" are category claims; asserting only "some text appeared" would pass on a generic "Error" |
| Assert `aria-invalid="true"` on the offending field | The case's "error message appears" as a real product state attribute, testid-scoped (`.agents/testing.md` § Locator policy — state via attribute filters) |
| Assert the credential form is ABSENT on the 404 route | Distinguishes the real not-found state from the transient blank editable form the route renders while the detail GET is in flight (divergence #3) |
| Assert no success toast on either failed Test connection | The case's Fail criterion ("unexpected"/wrong feedback) made concrete |

## Cleanup
- Teardown deletes the created credential via `credential_api.delete_credential(id)`
  (`DELETE /configurations/configuration/{project}/{id}` → 204), guarded so a
  failed run still cleans up. Steps 1–2 create nothing (pre-save form only).

## Concrete Handles (discovered/verified live 2026-08-22)

| Element | Handle | Provenance |
|---|---|---|
| Display Name input | `toolkit-field-label-input` | on-main ✓ |
| ID (elitea_title) input | `toolkit-field-elitea_title-input` | on-main ✓ |
| Base Url input | `toolkit-field-base_url-input` | on-main ✓ |
| **Base Url inline error/helper text** | **`toolkit-field-base_url-input-helper-text`** | **added for this case** — EliteaAI/EliteaUI@54ce148e, on `automation/testids` (awaiting human cherry-pick to `main`) |
| Auth-method radio "Token" | `toolkit-field-auth-radio-token` | on-`automation/testids` (ELITEA-1967, EliteaAI/EliteaUI@5892ae48) |
| Access Token secret field (wrapper) | `toolkit-field-access_token-input` | on-main ✓ |
| Access Token native `<input type=password>` | `toolkit-field-access_token-input-field` | on-main ✓ (derived by `SecretField.jsx`) |
| Save button | `credential-form-save-button` | on-main ✓ |
| Test connection button | `credential-form-test-connection-button` | on-`automation/testids` only (ELITEA-1967, EliteaAI/EliteaUI@5892ae48) |
| Toast container / severity | `toast-alert` + `data-severity="success"` (asserted ABSENT) | on-main ✓ |
| Credential list card / name | `entity-card` filtered by `entity-card-name` | on-main ✓ |
| **Not-found page** | **`page-not-found`** | **added for this case** — EliteaAI/EliteaUI@54ce148e, on `automation/testids` (awaiting human cherry-pick to `main`) |

Both new testids are **attribute-only, zero-functional-impact** additions
(`add-data-testid` § Step 5.5 — no new DOM node, no new hook, no removed line):

- `toolkit-field-{key}-input-helper-text` — `ToolBaseProperty.jsx` now passes
  the **already-supported** `helperTextTestId` prop (`InputBase.jsx:101`/`:270`,
  three pre-existing callers) with the caller-derived value. It is the exact
  grammar `SecretField.jsx` already uses for secret fields
  (EliteaAI/EliteaUI@58955184, ELITEA-1970) — so the shared mixin's existing
  `FIELD_HELPER_TEXT` constant covers plain and secret fields alike, and the
  digest's open gap ("the same handle on the plain fields' helper text") closes.
- `page-not-found` — a **generic** testid on the shared `Page404` container
  (no feature scope, per `.agents/testing.md` § Locator policy: shared
  components never hardcode feature-scoped testids). Every 404 route in the app
  gains a handle; this case references it on its executed path (#511).

## Network Behavior
- **Test connection (auth failure)**: `POST {api}/configurations/check_connection/{project}/github`
  → **400** `{"success": false, "message": "Authentication failed: Invalid credentials"}`.
- **Create**: `POST {api}/configurations/configurations/{project}` → 200 with
  `id`, `label`, `elitea_title`.
- **Test connection (unreachable host)**: same endpoint → **400**
  `{"success": false, "message": "Connection error: Unable to reach GitHub API"}`
  in ~1.1 s (no hung timeout).
- **Bad id**: `GET {api}/configurations/configuration/{project}/99999` → **404**
  `{"error": "Configuration not found"}`. This 404 also prints a **console
  error** — harmless, but any future console-error side-channel over this route
  needs an endpoint-specific filter (same class as `#1666` for delete).
- **Delete (teardown)**: `DELETE {api}/configurations/configuration/{project}/{id}` → 204.
- `networkidle` is **not** a usable settle condition on the credentials routes
  (`.agents/testing.md`; ELITEA-1964/1967) — settle on the form's own render
  signal and on the responses named above.

## Known Defects Found During Exploration
**None.** All six steps behaved as the case describes. Two things that look like
defects and are not, both ruled out live and recorded so nobody re-files them:
the auth error landing on **Base Url** (divergence #1 — deliberate fallback in
`credentialError.helpers.js`) and the **blank editable form** visible on
`/credentials/all/99999` before the detail GET resolves (divergence #3 — a
loading state; `Page404` follows).

## Blocked Steps
None — all six steps executed live end-to-end on `localhost:5173`, project 399.

## Automation Hints
- `pytestmark`: `ui`, `credentials`, `p2`, `regression`, `new`.
- Page objects: everything needed already exists —
  `CredentialCreatePage.open_type_form()` / `select_auth_method("token")` /
  `set_access_token()` / `set_base_url()`, `CredentialsListPage.click_credential_card()`
  / `card_by_name()`, `CredentialDetailPage.wait_for_page_load()` /
  `get_credential_id_from_url()`, and the shared mixin's
  `test_connection_button` / `success_toast()` / `FIELD_HELPER_TEXT`. Shipped
  additions: a generic `field_helper_text(field_key)` on
  `CredentialFormFieldsMixin` (`secret_field_helper_text` stays byte-identical
  for its ELITEA-1970 caller — additive-only on a shared-caller file);
  `FIELD_INPUT` + `field()` PROMOTED into that mixin from `CredentialCreatePage`
  so the detail route can read a field's `aria-invalid` (inherited — every
  existing caller unchanged; all 4 affected specs re-run green); and a
  `NotFoundPage` page object for `page-not-found`, whose `open_route()` skips
  `BasePage.navigate()`'s 30 s `networkidle` wait.
- **`set_base_url()` APPENDS** (click + `press_sequentially`) and Github's Base
  Url ships pre-filled — call `clear_base_url()` first, or step 3 posts
  `https://api.github.comhttp://unreachable.example.invalid`. Cost one run.
- Wrap **both** Test-connection clicks in `page.expect_response()` on
  `check_connection` — the round trip is 1–4 s and the assertion needs the body.
- Wrap the step-5 navigation in `page.expect_response()` on
  `configuration/{project}/99999` — that response, not a timer, is what turns
  the transient blank form into `Page404` (divergence #3).
- Keep the generated Display Name ≤ 32 chars (the silent-truncation trap).
- Github + Token auth needs **no** valid secret, so this spec has no skip path;
  do not copy ELITEA-1970's `pytest.skip` guard into it.
