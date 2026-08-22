# Test Case: Credential — Type-Specific Form Fields

## Metadata
- **TMS ID**: ELITEA-1967
- **Linked Story**: none
- **Priority**: l2 (case frontmatter `priority: medium` + body header
  `Priority: medium`, consistent — mapped `high`→l1 / `medium`→l2 / `low`→l3
  per the convention established by ELITEA-1965/1966/1971/1972/1974/1975)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`), project
  `Private` / `${ELITEA_PROJECT_ID}`=399, identity "Test Bot"
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. Per `.agents/test-automation.yaml` § `intake`,
  `draft` is intake-eligible. Proceeded to full live execution 2026-08-22 —
  all 10 steps driven against the live app.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` skips login).
- Project `Private` (399) selected. **No project-state precondition beyond
  that** — this case never leaves the create form, never saves, and reads
  nothing from the credentials list.
- The 10 credential types the case names must be offered by the backend for
  this project. Live-verified 2026-08-22 via the form's own data source
  `GET /configurations/available/?section=credentials` → 32 types, all 10
  present: `ado, confluence, figma, github, gitlab, jira, langfuse, postman,
  report_portal, sharepoint`.

## Test Data

### reuse-existing (no seeding, no cleanup — Hard Rule 10 read-only-by-default)
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- **Nothing is created, saved or deleted.** The case's observable is what the
  *create form renders* for a given type; that is reachable by navigating to
  `/credentials/create-credential/{type}` and reading the rendered form. The
  earlier "click a type card on `/credentials/all`" entry point is NOT usable
  (the type-selector grid only renders on a zero-credential project — see
  `CredentialCreatePage.navigate_to_type()`'s docstring, ELITEA-1963); the
  direct route is the stable one and lands on the identical form.
- No credential secrets are needed: no field is filled, no Save, no Test
  connection click. `GIT_HUB_TOKEN` / `JIRA_API_KEY` are irrelevant here, so
  this case has **no `pytest.skip` path**.

## Test Steps

Each case step is the same shape: navigate to the type's create form, then
assert (a) the exact set of type-specific fields rendered, (b) the exact set of
auth-method radio options, (c) the Test connection button's enabled/disabled
state. Every step additionally asserts the two invariant fields the case names
in every row — Display Name (`toolkit-field-label-input`) and ID
(`toolkit-field-elitea_title-input`, **disabled**).

"Exact set" is asserted **bi-directionally**: the expected fields are asserted
VISIBLE, and every field in the union of all ten types' fields that this type
should NOT render is asserted `to_have_count(0)`. Same for auth radios (union
of all ten slugs). This is what makes "renders **exactly** the expected fields
… no missing, no extra" (case Pass/Fail criteria) an actual assertion rather
than a presence-only smoke check.

1. **GitHub** (`/credentials/create-credential/github`) — case step 1.
   - **Verify**: Display Name visible; ID visible AND `disabled`; Base Url
     (`toolkit-field-base_url-input`) visible with value
     `https://api.github.com` (product pre-fill, from the schema default);
     auth radios exactly `Anonymous` (`…auth-radio-none`, **checked** by
     default), `Token` (`…-token`), `Password` (`…-password`),
     `App private key` (`…-app-private-key`); Test connection button visible
     and **ENABLED**. Absent: every other field/radio in the union.
2. **SharePoint** — case step 2.
   - **Verify**: Client Id (`…client_id-input`), Client Secret
     (`…client_secret-input` + secret-toggle pair `…-input-toggle-secret` /
     `…-input-toggle-password`), Site Url (`…site_url-input`); auth radios
     exactly `App-only` (`…-app-only`, checked) and `Delegated`
     (`…-delegated`); Test connection **ENABLED**.
3. **ADO** — case step 3.
   - **Verify**: Organization Url (`…organization_url-input`), Token
     (`…token-input` + secret-toggle pair); **no auth radio at all** — every
     `toolkit-field-auth-radio-*` slug in the union asserted count 0; Test
     connection **ENABLED**.
4. **GitLab** — case step 4.
   - **Verify**: Url (`…url-input`), Private Token (`…private_token-input` +
     secret-toggle pair); auth radios exactly `GitLab private token`
     (`…-gitlab-private-token`, checked — the only option); Test connection
     **ENABLED**.
5. **Confluence** — case step 5.
   - **Verify**: Hosting dropdown (`toolkit-field-hosting-select`) visible with
     displayed value `Auto`; Base Url; auth radios exactly `Basic`
     (`…-basic`, checked) and `Bearer` (`…-bearer`); Api Key
     (`…api_key-input` + secret-toggle pair); Username (`…username-input`);
     Test connection **ENABLED**.
6. **Jira** — case step 6. Identical expectation set to Confluence (the two
   schemas are field-for-field identical — verified against
   `/configurations/available/`), asserted independently.
7. **Figma** — case step 7.
   - **Verify**: auth radios exactly `Token` (`…-token`, checked — only
     option); Token (`…token-input` + secret-toggle pair); **no Base Url**;
     Test connection **ENABLED**.
8. **Postman** — case step 8.
   - **Verify**: Base Url, Workspace Id (`…workspace_id-input`); auth radios
     exactly `API Key` (`…-api-key`, checked — only option); Api Key
     (`…api_key-input` + secret-toggle pair); Test connection visible and
     **DISABLED** — the one type in the case where it is disabled. Product
     mechanism: the type's schema carries `has_test_connection: false`
     (`check_connection_supported: false`), which `CredentialForm.jsx`
     turns into `disabled` on the button.
9. **Langfuse** — case step 9.
   - **Verify**: Base URL, Public Key (`…public_key-input`), Secret Key
     (`…secret_key-input` + secret-toggle pair); **no auth radio**; Test
     connection **ENABLED**.
10. **Report Portal** — case step 10.
    - **Verify**: Project (`…project-input`), Endpoint (`…endpoint-input`),
      Api Key (`…api_key-input` + secret-toggle pair); **no auth radio**;
      Test connection **ENABLED**.

### Interaction-discovery note (role-overrides.md ladder — not needed here)
No control is *activated* by this case: it is a pure render-inventory case.
The one thing worth recording is that a type's form is reached by URL
(`/credentials/create-credential/{type}`), route
`CreateCredentialTypeFromMain` in `EliteaUI/src/routes.js` — no card click, no
dropdown, no search box. All ten routes resolved first try in the live run.

## Expected Results
- Each of the ten types renders exactly the field set the case names — no
  missing field, no extra field (asserted in both directions).
- The auth-method radio group is present only for types whose schema declares
  `metadata.sections.auth`; ADO, Langfuse and Report Portal declare none and
  render no radio at all.
- The default-selected auth option is the first option: `Anonymous` for GitHub
  (whose auth section is `required: false`, which is what prepends the
  synthetic `Anonymous`/`none` option — `ToolSection.jsx`), and the first real
  subsection for every other type (`App-only`, `Basic`, `Token`, `API Key`,
  `GitLab private token`).
- Secret fields render a Secret/Password toggle; plain fields do not.
- Test connection is enabled for nine types and **disabled for Postman**.
- No console errors at any step (standard side-channel; see § Automation Hints
  for the one filter applied).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS § Preconditions | `auth_state` fixture | asserted (implicitly — the form only renders authenticated) |
| Precondition: project exists, Credentials section accessible | — | AFS § Preconditions | every step navigates the credentials route successfully | asserted |
| Test Data: 10 credential types under test | all offered | AFS § Preconditions | the 10 create-form routes each render (each step's `navigate_to_type` + Display-Name wait) | asserted |
| 1 GitHub | Display Name, ID (disabled), Base Url pre-filled `https://api.github.com`, Auth radio (Anonymous, Token, Password, App private key), Test connection enabled | AFS step 1 | step 1: field-set equality (present + absent), radio-set equality + labels, `base_url` value, ID `to_be_disabled()`, TC `to_be_enabled()` | asserted |
| 2 SharePoint | Display Name, ID, Client Id, Client Secret (Secret/Password toggle), Site Url, Auth radio (App-only, Delegated), TC enabled | AFS step 2 | step 2, same shape + toggle-pair visible on `client_secret` | asserted |
| 3 ADO | Display Name, ID, Organization Url, Token (toggle); no Auth radio; TC enabled | AFS step 3 | step 3, same shape; all 10 auth slugs `to_have_count(0)` | asserted |
| 4 GitLab | Display Name, ID, Url, Auth radio (GitLab private token only), Private Token (toggle), TC enabled | AFS step 4 | step 4, same shape | asserted |
| 5 Confluence | Display Name, ID, Hosting dropdown (Auto), Base Url, Auth radio (Basic, Bearer), Api Key (toggle), Username, TC enabled | AFS step 5 | step 5, same shape + `hosting-select` visible with text `Auto` | asserted |
| 6 Jira | same set as Confluence | AFS step 6 | step 6, asserted independently (not shared with step 5) | asserted |
| 7 Figma | Display Name, ID, Auth radio (Token only), Token (toggle), TC enabled | AFS step 7 | step 7, same shape | asserted |
| 8 Postman | Display Name, ID, Base Url, Workspace Id, Auth radio (API Key only), Api Key (toggle), **TC DISABLED** | AFS step 8 | step 8, same shape + TC `to_be_disabled()` | asserted |
| 9 Langfuse | Display Name, ID, Base URL, Public Key, Secret Key (toggle); no Auth radio; TC enabled | AFS step 9 | step 9, same shape | asserted |
| 10 Report Portal | Display Name, ID, Project, Endpoint, Api Key (toggle); no Auth radio; TC enabled | AFS step 10 | step 10, same shape | asserted |
| Expected Final State: "each type presents its correct set of fields, auth options, and Test connection state" | — | AFS steps 1–10 | as above | asserted |
| Pass: "each credential type renders exactly the expected fields … no incorrect, missing, or extra fields" | — | all steps | the **absence** half of every step (union-complement `to_have_count(0)`) | asserted |
| Pass: "all steps complete without errors" | — | all steps | console side-channel assertion at the end | asserted |

### Axis 2 — Analyst additions
- **Absence assertions on the union-complement of fields and auth radios** —
  *added: the case's Fail criterion names "extra fields" explicitly, and a
  presence-only check cannot see an extra field. The union is closed and small
  (22 field stems, 10 radio slugs), so the complement is enumerable.*
- **`checked` state of the default auth option** — *added: the case names the
  auth options but not which is pre-selected. The default is
  product-determined (`ToolSection.jsx` picks `sectionOptions[0]`), it is what a
  user actually sees on arrival, and it is what decides which type-specific
  fields render at all (GitHub shows no credential field precisely because
  `Anonymous` is default). Without it, step 1's "no access_token field" absence
  assertion would be unexplained.*
- **Radio LABEL text assertion** — *added: the testid slug is derived
  (`value.toLowerCase().replace(/\s+/g,'-')`), so asserting only the testid
  would not catch a label rename. The case names the labels ("Anonymous",
  "App private key", …), so the label is part of the contract.*
- **Secret/Password toggle asserted as a visible pair of controls** —
  *the case writes "(Secret/Password toggle)" against six fields; asserting the
  toggle's two buttons is the direct reading. Required an `add-data-testid`
  round — see § Concrete Handles.*
- **ID field asserted `disabled` on every type, not just GitHub** — *the case
  writes "ID (disabled)" only in step 1 but plain "ID" in steps 2-10; live
  observation shows it is disabled on all ten. Asserting the live contract on
  all ten (rather than the case's shorthand) is the reverse-masking-guard
  reading — see § Known Defects/Gaps note 2.*
- **No console errors** — *added, standard side-channel check.*

## Cleanup
None. The test never mutates server state: no credential is created, saved,
or deleted; the form is never submitted. Read-only-by-default (Hard Rule 10).

## Concrete Handles (discovered during exploration)

Locator policy: **testid-only** (`.agents/testing.md` § Locator policy).
Provenance verified 2026-08-22 after `cd ../EliteaUI && git fetch origin`.

| Element | Testid | Provenance |
|---|---|---|
| Display Name input | `toolkit-field-label-input` | **on-main ✓** (shared `ToolBaseProperty`) |
| ID input (disabled, mirrors Display Name) | `toolkit-field-elitea_title-input` | **on-main ✓** |
| Any plain text field | `toolkit-field-{field}-input` (dynamic; `{field}` is the schema property key — `base_url`, `client_id`, `site_url`, `organization_url`, `url`, `username`, `workspace_id`, `public_key`, `project`, `endpoint`) | **on-main ✓** (`ToolBaseProperty.jsx:589`) |
| Any secret field — wrapper | `toolkit-field-{field}-input` (a `<div>`, not an `<input>`) | **on-main ✓** (`SecretManagementInput` → `SecretField`) |
| Any secret field — native input | `toolkit-field-{field}-input-field` | **on-main ✓** (`SecretField.jsx` derives the `-field` suffix) |
| Secret/Password toggle buttons | `toolkit-field-{field}-input-toggle-secret` / `…-toggle-password` | **needs-adding → ADDED** for this case, EliteaAI/EliteaUI@5892ae48 on `automation/testids` (awaiting human cherry-pick to `main`) |
| Enum dropdown (Jira/Confluence `Hosting`) | `toolkit-field-{field}-select` (+ `-select-combobox` on the display node, free from `SingleSelect`) | **needs-adding → ADDED**, same commit |
| Auth-method radio option | `toolkit-field-auth-radio-{slug}` (dynamic; slug = the option VALUE lowercased with spaces→hyphens — `none`, `token`, `password`, `app-private-key`, `app-only`, `delegated`, `gitlab-private-token`, `basic`, `bearer`, `api-key`) | **on-main ✓** (`RadioButtonGroup.jsx:36-37`) |
| Test connection button | `credential-form-test-connection-button` | **needs-adding → ADDED**, same commit |

### `add-data-testid` work performed (EliteaAI/EliteaUI@5892ae48, `automation/testids`)
All three additions are attribute-only (no new DOM node, no new hook, no
replaced MUI built-in); the only removed line in the diff is `Toggle.jsx`'s
function signature, which is mandatory plumbing for a new optional prop.

1. `credential-form-test-connection-button` — `src/pages/Credentials/CredentialForm.jsx`.
   `Button.BaseBtn` spreads `restProps` onto `MuiButton`, so the attribute
   passes straight through.
2. `toolkit-field-{field}-select` — `ToolBaseProperty.jsx`'s enum branch.
   `SingleSelect` already accepts a `data-testid` prop and derives
   `${dataTestId}-combobox` for its display node.
3. `toolkit-field-{field}-input-toggle-{secret|password}` — `SecretField.jsx`
   derives `testIdPrefix` from the caller-supplied `data-testid` (exactly the
   pattern it already uses for the native input's `-field` suffix) and passes
   it to `src/components/Toggle.jsx`, which gained an optional `testIdPrefix`
   prop. The shared `Toggle` hardcodes **no** feature-scoped testid — the
   value is caller-derived, per `.agents/testing.md` § Locator policy
   ("shared components never hardcode feature-scoped testids").

### Page object impact (as shipped)
`automation/pages/credential_create_page.py` gains, as class-level constants /
methods — all **additive**, nothing existing modified:
```python
FIELD_INPUT        = '[data-testid="toolkit-field-{}-input"]'
FIELD_SECRET_TOGGLE = '[data-testid="toolkit-field-{}-input-toggle-{}"]'
FIELD_SELECT       = '[data-testid="toolkit-field-{}-select"]'
test_connection_button = LocatorDescriptor(testid="credential-form-test-connection-button", ...)
```
plus the accessors `field(field_key)`, `secret_toggle(field_key, mode)` and
`field_select(field_key)`, and `open_type_form(credential_type)` (see
§ Known Defects/Gaps note 4). The existing `AUTH_METHOD_RADIO` constant and
`auth_radio()` accessor are reused unchanged; `navigate_to_type()` and
`wait_for_page_load()` are left byte-identical for their existing callers.

`FIELD_INPUT` intentionally covers BOTH shapes: on a plain field the testid is
on the `<input>`, on a secret field it is on the `SecretField` wrapper `<div>`
— so one template serves presence and absence assertions for every field. The
secret field's native `…-input-field` input is not needed by this case (no
field is ever filled).

## Network Behavior
- `GET /api/v2/configurations/available/?section=credentials&section=storage`
  — the form's schema source; every field, every auth subsection and
  `has_test_connection` come from this response. The form renders after it
  resolves; `CredentialCreatePage.wait_for_page_load()` (network settle +
  Display-Name field visible) is the correct wait. **No sleeps.**
- Nothing is POSTed: the case never saves and never clicks Test connection
  (which would fire `POST /configurations/check_connection/{project}/{type}`).

## Known Defects Found During Exploration
1. **None.** All ten case steps behaved exactly as the case specifies, first
   try, 10/10. Every field name, every auth option label, and the
   Postman-only Test-connection-disabled expectation matched the live product
   byte-for-byte. This case is an unusually accurate piece of case text.
2. **Case-text shorthand (not a defect, no clarification filed):** the case
   annotates the ID field as "(disabled)" only in step 1 and writes bare "ID"
   in steps 2-10. Live, the ID field is disabled on **all ten** types (it
   live-mirrors Display Name — same `ToolBaseProperty` renderer everywhere).
   The AFS asserts the live contract on all ten. Not filed as a case-text
   clarification because the case never asserts ID is *enabled* anywhere — it
   is an omission of repetition, not a contradiction.
3. **Fidelity note:** no substitution of any kind is used. Every asserted value
   (field presence, radio labels, `Auto` hosting default, the pre-filled
   `https://api.github.com`, the Test-connection disabled state) is rendered by
   the product from a live backend schema response. No `page.route`, no
   `page.evaluate` in the shipped test, no injected state.

### Implementer-phase addendum — discovered during automation

4. **`networkidle` does not reliably settle on the credentials routes (not a
   defect — a wait-strategy fact).** The first full implementation run failed
   on **step 8 of 10** with a bare
   `TimeoutError: Timeout 10000ms exceeded` raised from
   `BasePage.wait_for_network()` → `wait_for_load_state("networkidle")`, on a
   page that was already fully rendered (seven prior navigations settled fine;
   an immediate re-run passed). Background traffic against the shared DEV
   backend keeps the connection count above zero. Same characteristic already
   recorded for `/credentials/all` by ELITEA-1964
   (`test-specs/toolkits-credentials/_surface.md`).
   Fixed additively: `CredentialCreatePage.open_type_form()` navigates and then
   waits for the Display Name field to be visible — which IS the product's own
   "schema resolved, form rendered" signal, since `CreateCredential.jsx` only
   builds `credentialDetails` once
   `GET /configurations/available/` has returned. No sleep, no idle heuristic.
   `navigate_to_type()` is untouched for its four existing callers.
   Side benefit: the spec's runtime dropped from ~91s to ~85s.

## Blocked Steps
None — all 10 case steps executed and observed live on 2026-08-22 against
`http://localhost:5173`.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Markers: `ui`, `credentials`, `p2`, `regression`.
- **One test, ten `allure.step("Step N — …")` blocks** — not a parameterized
  test. Rationale: (a) this is ONE TMS case with ten sequential steps, and the
  project's step-reporting convention is one `allure.step` per AFS step;
  (b) a parameterized test would produce ten node ids of the form
  `test_x[github]`, and the TMS back-write's Form C correlation key is built
  from the JUnit `classname + "." + name` — the `[param]` suffix would not
  correlate (`.agents/test-automation.yaml` § `backwrite_on_done`);
  (c) each parameterized row would pay a fresh browser context.
- The per-type expectation table lives as a module-level constant in the spec
  (a `TYPE_EXPECTATIONS` dict), with the union sets derived from it — so
  "absent" is computed, never hand-maintained twice.
- No seeding, no teardown, no `pytest.skip` path.
- Console filter: apply only this suite's `#554` prompt_lib-404 filter
  (`toolkitTypes` RTK-Query race, pinned to the
  `.../toolkits/prompt_lib/` URL shape). Do NOT copy the `#518`
  `<CredentialsList>`-crash filter — that component is never rendered by this
  case, and #518 is CLOSED as NOT REPRODUCIBLE
  (`tests/unit/test_credentials_console_filters_scope.py` pins this).
