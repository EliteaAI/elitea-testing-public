# Test Case: Credential — OAuth-Required Credential Flow (SharePoint Delegated)

## Metadata
- **TMS ID**: ELITEA-1981
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` @ `2706969d` → DEV backend `https://dev.elitea.ai/api/v2`),
  project 399 "Private" (`Test Bot`)
- **User set**: `${TEST_USER}` (nominal — `auth_state` no-op on localhost)
- **Analyst**: qa-engineer (analyst slot), 2026-08-23
- **Status**: **ready-for-automation**
- **Filed**: **#1711** — case-text clarification (steps 5 and 7→8, see below).
  No product defect found.
- **Cluster**: analysed in one live session with ELITEA-1982. **Separate AFS files**
  — the two cases differ in *steps*, not in data (see § Cluster note).

## Cluster note — why this is not a family AFS with ELITEA-1982

Same surface, one exploration session, but different flows: 1981 is a
create-and-save lifecycle on the create form; 1982 is a dialog-invocation-and-
cancel on an existing credential's detail page, asserting a modal 1981 never
opens. Per `test-case-analysis` § Cluster dispatches that is one AFS each. They
share page objects, the seeding helper and (if the implementer wants) one branch.

## Preconditions

- Logged in (localhost `auth_state` no-op), project **399**.
- Nothing to seed — `/credentials/create-credential/sharepoint` renders with no
  project state (digest § Cheap navigation fact).
- Clean up the created credential (`DELETE /configurations/configuration/399/{id}`)
  — every run creates one.

## Test Data (as executed)

| Field | Value used |
|---|---|
| Display Name | `autotest_sp_deleg_<n>` — **must stay ≤32 chars** (digest: silently truncated) |
| Client Id | `placeholder-client-id` |
| Client Secret | `placeholder-client-secret` |
| Site Url | `https://contoso.sharepoint.com/sites/test` |
| Oauth Discovery Endpoint | `https://login.microsoftonline.com/placeholder-tenant` |
| Scopes | `Sites.Read.All` |

Placeholders are sufficient end-to-end — the credential saves (200) and (for
ELITEA-1982) the backend still produces a real OAuth handshake from them. No
Microsoft tenant, no `.env.test` secret, so this case is immune to `#1673`
(expired `GIT_HUB_TOKEN`).

## Steps — as executed live (clean browser context)

| # | Action | Expected (case) | **Observed live** | Verdict |
|---|---|---|---|---|
| 1 | Navigate to Credentials | list loads | `/credentials/create-credential/sharepoint` renders the form directly; the type-card grid only exists on a zero-credential project (digest) | ✅ |
| 2 | Create a credential of type SharePoint | SharePoint fields displayed | `client_id`, `client_secret` (secret), `site_url` + Display Name / ID; auth radios `App-only` (**default ✓**) / `Delegated`; the three Delegated fields are **absent** | ✅ |
| 3 | Select **Delegated** | Delegated fields appear | radio becomes checked; the subsection renders | ✅ |
| 4 | Verify Auto Refresh Token checkbox, Oauth Discovery Endpoint, Scopes appear | all visible | all three render — labels `Auto Refresh Token`, `Oauth Discovery Endpoint *`, `Scopes *`. Both are marked required by the **subsection**, though the JSON-schema `required` list is only `client_id/client_secret/site_url`. The checkbox toggles normally (default unchecked). | ✅ |
| 5 | Verify a **Login** button appears next to Test connection | Login visible in the form | **Case-text drift → #1711.** Login is **absent** right after step 3/4 and appears the moment **Oauth Discovery Endpoint** is non-empty (`Login count 0 → 1`, measured both ways). `CredentialForm.jsx:342` gates it on `oauthTokenKey`, derived from `settings.oauth_discovery_endpoint` (`:168-176`). Product is correct; the case text orders the step too early. | ⚠️ clarification |
| 6 | Fill all required fields | all accept input | all accept input. **Save stays disabled until a field is typed with real keystrokes** — a Playwright `fill()` on Display Name leaves formik non-dirty (`useFormDirtyExcluding`), so `credential-form-save-button` *and* Discard stay disabled; one `press_sequentially` char flips both. `CredentialCreatePage.set_display_name()` already does select-all + type — use it. | ✅ |
| 7 | Save | saved with Delegated auth | `POST /configurations/configurations/399` → **200**; app navigates to **`/credentials/all`**, not to the detail page (**#1711**). Persisted `data`: `{"scopes":["Sites.Read.All"], "site_url":…, "client_id":…, "client_secret":"{{secret.<uuid>}}", "oauth_discovery_endpoint":…}` — **`scopes` is stored as an array** built from the free-text input, and **`auto_refresh_token` is absent** when left unchecked. | ✅ |
| 8 | Verify Login remains on the saved credential detail page | Login present | open `/credentials/all/{id}`: `Delegated` radio checked (derived from the field values), all values round-tripped, **Login** present next to Test connection. `client_secret` renders as the bare vault uuid — known non-defect (digest § NOT a defect — the saved-secret round trip). | ✅ |

## Handles Reference

Provenance verified 2026-08-23 after `cd ../EliteaUI && git fetch origin`.

| Purpose | Handle | Provenance |
|---|---|---|
| Display Name | `toolkit-field-label-input` | on-main ✓ |
| ID (disabled) | `toolkit-field-elitea_title-input` | on-main ✓ |
| Client Id | `toolkit-field-client_id-input` | on-main ✓ |
| Client Secret (wrapper / native input) | `toolkit-field-client_secret-input` / `…-input-field` | on-main ✓ |
| Site Url | `toolkit-field-site_url-input` | on-main ✓ |
| Auth radio — App-only / Delegated | `toolkit-field-auth-radio-app-only` / `toolkit-field-auth-radio-delegated` | on `automation/testids` only (EliteaAI/EliteaUI@c8d5c6af, ELITEA-1962) — awaiting human cherry-pick to `main` |
| Auto Refresh Token (wrapper / native input) | `toolkit-field-auto_refresh_token-checkbox` / `…-checkbox-field` | on `automation/testids` only (same family) |
| Oauth Discovery Endpoint | `toolkit-field-oauth_discovery_endpoint-input` | on-main ✓ (generic schema-driven grammar) |
| Scopes | `toolkit-field-scopes-input` | on-main ✓ (same grammar) |
| Test connection | `credential-form-test-connection-button` | on `automation/testids` (EliteaAI/EliteaUI@5892ae48) |
| Save / Discard | `credential-form-save-button` / `credential-form-discard-button` | on-main ✓ |
| **Login button** | **testid needed: `credential-form-oauth-login-button`** | **needs-adding** — `CredentialForm.jsx:342-350`, a bare `Button.BaseBtn` with no testid. `Button.BaseBtn` spreads `restProps` onto the MUI button, so this is **one attribute** — same one-line shape as its sibling `credential-form-test-connection-button`. Shared with ELITEA-1982; add once. |
| **Logout button** (mutually exclusive twin, `CredentialForm.jsx:333-340`) | **do NOT add** | canon #511 — neither case reaches the logged-in state, so it stays untestid'd |

Auth state is read off the native input
(`[data-testid="toolkit-field-auth-radio-delegated"] input[type=radio]` +
`to_be_checked()`) — no state-switched testid, per `.agents/testing.md`.

## Page-object notes for the implementer

`CredentialCreatePage` already carries everything except the Login button:
`AUTH_METHOD_RADIO` (`select_auth_method(slug)` / `auth_radio(slug)`),
`FIELD_INPUT` + `field()`, `set_display_name()`,
`credential-form-save-button`. What to add:

- `oauth_login_button` — class-level `LocatorDescriptor(testid="credential-form-oauth-login-button")`
  on `CredentialFormFieldsMixin` (both the create and the detail route render the
  same `CredentialForm.jsx`, exactly like `test_connection_button` — digest
  § `CredentialFormFieldsMixin` now owns the shared handles).
- A checkbox handle for `toolkit-field-auto_refresh_token-checkbox-field` if a
  future case toggles it; this case only asserts visibility.
- The Delegated auth slug is **`delegated`** (from the option *value*
  `"Delegated"`, lowercased) — not a label-derived guess.

## Waits & settling

- **Never `networkidle`** on `/credentials/**` (digest, two independent
  incidents). Use `CredentialCreatePage.open_type_form()` — it waits for
  `toolkit-field-label-input`, which only renders after
  `GET /configurations/available/` resolves.
- The auth radio group **re-mounts** when that schema GET resolves: a click
  issued before the form settles is silently lost (hit twice during exploration
  via MCP). Waiting for `toolkit-field-label-input` first is sufficient.
- After Save, settle on the list GET (`CredentialsListPage.reload_list()`), then
  navigate to the detail route and settle on
  `GET /configurations/configuration/399/{id}`.
- Once any field is touched, `page.goto()`/`reload()` raises `beforeunload`.
  Playwright auto-dismisses dialogs in the pytest suite; an MCP session must not.

## Coverage Map

### Axis 1 — every element of the case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in, Credentials accessible | — | `auth_state` | setup | covered |
| Precondition: a project exists | — | project 399 default | setup | covered |
| Step 1 Navigate to Credentials | list loads | direct route to the create form | Step 1 | covered |
| Step 2 Create SharePoint credential | SharePoint fields shown | presence of `client_id`/`client_secret`/`site_url` + **absence** of the three Delegated fields + `App-only` checked | Step 2 | covered |
| Step 3 Select Delegated | Delegated fields appear | radio click + `to_be_checked()` | Step 3 | covered |
| Step 4 Auto Refresh Token / Oauth Discovery Endpoint / Scopes visible | all visible | three visibility assertions | Step 4 | covered |
| Step 5 Login button next to Test connection | Login visible | absence assertion **before** the endpoint is filled, then visibility **after** — both, with a comment naming #1711 | Step 5 | covered (case-text order corrected — **clarification #1711**) |
| Step 6 Fill all required fields | fields accept input | value round-trip assertions on all five fields | Step 6 | covered |
| Step 7 Save | saved with Delegated auth type | `POST …/configurations/399` 200 + response `data` shape (`scopes == ["Sites.Read.All"]`, endpoint present) | Step 7 | covered |
| Step 8 Login remains on detail page | Login present | open the saved credential, assert Login visible | Step 8 | covered (explicit navigation added — **clarification #1711**) |
| Expected Final State | credential saved with OAuth fields populated, Login available | steps 7+8 together | Steps 7-8 | covered |
| Pass criterion "all steps complete without errors" | no errors | console-error side channel over the whole flow | teardown | covered |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why |
|---|---|
| `Delegated` radio still checked on the reloaded detail page | the case says "saved with Delegated auth type" but names no observable for it; this is the only one the product exposes (the auth mode is *derived* from which subsection's fields have values, `ToolSection.jsx:58-72`) |
| Persisted `scopes == ["Sites.Read.All"]` (array, from a free-text input) | the free-text→array conversion is the one non-obvious transformation in this flow and is invisible in the UI |
| Login button **absent** before the endpoint is filled | turns clarification #1711 into a test-enforced invariant instead of a comment — catches a regression that made the button appear unconditionally |
| The three Delegated fields **absent** on arrival (App-only default) | makes step 3 a real state change rather than a presence check that would pass even if the fields rendered eagerly (same discipline as ELITEA-1967's absence union) |

## Known Defects

None found in this flow. Two case-text clarifications filed as **#1711** (not
product bugs — reverse-masking guard: the live contract is asserted, not the
stale wording).

**Retracted, for the record:** #1709 and #1710 were filed by this analysis and
then **retracted as not reproducible** — they were artifacts of a wedged
Playwright-MCP browser context, disproved by the merged
`test_credential_create.py` (green) and by re-running the exact scenario in a
fresh `browser.new_context()`. Nothing in this AFS depends on them.
