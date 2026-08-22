# Test Case: Credential — Test Connection

## Metadata
- **TMS ID**: ELITEA-1970
- **Linked Story**: none
- **Priority**: l3 (case frontmatter: `low`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`),
  project 399 "Private" (`Test Bot`)
- **User set**: `${TEST_USER}` (nominal — `auth_state` no-op on localhost)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), 2026-08-22
- **Status**: ready-for-automation

## Case-text divergence #1 (BLOCKING for the case's stated type) — Jira replaces Github as the credential type

The case names **Github + "a working Github personal access token"**. The
suite's `GIT_HUB_TOKEN` (`.env.test`, the project's declared GitHub test data
per `.agents/profile.md` § Roles & sample users) **no longer authenticates**:

```
curl -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $GIT_HUB_TOKEN" https://api.github.com/user   → 401
curl -o /dev/null -w "%{http_code}" -H "Authorization: token  $GIT_HUB_TOKEN" https://api.github.com/user   → 401
```

Driven end-to-end through the product it reproduces exactly: a Github
credential created in the UI with that token, then **Test connection** on its
detail page →
`POST /configurations/check_connection/399/github` → **400**
`{"success": false, "message": "Authentication failed: Invalid credentials"}`.
Step 3's expected result (`"The connection is OK!"`) is therefore **not
producible** with Github today. Filed for a human as
**`elitea-testing-public#1673`** (`question`, test data — not a product defect).

**This is NOT an Elitea defect.** The same flow with the suite's *valid* Jira
test data (`JIRA_BASE_URL` / `JIRA_USERNAME` / `JIRA_API_KEY`) returns
`{"success": true}` and the exact toast the case demands — verified live twice
(pre-save on the create form, and post-save on the detail page).

**Decision:** the case is executed and automated against the **Jira**
credential type. Nothing about *what* is verified changes — the subject is the
Test connection button's success/failure feedback, which is type-agnostic
machinery (`CredentialForm.jsx` → `useCreateConfiguration.onTestConnection` →
`POST /configurations/check_connection/{project}/{type}`); only the *vehicle*
(which credential type the environment can supply valid data for) changes.
The spec keeps the type + field key + credentials in ONE module-level table,
so re-pointing it at Github after `#1673` is resolved is a one-row edit.

## Case-text divergence #2 (non-blocking) — the invalid-token message text

Case step 5 expects "a message such as **'Invalid token. Please verify the
token and try again.'**". The live product renders the **backend's own**
message verbatim, which for an invalid Jira api_key is
`Authentication failed: Invalid username or API key` (Github's is
`Authentication failed: Invalid credentials`). The case says "such as", so
this is an example, not a contract. The spec asserts the **carry-through
invariant** instead of any literal: the inline message must equal the
`message` field of the failing `check_connection` response body. That is
strictly stronger than a hardcoded string (it catches the UI dropping or
mangling the backend's reason) and survives a backend wording change.

## Case-text divergence #3 (informational) — "the token field"

For Jira the secret field is **Api Key** (`api_key`), not "Token"; for Github
it is Access Token (`access_token`). Same `SecretField` renderer, same testid
grammar — the spec addresses it by schema key, so the row swap in divergence
#1 carries the field with it.

## Preconditions
- User authenticated (`auth_state` fixture — no-op on localhost).
- Credentials section accessible; the create form is reachable directly at
  `/credentials/create-credential/jira`.
- Valid Jira credentials configured in `.env.test`
  (`JIRA_BASE_URL`, `JIRA_USERNAME`, `JIRA_API_KEY`). The spec `pytest.skip`s
  when any of the three is unset — the suite's established pattern for
  toolkit test data (`.agents/testing.md` § Test data strategy). They are
  **set and valid** today (verified live: `check_connection` → `{"success": true}`).

## Test Data
### generate-per-test (created in test, deleted in teardown via the API)
- **Display Name**: `autotest_cred_conn_${timestamp}` — timestamped per this
  feature's established collision-avoidance convention (ELITEA-1964/1976/1978),
  and deliberately SHORT: the Display Name input carries a real
  `maxLength = MAX_NAME_LENGTH = 32` (`EliteaUI/src/common/constants.js`,
  applied at `ToolBaseProperty.jsx:589` for `k === 'label'`), so a longer name
  is **silently truncated by the field** — the create response then carries the
  truncated `label`/`elitea_title` and every later lookup by name misses.
  Found the expensive way on this case's first run (33-char name → 32 stored).
- **Credential type**: `jira` (see divergence #1).
- **Valid secret**: `settings.jira_api_key` + `settings.jira_username` +
  `settings.jira_base_url` — never logged, never asserted on, only typed.
- **Invalid secret**: `invalid_token_xyz` — the literal from the case's Test
  Data table.

## Test Steps
1. Navigate to `/credentials/create-credential/jira`, fill Display Name with
   `autotest_cred_conn_${ts}` (§ Test Data — the name MUST stay within the
   field's real `maxLength` of 32, which truncates silently), Base Url /
   Username / Api Key from `.env.test`, click Save.
   - **Verify**: the Display Name input's own value reads back `${name}`
     in full (the truncation guard — a name over 32 chars fails here, loudly,
     instead of silently mismatching every later lookup); Save is enabled once
     all four fields are filled; `POST /configurations/configurations/{project}`
     → **200**, response `label == elitea_title == ${name}` with a numeric `id`;
     the app redirects to `/credentials/all`.
2. Open the credential's detail page by clicking its card in the list.
   - **Verify**: URL becomes `/credentials/all/{id}` carrying the SAME id the
     create response returned; the Display Name field reads `${name}`; the
     Api Key secret field is rendered (password mode).
3. Click **Test connection**.
   - **Verify**: the button is enabled before the click;
     `POST /configurations/check_connection/{project}/jira` → **200** with body
     `{"success": true}`; a **success** toast appears
     (`toast-alert[data-severity="success"]`) whose `toast-message` text is
     exactly `The connection is OK!`; the Api Key field shows **no** inline
     error (`…-helper-text` count 0, `aria-invalid="false"`) and the global
     `credential-form-api-error-message` is absent. The toast is then allowed
     to auto-hide (its own product behaviour, awaited — no sleep) so step 5's
     "no success toast" assertion starts from a clean baseline.
4. Replace the Api Key field's value with `invalid_token_xyz`.
   - **Verify**: the field's native input value reads `invalid_token_xyz`.
5. Click **Test connection** again.
   - **Verify**: `POST /configurations/check_connection/{project}/jira` →
     **400** with body `success == false` and a non-empty `message`; the Api
     Key field renders the inline error indicator
     (`aria-invalid="true"`) and its `…-helper-text` element is visible with
     text **equal to that response body's `message`**; the global
     `credential-form-api-error-message` stays absent (the error is inline, not
     a banner); no success toast is raised by this click.

## Expected Results
- Test connection reports the **truth from the target service**: a success
  toast for a working credential, an inline field-level error carrying the
  service's own reason for a broken one.
- The failure is surfaced **on the offending field**, not only as a global
  banner (`credential-form-api-error-message` stays absent — the per-field
  branch of `useCreateConfiguration.onTestConnection` wins whenever
  `extractInformationFromCredentialError` maps the message to a schema key).

## Coverage Map

### Axis 1 — Case coverage
| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: user logged in | precondition | `auth_state` fixture (no-op on localhost) |
| Precondition: project + Credentials section accessible | precondition | Step 1 navigation succeeds (form renders) |
| Precondition: valid auth token available | precondition (adapted) | `JIRA_*` env vars — see divergence #1; `pytest.skip` when unset |
| Step 1 — create credential with a valid token → saved successfully | asserted | Step 1: create `POST` 200 + `label`/`elitea_title`/`id` + redirect |
| Step 2 — open the credential detail page → page loads | asserted | Step 2: URL carries the created id + Display Name field reads the name |
| Step 3 — Test connection → success indicator + toast "The connection is OK!" | asserted | Step 3: `check_connection` 200 `{"success": true}`, `toast-alert[data-severity="success"]`, `toast-message` text equality, absence of inline error |
| Step 4 — edit the token field to an invalid value → field updates | asserted | Step 4: native input value equality |
| Step 5 — Test connection → failure indicator in the token field + message | asserted | Step 5: `check_connection` 400 `success == false`, `aria-invalid="true"`, `…-helper-text` visible with text == body `message` |
| Expected Final State / Pass criteria: accurate feedback both ways | asserted | The two halves above, in one test (the contrast IS the case) |
| Fail criterion: success toast for invalid credentials | asserted | Step 5 asserts no success toast is raised by the second click |

### Axis 2 — Analyst additions
| Addition | Why grounded |
|---|---|
| Assert the inline message **equals the response body's `message`** | The honest oracle for a backend-authored string (see divergence #2) — proves carry-through instead of pinning a wording |
| Assert `aria-invalid` flips `false` → `true` on the same field | The case's "success/failure indicator" as a real product state attribute, testid-scoped (`.agents/testing.md` § Locator policy — state via `data-*`/ARIA attribute filters) |
| Assert the global `credential-form-api-error-message` stays absent | Distinguishes the case's "inline error **in the token field**" from the other error surface the same handler can take |
| Assert the check_connection response status/body directly | The product's own network truth as the oracle for both halves — no fabricated payload anywhere |

## Cleanup
- Teardown deletes the created credential via `credential_api.delete_credential(id)`
  (`DELETE /configurations/configuration/{project}/{id}` → 204). Guarded so a
  failed run still cleans up. The case's own flow never deletes it.

## Concrete Handles (discovered/verified live 2026-08-22)

| Element | Handle | Provenance |
|---|---|---|
| Display Name input | `toolkit-field-label-input` | on-main ✓ |
| Base Url input | `toolkit-field-base_url-input` | on-main ✓ |
| Username input | `toolkit-field-username-input` | on-main ✓ |
| Api Key secret field (wrapper) | `toolkit-field-api_key-input` | on-main ✓ |
| Api Key native `<input type=password>` | `toolkit-field-api_key-input-field` | on-main ✓ (derived by `SecretField.jsx`) |
| **Api Key inline error/helper text** | **`toolkit-field-api_key-input-helper-text`** | **added for this case** — EliteaAI/EliteaUI@58955184, on `automation/testids` (awaiting human cherry-pick to `main`) |
| Save button | `credential-form-save-button` | on-main ✓ |
| Test connection button | `credential-form-test-connection-button` | on-`automation/testids` only (added for ELITEA-1967, EliteaAI/EliteaUI@5892ae48) |
| Toast container / severity | `toast-alert` + `data-severity="success"` | on-main ✓ |
| Toast text | `toast-message` | on-main ✓ |
| Global API-error text (asserted ABSENT) | `credential-form-api-error-message` | on-main ✓ |
| Credential list card | `entity-card` filtered by `entity-card-name` | on-main ✓ |

The new `…-helper-text` testid is **caller-derived** inside the shared
`SecretField.jsx` (`${inputProps['data-testid']}-helper-text`), exactly like
the existing `-field` / `-toggle-*` / `-refresh-secrets-button` derivations —
the shared component hardcodes no feature-scoped testid, and every secret
field in the app (toolkits included) gains a unique handle for its inline
error. Attribute-only: one `const`, one `slotProps.formHelperText` entry, no
new DOM node, no new hook, no behavioural change.

## Network Behavior
- **Create**: `POST {api}/configurations/configurations/{project}` → 200,
  body carries `id`, `label`, `elitea_title`. Secret values are stored as a
  vault template — the saved credential's `data.api_key` reads
  `{{secret.<uuid>}}`.
- **Test connection**: `POST {api}/configurations/check_connection/{project}/{type}`
  → **200 `{"success": true}`** on success, **400
  `{"success": false, "message": "<service reason>"}`** on failure. Both
  observed live.
- **Delete (teardown)**: `DELETE {api}/configurations/configuration/{project}/{id}` → 204.
- `networkidle` is **not** a usable settle condition on the credentials routes
  (`.agents/testing.md`; ELITEA-1964/1967) — settle on the form's own render
  signal and on the `check_connection` response.

## Known Defects Found During Exploration
**None in the product.** One test-environment finding, filed for a human:
`elitea-testing-public#1673` (`question`) — `GIT_HUB_TOKEN` is expired.

Explicitly ruled OUT as a defect during exploration: on a saved credential's
detail page the secret field renders the vault entry's **bare name**
(a uuid4 hex) in password mode rather than the `{{secret.<name>}}` template,
and Test connection posts that bare name. It looks wrong and it is not — the
backend resolves it: with valid Jira data the post-save detail-page test
returns `{"success": true}`. Recorded in `_surface.md` so the next analyst
does not re-file it.

## Blocked Steps
None — all five steps executed live end-to-end on the Jira vehicle
(see divergence #1 for why not on Github).

## Automation Hints
- `pytestmark`: `ui`, `credentials`, `p3`, `regression`, `new`.
- Page objects: the three `CredentialForm.jsx` handles this case needs on the
  DETAIL page (`test_connection_button`, `api_error_message`,
  `FIELD_SECRET_INPUT`/`secret_native_input`) were declared only on
  `CredentialCreatePage`; they are **promoted** into the shared
  `CredentialFormFieldsMixin` (the `id_input` precedent) rather than duplicated,
  so one testid still lives in exactly one file. Both page objects inherit the
  mixin, so every existing caller is unchanged — re-run evidence in the PR.
- The credential type + field key + credential values live in ONE
  module-level constant block, so `#1673`'s fix is a one-row re-point.
- Use `page.expect_response()` on `check_connection` around BOTH clicks — the
  Jira round trip takes ~2-4 s and the toast auto-dismisses.
- The success toast must be read (and asserted) **before** step 4's typing:
  MUI auto-hides it. Assert it inside step 3, then let it go.
- Typing over the secret field: click → `ControlOrMeta+a` → `Backspace` →
  `press_sequentially` (MUI needs real key events; `fill()` does not fire
  React onChange — `.claude/rules/mui-patterns.md`).
- **Vite transform cache**: after adding the testid the dev server kept serving
  the STALE module even after `touch` + reload (the digest's HMR caveat, worse
  than recorded — a plain `GET` of the module returned the old text while a
  `?t=` cache-busted GET returned the new one). A dev-server restart with
  `rm -rf node_modules/.vite` was required. Cost 3 turns; recorded in `_surface.md`.
