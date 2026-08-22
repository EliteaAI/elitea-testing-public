# Surface digest — toolkits-credentials (Configuration/Credential dropdown family)

Confirmed live 2026-08-02 against `http://localhost:5173` (EliteaUI
`automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`), identity
"Test Bot" (`author_id 659`, `personal_project_id 399` = the "Private"
project). Read before driving `CredentialsSelect` (toolkit Configuration
dropdown, credential-create form) on a new case; update after your own run.

## Project topology (identity: Test Bot)

| project_id | name | scope | write access (configurations/toolkits) |
|---|---|---|---|
| 399 | Private | personal (`personal_project_id`) | YES — full CRUD |
| 406 | Bugs & Features | team | READ only (403 on `configurations.configuration.create` / `models.applications.tools.create`) |
| 25 | Elitea Development | team | READ only (same 403 pattern, not individually re-verified) |
| 471 | Elitea Testing Team | team | READ only (confirmed via live 403) |
| 400 | UI Testing | team | **WRITE — credentials CRUD confirmed** (see correction below) |

Project switch (UI): `[data-testid="project-selector-trigger"]` → click →
`[data-testid="select-option-{project_id}"]`. Switch persists across
`page.goto()` within the same browser context (localStorage-backed).

**CORRECTION (2026-08-22, ELITEA-1977):** the "400 = READ only" row above was
never individually verified and was **wrong**. Live-probed all four team
projects with a real `POST /configurations/configurations/{p}`:
471 → **403**, 406 → **403**, 25 → **403**, **400 → 200** (credential created,
probe deleted). Project **400 "UI Testing" is the ONE team project this
identity can create credentials in** — and therefore the only project where a
*project-scoped* create flow (`{"kind":"create_action","private":false}`) can
be executed end-to-end. It is already wired as `settings.users_team_project_id`
(`config.py:207`, `USERS_TEAM_PROJECT_ID=400` in `.env.test`) — use the setting,
never a literal. Toolkit writes are permitted there too (`PUT` returns a 400
validation error, not a 403). Caveat: project 400 contains **zero toolkits of
any type** and only one (s3) credential, so any case needing a toolkit there
must seed it (transit) — `POST /elitea_core/tools/prompt_lib/400` requires a
valid `settings.github_configuration` dict, so seed a Github credential first.

**Project-scope discriminator: `project_id`, NOT `shared`.** A credential
created in team project 400 comes back `shared: false`, exactly like a private
one — `shared` marks cross-project sharing, not scope. The dropdown's own
classification is `private = isConfigurationPersonal`
(`CredentialsSelect.jsx:249`), i.e. "row came from `personal_project_id`", so a
project credential renders as `select-option-{"kind":"saved","elitea_title":
"…","private":false}` and its `"private":true` twin does not exist (count 0).
The saved list itself is `GET /configurations/configurations/{selectedProjectId}`
(`useOriginalConfigurations`, `src/hooks/useConfigurations.js`) — membership-
scoped, which is the mechanism behind "visible to all project members".

**After clicking "Refresh the configurations" the option list RE-MOUNTS.** A
synchronous `option.is_visible()` immediately after the refresh returns
`False` while `text_content()` on the same locator resolves fine (auto-wait).
Use web-first `expect(option).to_be_visible()` — observed live during
ELITEA-1977.

**Toolkit-form Save on a project-400 toolkit stayed DISABLED** (fresh load,
after a credential selection, and after a Description edit); in one earlier
probe where it was enabled, clicking it left the persisted
`github_configuration` unchanged. Not a permission wall (API `PUT` → 400
validation, not 403). Not chased — no case in this batch saves a toolkit; the
interaction-discovery ladder was not exhausted, so it is a **note**, not a
filed bug. Anyone writing a toolkit-form-save case starts here.

**Why the project matters for `CredentialsSelect`:** `Create_Project_Title`
option only renders when `selectedProjectId != personal_project_id`
(`EliteaUI/src/[fsd]/features/credentials/ui/credentials-select/CredentialsSelect.jsx`
`createMenuData` `useMemo`). On project 399 (Test Bot's own personal
project) the CREATE section shows **only** "New private ... credentials" —
the "New project ..." option is entirely absent from the DOM, not just
disabled. Both options render together only in a team project (471 used
here — pick any team project the identity can at least READ).

## CredentialsSelect dropdown — confirmed DOM shape (project 471, toolkit 151 "ProjectAlita/elitea_core")

```
<ul role="listbox" aria-labelledby="simple-select-label-Github Configuration">
  <li role="option">CREATE</li>                                         <!-- ListSubheader, no testid -->
  <li role="option" data-value='{"kind":"create_action","private":true}'>
    New private github credentials                                       <!-- NO data-testid -->
  </li>
  <li role="option" data-value='{"kind":"create_action","private":false}'>
    New project github credentials                                       <!-- NO data-testid; only renders off-personal-project -->
  </li>
  <li role="option">SAVED GITHUB CREDENTIALS <button aria-label="Refresh the configurations">…</button></li>
  <li role="option" data-testid='select-option-{"kind":"saved","elitea_title":"...","private":true|false}'>
    <credential label> <button data-testid="credential-open-in-new-tab-button" aria-label="Open in new tab">
    <!-- credential-status-indicator / credential-reload-button also live here per toolkit_detail_page.py, when invalid -->
  </li>
  ...
</ul>
```

Text renders visually UPPERCASE ("CREATE") via CSS `text-transform` — the
underlying string is `"Create"` / `"Saved github Credentials"` (verify
against rendered `inner_text()`, not raw textContent, if asserting case).

## Confirmed testid gaps (needs-adding — none present on `main` or `automation/testids`, re-verified via fresh `git fetch origin` 2026-08-02)

| Element | Current state | Where to add | Suggested testid |
|---|---|---|---|
| Configuration select **trigger** (combobox button) | `role="combobox"` only, no testid; `Select.SingleSelect` already supports a `dataTestId` prop (renders `${dataTestId}` on the root + `${dataTestId}-combobox` on `SelectDisplayProps`, `SingleSelect.jsx:658-659`) but `CredentialsSelect.jsx`'s `<Select.SingleSelect>` call never passes it | `CredentialsSelect.jsx` — add `dataTestId={\`toolkit-credential-select-${type}\`}` to the `<Select.SingleSelect>` call | `toolkit-credential-select-{type}` (e.g. `toolkit-credential-select-github`), combobox sub-part auto-gets `-combobox` suffix per the shared component |
| CREATE-section option `<li>` (`variant: 'action'`, both private + project) | Bare `<MenuItem>`, no `data-testid` — sibling "saved" branch DOES get one via `SingleSelectMenuItem.jsx:117` (`data-testid={option.testId ?? \`select-option-${option.value}\`}`) because it renders through `SingleSelectDropdown`→`SingleSelectMenuItem`; the action branch bypasses that and renders a bare `MenuItem` directly | `EliteaUI/src/[fsd]/shared/ui/select/SingleSelect.jsx` ~line 411-417 (the `option.variant === 'action'` branch of `renderMenuItems`) — add `data-testid={option.testId ?? \`select-option-${option.value}\`}` to match the sibling branch | Comes for free once added: `select-option-{"kind":"create_action","private":true}` / `...,"private":false}` — same encoding the saved options already use |
| Duplicate-credential-name API-error text ("Credential with ID '…' already exists") | Plain `<Typography variant="bodyMedium" sx={styles.errorMessage}>{apiError}</Typography>`, no testid | `EliteaUI/src/pages/Credentials/CredentialForm.jsx` ~line 352-360 | `credential-form-api-error-message` |
| Configuration-field mismatch footer ("Your configuration does not match any available configurations.") — shown when the linked credential's `elitea_title` no longer resolves against any fetched configuration (e.g. it was deleted) | `<FormControl error><FormHelperText>…</FormHelperText></FormControl>`, no testid | `EliteaUI/src/[fsd]/features/credentials/ui/credentials-select/CredentialMismatchFooter.jsx` ~line 20-26 | `credential-select-mismatch-footer` |

**Note (2026-07-24, orphaned prior attempt):** a dangling, never-merged local
commit from an earlier session claims a testid
`credential-form-api-error-message` was added at `EliteaUI@8c448d99` — that
SHA is a **dangling commit object**, unreachable from any branch
(`git log --all` confirms), and the string is absent from both `main` and
`automation/testids` today. Treat it as **needs-adding**, not existing;
reuse the same proposed name (it's a reasonable one) but the work itself was
lost, not landed.

## Server-side duplicate-name error (confirmed via API, `POST /configurations/configurations/{project_id}`)

```
400 {"error": "Credential with ID '<elitea_title>' already exists", "field": "elitea_title"}
```
Fires when `elitea_title` collides — the create form's ID field **live-mirrors
Display Name** (`credential_form_fields.py`), so a Display-Name collision on
an unedited ID field reproduces this. UI surfaces the exact string visibly
(confirmed live) even though the element carries no testid yet (see gap
table above).

## Credential deletion reflection in a toolkit's Configuration field (ELITEA-1979 step 8)

Deleting a **non-private, non-personal-project** credential that's linked to
a toolkit, then reloading the toolkit's detail page: the Configuration
combobox still renders the (now-orphaned) `elitea_title` text, but in
**red/error styling**, with the `CredentialMismatchFooter` "does not match
any available configurations" text below it (confirmed live, screenshot
`test-results/screenshots/ELITEA-1979-step-08-mismatch.png` pattern). This is
the concrete "empty/error state" the case's Pass criteria describe — it is
NOT a blank/empty field, it's a red mismatched-value + helper-text pair.

## Known defects touching this surface

- **#1004** (OPEN) — GitHub credential create form: Access Token field is
  NOT enforced as required once "Token" auth is selected — Save stays
  enabled and the backend persists a credential with `access_token: null`.
  Re-confirmed live 2026-08-02, identical repro. Relevant to ELITEA-1978
  steps 5-6.
- **#1047** (OPEN, filed as `[Clarification]`) — the Configuration select's
  menu does NOT auto-close after a CREATE-action click (`variant: 'action'`
  options set `skipNextCloseRef.current = true` in `SingleSelect.jsx`,
  making the following `handleMenuClose` a no-op). Re-clicking the trigger
  afterward hits an obscured element (`TimeoutError`). Relevant whenever a
  test returns to the SAME open tab after a CREATE-action click without an
  intervening reload/navigation — not hit in this session's own scripted
  probes (which always did a fresh `page.goto()`/`page.reload()` before the
  next combobox click), but a real trap for anyone assuming "click again to
  reopen."
- **#999** (OPEN, filed 2026-07-23/24: "GitHub toolkit type unavailable for
  creation; existing toolkits locked to Raw JSON") — **appears NO LONGER
  reproducible as of 2026-08-02**: this session created GitHub toolkits via
  both API and the UI type-picker without error (`github` present in the
  type-selector search, `POST .../tools/prompt_lib/399 {"type":"github",...}`
  → 200), and the 3 pre-existing project-471 GitHub toolkits (117/150/151)
  render the full Form view (Configuration tab, tool chips, credential
  dropdown) — none are locked to Raw-JSON-only. Left OPEN (not closed by
  this analyst — closure is human-only per `.agents/profile.md`); flagged
  as a note for the report so a human can verify + close.

## Credential DELETE flow (detail page three-dot menu) — confirmed live 2026-08-22 (ELITEA-1964)

Full path, all testids **pre-existing on `main`** (no `add-data-testid` work
needed — verified by driving the flow live on `localhost:5173`, project 399):

```
/credentials/all/{id}
  [data-testid="controls-menu-button"]            → opens [data-testid="controls-menu"]
    [data-testid="pin-toggle-credential-menuitem"]  "Pin to top"
    [data-testid="delete-credentials-menuitem"]     "Delete"      ← auto-derived by DotMenu.jsx
                                                                    from item key 'delete-credentials'
  → [data-testid="delete-confirm-dialog"]          (shared DeleteEntityModal.jsx)
      delete-confirm-title          "Delete confirmation"
      delete-confirm-message        "Are you sure to delete the {name}? Enter the name to complete the action."
      delete-confirm-entity-name    "{name}"
      delete-confirm-name-input     ← MUI TextField WRAPPER div, not the <input>
      delete-confirm-button         disabled until the typed name === entity name exactly
      delete-confirm-cancel-button
```

- **Type-to-confirm is mandatory here**: `CredentialsControls.jsx` sets
  `shouldRequestInputName: true` on the Delete item, so the confirm button
  stays disabled until the exact Display Name is typed.
- **`skipConfirmation` escape hatch:** `DotMenu.jsx` calls
  `useDeleteConfirmationDisabled()`, which reads the project secret
  `disable_confirmation_delete_mode`. If that secret exists **and** equals
  `"true"`, the dialog is **skipped entirely** and delete fires immediately.
  Not set on project 399 today (dialog confirmed rendering), but any test
  asserting the dialog depends on it staying unset.
- **Network:** `DELETE /configurations/configuration/{project}/{id}` → **204**
  (singular `configuration` segment; the plural one is the list endpoint).
  Then the app `navigate(..., {replace:true})`s back to `/credentials/all`.
- **Known defect `#1666`** (filed 2026-08-22 by the ELITEA-1964 pass, sibling of
  `#1330`): immediately after the 204 the app re-fetches the deleted id —
  `GET /configurations/configuration/{project}/{id}` → **404**, a visible
  console error inside the happy path. Cosmetic; any "no console errors"
  side-channel over a delete flow needs an endpoint-specific filter linked to
  `#1666`.
- **Cheapest honest credential to create for a delete/cleanup case:** Github
  type + Display Name only. Base Url ships pre-filled and **Anonymous** is the
  default auth, so Save enables with just the name — no `GIT_HUB_TOKEN`, no
  `pytest.skip` path, no secret typed. Confirmed live (`POST` → 200).
- **Resolved/added during ELITEA-1964 implementation:** `/credentials/all` does
  NOT reliably settle to `networkidle` — `page.reload()` +
  `wait_for_load_state("networkidle", 15s)` timed out once in two runs on a
  fully-rendered page (background traffic keeps the network busy). Settle on the
  list `GET .../configurations/configurations/{project}?...&section=credentials...`
  response instead; `CredentialsListPage.reload_list()` now does exactly that.
  `CredentialsListPage.card_by_name()` (name-filtered `entity-card`) was added
  for presence AND absence assertions, and `CredentialDetailPage` gained the
  delete-menu + `DeleteEntityModal` handles plus `open_delete_dialog()` /
  `fill_delete_confirm_name()` / `confirm_delete(id)`.

## Credentials LIST page — type filter + view toggle — confirmed live 2026-08-22 (ELITEA-1966 / ELITEA-1973)

Both flows executed end-to-end against `localhost:5173`, project 399. No product
defects found in either.

### Right-hand TYPES panel (type filter, ELITEA-1966)

- Rendered by the **shared** `Categories.jsx` via `CredentialsTypesPanel.jsx`.
  Chips: `[data-testid="tags-panel-chip-{Label}"]`, clear-all:
  `[data-testid="tags-panel-clear-all"]`, empty state:
  `[data-testid="tags-panel-empty-state"]`. Chips + clear-all are **on `main`**.
- **The panel is data-derived, not a fixed vocabulary.** Its source is
  `GET /configurations/types/{project}` which returns ONLY types actually
  present: with one `s3_api_credentials` credential the panel showed exactly one
  chip. **A type-filter test MUST seed its own typed credentials** — Github /
  Jira / Confluence simply do not exist in project 399 by default.
- Chip label = `CredentialNameHelpers.extraCredentialName(type)`:
  `github`→`Github`, `jira`→`Jira`, `confluence`→`Confluence`,
  `s3_api_credentials`→`S3 api credentials`.
- Click = direct activation (no debounce/Enter): mutates URL `?tags[]=Github`
  (`useCredentialTypes`), then `useLoadAllCredentials` maps label→raw type and
  re-fetches server-side with `&type=github`. Selection is a **toggle** —
  clicking the selected chip clears it. `tags-panel-clear-all` renders ONLY
  while ≥1 chip is selected, so it doubles as the "a filter is active" signal.
- **Chip selected-state is NOT assertable**: `StyledChip`'s `isSelected` is a
  styled-prop filtered out of the DOM (CSS background only) — no `data-*`, no
  `aria-pressed`. A future case needing it requires a UI change, not a locator.
- **Removing a filter has a render race**: the follow-up list `GET` resolves
  before the cards re-render, so a synchronous card read right after it can see
  an EMPTY grid (hit on ELITEA-1966's first run). Settle on network **plus**
  `entity-card` first-visible (`CredentialsListPage._settle_unfiltered_list()`).
  The applying direction does not show it.
- `CredentialsList.jsx`'s empty-project redirect explicitly short-circuits while
  a type filter is active (`hasTypeFilter`), so a zero-match filter does NOT
  bounce to `/credentials/create-credential` (unlike the zero-match SEARCH path,
  defect #551).

### Card/Table view toggle + table pagination (ELITEA-1973)

- Toggle buttons are the **cross-page shared** `agent-table-view-button` /
  `agent-card-view-button` (misnamed `agent-` prefix — elitea-testing-public#521),
  both **on `main`**; state read via `aria-pressed`. URL-driven:
  fresh nav has NO `?view=`, table → `?view=table`, back → `?view=cards`.
- Table view for credentials renders exactly 5 columns:
  `Name & Description | Type | Authors | Created | Actions`.
- **Testids added during ELITEA-1973** (EliteaAI/EliteaUI@84446b15, on
  `automation/testids`, awaiting human cherry-pick to `main`) — attribute-only:
  - `credentials-table-column-header-{name,type,author,created_at,actions}`
    (extends `DataTable.jsx`'s existing `columnTestIdPrefix` mcp-branch)
  - `credentials-table-row-name` (mirrors `mcp-table-row-name` in
    `DataTableNameCell.jsx`)
  - `credentials-pagination-{page-info,prev-button,next-button}` (wires
    `GridTablePagination`'s already-supported props, gated on `isCredentials`)
  - Side effect of the shared prefix prop: `credentials-table-sort-icon-*` also
    appears (unreferenced — same as the pre-existing `mcp-table-sort-icon-*`).
  - `pageSizeSelectTestId` deliberately left unwired (nothing references it yet).
- **Pagination needs >20 rows to be observable**: `GridTablePagination` disables
  BOTH arrows when `total <= pageSize` (default 20). Verified with 22
  credentials: `1 - 20 of 22` → Next → `21 - 22 of 22` → Prev → `1 - 20 of 22`.
  Page changes do NOT put a page param in the URL.
- Credentials table rows are **server-paged, not client-sliced**: `DataTable`'s
  `visibleRows` skips the `.slice()` for `isCredentials`/`isToolkits`/`isMCPs`.
- Cheapest honest seeding for a >20 precondition: `credential_api.create_credential`
  with `{"type":"github","data":{"base_url":"https://api.github.com"}}` — no
  token, no secret; ~20 POSTs run in a few seconds. Top up to 21 rather than
  seeding a fixed count (read-only-by-default on whatever already exists).

### Vite HMR caveat (cost 3 turns, 2026-08-22)

After editing `../EliteaUI/src`, the dev server on this OneDrive-backed clone did
**not** pick the change up on `page.goto()` alone — the transformed module was
stale twice in a row. `touch`-ing the edited files and then doing an in-page
`location.reload()` served the new module. If a freshly added testid is "missing"
from the DOM, verify the served module first
(`fetch('/src/…jsx?t='+Date.now())` and grep it) before doubting the edit.

## Credential CREATE form — schema-driven field rendering — confirmed live 2026-08-22 (ELITEA-1967)

All ten types the case names driven end-to-end at
`/credentials/create-credential/{type}` (direct route — the type-card grid on
`/credentials/all` only renders on a zero-credential project). **Zero defects;
the case text matched the live product on every row.**

### The form is 100% backend-schema-driven — read the schema, don't guess

`GET /configurations/available/?section=credentials` is the single source for
every credential type's form. One authenticated call answers "what fields does
type X render, which are secret, which auth options exist, is Test connection
enabled" without opening a browser:

```bash
curl -s -H "Authorization: Bearer $ELITEA_API_TOKEN" \
  "$ELITEA_API_BASE/configurations/available/?section=credentials"
# per item: .type, .has_test_connection, .config_schema.properties.data.properties (fields),
#           .config_schema.properties.data.required,
#           .config_schema.properties.data.metadata.sections.auth.subsections (auth radio options)
```

- 32 credential types available on project 399 (2026-08-22).
- `has_test_connection: false` ⇒ the Test connection button renders **disabled**.
  Of the ten ELITEA-1967 types, **only `postman`** is false.
- `metadata.sections.auth` absent ⇒ **no auth radio group at all**
  (`ado`, `langfuse`, `report_portal`).
- `metadata.sections.auth.required: false` ⇒ `ToolSection.jsx` **prepends a
  synthetic `Anonymous` option with value `none`** (this is why GitHub has an
  Anonymous radio that appears in no schema field list).
- Default-selected auth option = `sectionOptions[0]` when no field has a value
  ⇒ `Anonymous` for GitHub, the first real subsection everywhere else.
  Only the selected subsection's fields render — GitHub on Anonymous shows
  **no** credential field, just Base Url.

### Field-testid grammar (all generic, all derived from the schema property key)

| Shape | Testid | Source |
|---|---|---|
| plain text field | `toolkit-field-{key}-input` (the `<input>`) | `ToolBaseProperty.jsx:589` |
| secret field | `toolkit-field-{key}-input` on the **wrapper `<div>`**, `toolkit-field-{key}-input-field` on the native `<input>` | `SecretField.jsx` derives the `-field` suffix |
| secret field toggle | `toolkit-field-{key}-input-toggle-secret` / `…-toggle-password` | **added by ELITEA-1967**, see below |
| enum dropdown | `toolkit-field-{key}-select` (+ `-select-combobox` on the display node) | **added by ELITEA-1967** |
| auth radio option | `toolkit-field-auth-radio-{slug}`, slug = option VALUE `.toLowerCase().replace(/\s+/g,'-')` | `RadioButtonGroup.jsx:36-37` |
| Test connection button | `credential-form-test-connection-button` | **added by ELITEA-1967** |

Because the grammar is generic, **a new credential type needs no new testid** —
only the page object's expectation table grows.

### Testids added during ELITEA-1967 (EliteaAI/EliteaUI@5892ae48, `automation/testids`, awaiting human cherry-pick to `main`)

Attribute-only, no functional change:
- `credential-form-test-connection-button` — `CredentialForm.jsx`
  (`Button.BaseBtn` spreads `restProps` onto `MuiButton`).
- `toolkit-field-{key}-select` — `ToolBaseProperty.jsx` enum branch
  (`SingleSelect` already accepted a `data-testid` prop; it was simply never passed).
- `toolkit-field-{key}-input-toggle-{secret|password}` — `SecretField.jsx`
  derives `testIdPrefix` from the caller's `data-testid`; `src/components/Toggle.jsx`
  gained an optional `testIdPrefix` prop. **Caller-derived — the shared `Toggle`
  hardcodes no feature-scoped testid.** This one benefits every secret field in the
  app (toolkits included), not just credentials.

### Observed per-type inventory (2026-08-22, verbatim from the live DOM)

Every type also renders `toolkit-field-label-input` (Display Name) and
`toolkit-field-elitea_title-input` (ID, **`disabled` on all ten** — the case text
only annotates "(disabled)" on GitHub, but it holds everywhere).

| type | type-specific fields | secret fields | auth radios (default first) | Test connection |
|---|---|---|---|---|
| github | `base_url` (pre-filled `https://api.github.com`) | — | `none`=Anonymous ✓, `token`, `password`, `app-private-key` | enabled |
| sharepoint | `client_id`, `client_secret`, `site_url` | `client_secret` | `app-only` ✓, `delegated` | enabled |
| ado | `organization_url`, `token` | `token` | **none** | enabled |
| gitlab | `url`, `private_token` | `private_token` | `gitlab-private-token` ✓ | enabled |
| confluence | `hosting` (select, `Auto`), `base_url`, `api_key`, `username` | `api_key` | `basic` ✓, `bearer` | enabled |
| jira | identical to confluence | `api_key` | `basic` ✓, `bearer` | enabled |
| figma | `token` | `token` | `token` ✓ | enabled |
| postman | `base_url`, `workspace_id`, `api_key` | `api_key` | `api-key` ✓ | **DISABLED** |
| langfuse | `base_url`, `public_key`, `secret_key` | `secret_key` | **none** | enabled |
| report_portal | `project`, `endpoint`, `api_key` | `api_key` | **none** | enabled |

### Cheap navigation fact
`/credentials/create-credential/{type}` renders the form with no project-state
precondition, no seeding and no save. A render-inventory case on this surface is
fully read-only.

### `networkidle` is NOT a usable settle condition on the credentials routes

**Resolved/added during ELITEA-1967 implementation:** `BasePage.wait_for_network()`
(`wait_for_load_state("networkidle")`) timed out on the **8th of 10** consecutive
`/credentials/create-credential/{type}` navigations, on a page that was already
fully rendered — a bare `TimeoutError`, not an assertion failure; the immediate
re-run passed. Background DEV-backend traffic keeps the connection count above
zero. This is the same characteristic ELITEA-1964 recorded for `/credentials/all`
(`CredentialsListPage.reload_list()` settles on the list `GET` instead).

For the CREATE form the correct condition is the form's own render signal:
`CredentialCreatePage.open_type_form()` navigates and waits for
`toolkit-field-label-input` to be visible — `CreateCredential.jsx` only builds
`credentialDetails` (and therefore only renders any field) after
`GET /configurations/available/` resolves. `navigate_to_type()` still uses
`wait_for_page_load()`/`networkidle` for its four pre-existing callers; prefer
`open_type_form()` in new work on this form.

## Credential form — Secret/Password field toggle + secret-vault dropdown — confirmed live 2026-08-22 (ELITEA-1968 / ELITEA-1969)

Both flows executed end-to-end against `localhost:5173`, project 399
("Private", which IS this identity's `personal_project_id`). No product defects
found; four **case-text** divergences recorded (see the two AFS files).

### The field: `SecretField.jsx` (shared, `[fsd]/shared/ui/secret-field/`)

Rendered for every schema property marked secret — GitHub `access_token` under
`Token` auth, Jira/Confluence `api_key`, etc. Two mutually-exclusive modes,
switched by a `ToggleButtonGroup`:

| Mode | Renders | Handles |
|---|---|---|
| `password` (**the default** — `useState(toggleOptions[1].value)`) | native `<input type="password">` | `toolkit-field-{key}-input-field` |
| `secret` | a `SingleSelect` over the project's secret vault | `toolkit-field-{key}-input-combobox` |

- Both toggle buttons carry `aria-pressed` — mode state is assertable
  testid-only, no CSS sniffing: `…-input-toggle-secret` / `…-input-toggle-password`.
- **Switching modes CLEARS the value** (`handleToggleTab` → `onChange(e, '')` +
  `setRawPasswordInput('')`). Don't write a test that expects a value to survive
  a round trip through the other mode.
- The vault query is `skip`-gated on the mode: `GET /secrets/secrets/default/{project}`
  fires only when the field first enters Secret mode, then RTK-Query-caches.
- A field bound to `{{secret.<name>}}` auto-lands in Secret mode on load
  (`handleSwitchToSecretTab`), unless the referenced secret no longer resolves.

### The dropdown (open the combobox with a REAL click)

```
ul[role="listbox"]
  [data-testid="select-group-header-Create"]            → renders "CREATE"  (CSS uppercase)
  [data-testid="select-option-__create_private_secret__"]
  [data-testid="select-group-header-Saved Secrets"]     → renders "SAVED SECRETS"
      + refresh button  [data-testid="{field-testid}-refresh-secrets-button"]   ← ADDED 2026-08-22
  [data-testid="select-option-{{secret.<name>}}"]  ×N   → option TEXT is the bare name
```

- The saved option's **value** is the template `{{secret.<name>}}`; the
  combobox **displays** the bare name. Assert both — a UI showing the right
  name while storing the wrong value passes a text-only check.
- **The CREATE option's label is project-scope-dependent:**
  `personal_project_id === selectedProjectId ? 'New Private Secret' : 'New Project Secret'`.
  On the automation default project (399 = personal) it reads **"New Private
  Secret"**. Its testid and behaviour are identical in both scopes. Both
  ELITEA-1968 and ELITEA-1969 case texts say "New Project Secret" — a case-text
  clarification, not a bug.
- The CREATE group renders at all only when the identity holds
  `PERMISSIONS.secrets.create`; without it `createSecretsOptions` is `[]` and
  the entire group is absent from the DOM.
- **Clicking the CREATE option opens a NEW TAB** —
  `window.open('{basename}/{projectId}/settings/secrets?createSecret=1', '_blank')`.
  Not an in-page navigation. Capture it with `context.expect_page()`.
  The originating tab keeps its dropdown **OPEN** (the #1047 `skipNextCloseRef`
  mechanism) — convenient, but assert it rather than assume it.
- `?createSecret=1` **auto-opens the inline create row** on the secrets page
  (same `addSecretRow()` the "+" button calls) and `secrets-add-button` is then
  `disabled`. A test cannot "click +" after arriving this way.
- The MUI menu will NOT close from a JS `document.body.click()` — use a real
  Playwright click, `Escape`, or select an option.
- **The group headers render BEFORE the vault list resolves.** `useSecretsListQuery`
  is `skip`-gated on the field's mode, so the first entry into Secret mode opens a
  menu with both headers present and an EMPTY group body. Wait on the first
  saved-secret option, never on the header alone (cost one rerun, ELITEA-1968);
  `networkidle` remains unusable on these routes.
- **Assert the group headers' UNDERLYING strings** (`Create` / `Saved Secrets`).
  The all-caps rendering is CSS `text-transform`; Playwright's `to_have_text`
  reads `textContent` and never sees it — while a browser-console `innerText`
  probe DOES return `CREATE` / `SAVED SECRETS` and will mislead you (cost one
  rerun, ELITEA-1968/1969).

### Open testid gap — the Secret-mode select's bound VALUE
The combobox DISPLAYS the secret's bare name; the `{{secret.<name>}}` template it
actually stores lives on MUI's hidden `MuiSelect-nativeInput`, which carries **no
testid**. `SingleSelect.jsx` forwards an `inputProps` prop to `<Select>`, but that
does not reach the native input on this MUI version (tried live 2026-08-22 and
reverted). Wiring it needs `slotProps.htmlInput` on the shared `SingleSelect` —
a bigger shared-component change than ELITEA-1968 warranted, so the value
assertion was dropped there. Pick this up if a case needs to prove
displayed-name-vs-stored-value.

### Testids added during ELITEA-1968/1969 (EliteaAI/EliteaUI@29214bf1, `automation/testids`, awaiting human cherry-pick to `main`)

Attribute-only, no functional change:
- `{field-testid}-refresh-secrets-button` — `SecretField.jsx`, derived from the
  caller's `data-testid` exactly like the existing `-field` / `-toggle-*`
  derivations, so the shared component hardcodes no feature-scoped testid and a
  page with several secret fields keeps one unique handle per field.
- `secret-column-header-{name,secretValue,actions}` — `SecretsTable.jsx` now
  passes `GridTableHeader`'s already-supported `columnTestIdPrefix="secret"`
  (identical mechanism to `TokensTable.jsx`'s `personal-token-*`). Side effect:
  `secret-sort-icon-name` also renders, unreferenced — same precedent as
  `credentials-table-sort-icon-*`.

### Project 471 is NOT a usable substitute for the personal project here
Evaluated live and rejected: it carries **zero** secrets (nothing to select for
ELITEA-1968 step 5 without seeding a shared team project), and its
`/settings/secrets` reproduces known defect **#1203** ("Maximum update depth
exceeded", hundreds of console errors per mount). #1203 was re-confirmed on
project 399 too — it is page-wide, not project-specific.

### Unsaved-form `beforeunload` trap
Once anything on the credential create form is touched, `page.goto()` /
`reload()` raises a `beforeunload` dialog. Playwright auto-dismisses dialogs by
default in the pytest suite, but an MCP-driven exploration session must handle
it explicitly or the navigation hangs to timeout.

## Credential "Test connection" — confirmed live 2026-08-22 (ELITEA-1970)

Whole flow driven end-to-end on `localhost:5173`, project 399. **No product
defects.** One test-environment finding (`#1673`) and one plausible-looking
non-defect ruled out (secret round-trip, below).

### The mechanism (type-agnostic)

`CredentialForm.jsx` → `useCreateConfiguration.onTestConnection` →
`POST /configurations/check_connection/{project}/{type}`:

| Outcome | HTTP | Body | UI |
|---|---|---|---|
| success | **200** | `{"success": true}` | success toast `The connection is OK!` (`toast-alert[data-severity="success"]` + `toast-message`) |
| failure | **400** | `{"success": false, "message": "<service reason>"}` | **inline** error on the offending field: `aria-invalid="true"` + helper text carrying the backend `message` **verbatim** |

Which surface the failure lands on is decided by
`credentialError.helpers.js#extractInformationFromCredentialError`: it maps
the message onto schema keys (title/description/value/key substring match,
plus `authentication` → any secret field, plus `url` → any `*url*` key). Any
mapped key ⇒ per-field `validationErrorMessages` + `showValidation`. **Only
when nothing maps** does it fall back to the global
`credential-form-api-error-message` banner. An auth failure always maps, so
that banner stays ABSENT for a bad token — assert accordingly.
Note the mapping is deliberately loose: `Authentication failed: Invalid
username or API key` lit up BOTH `api_key` and `username` on Jira (two
identical helper texts) — count helper texts per FIELD, never globally.

### Testid added during ELITEA-1970 (EliteaAI/EliteaUI@58955184, `automation/testids`, awaiting human cherry-pick to `main`)

- `{field-testid}-helper-text` — `SecretField.jsx`, caller-derived from
  `inputProps['data-testid']` exactly like the existing `-field` /
  `-toggle-*` / `-refresh-secrets-button` derivations, wired through MUI v7
  `slotProps.formHelperText`. Attribute-only (one `const`, one slotProps
  entry) — no new node, no hook, no behaviour change. Benefits every secret
  field in the app, not just credentials.
- Still missing (nobody has needed it): the same handle on the **plain**
  (non-secret) fields' helper text, which `ToolBaseProperty` renders through
  its own `TextField`/`FormInput` path.

### NOT a defect — the saved-secret round trip (ruled out, don't re-file)

Saving a credential turns its secret into a vault template:
`data.api_key == "{{secret.<uuid4hex>}}"` (`GET /configurations/configuration/{project}/{id}`).
On the detail page that field renders in **password** mode showing the
**bare uuid name** (not the template, and not Secret mode — the auto-created
entry isn't in the visible vault, so `handleSwitchToSecretTab` doesn't take).
Test connection then posts that bare name. It looks broken and is not: the
backend resolves it — with valid Jira data the post-save detail-page test
returns `{"success": true}` and the OK toast.

### `GIT_HUB_TOKEN` is EXPIRED (`#1673`, `question`) — plan around it

`.env.test`'s `GIT_HUB_TOKEN` returns **401** from `https://api.github.com/user`
(both `Bearer` and `token` schemes). Consequences for this surface:

- Any case needing a **successful** GitHub connection is not producible today;
  ELITEA-1970 was executed and automated on **Jira** instead (declared in its AFS).
- GitHub cases that only need the credential to EXIST are unaffected —
  Anonymous auth still passes: `POST check_connection/{p}/github` with just
  `{"base_url": "https://api.github.com"}` → `{"success": true}`.
- The `JIRA_*` trio in `.env.test` **is valid** (verified via
  `check_connection/{p}/jira` → `{"success": true}`) — it is the cheapest
  honest "working credential" on this surface. `POSTMAN_*`, `CONFLUENCE_*`,
  `ADO_*`, `BITBUCKET_*` exist too but were not validated.
- Cheap one-call validity probe for any type, no browser:
  `curl -XPOST -H "Authorization: Bearer $ELITEA_API_TOKEN" -d '<data>' \
   "$ELITEA_API_BASE/configurations/check_connection/399/<type>"`.

### Vite transform cache — worse than the caveat above (cost 3 turns)

After editing `SecretField.jsx`, `touch` + in-page reload was **not** enough:
a plain `GET /src/…/SecretField.jsx` returned the OLD transform while
`GET …?t=<now>` returned the new one, so the browser (which requests without
the query) kept running stale code and the new testid resolved 0 times.
Fix that worked: kill the dev server, `rm -rf node_modules/.vite`, restart.
Verify with `curl -s http://localhost:5173/src/... | grep -c <new-testid>`
**without** a cache-busting query before blaming your edit.

### Display Name is capped at 32 chars — silently TRUNCATED, not rejected

`ToolBaseProperty.jsx:589` applies `maxLength = MAX_NAME_LENGTH` (= 32,
`src/common/constants.js`) to the `label` field on every credential/toolkit
form. A longer generated name is cut by the input itself, so the create
response comes back with a *different* `label`/`elitea_title` than the test
typed and every subsequent lookup-by-name misses. Keep generated names
(`autotest_cred_<what>_<epoch>`) under 32 characters — an epoch timestamp
alone is 10. Cost one run on ELITEA-1970 (33 chars → 32 stored).

### `CredentialFormFieldsMixin` now owns the shared `CredentialForm.jsx` handles

Promoted out of `CredentialCreatePage` during ELITEA-1970 (both the create and
the detail route render the same `CredentialForm.jsx`):
`test_connection_button`, `api_error_message`, `FIELD_SECRET_INPUT` +
`secret_native_input()`, plus new `FIELD_HELPER_TEXT` +
`secret_field_helper_text()`, `replace_secret_value()`, toast handles
(`toast_alert` / `toast_message` / `TOAST_ALERT_SEVERITY` / `success_toast()`).
Both page objects inherit them, so `create_page.test_connection_button` still
resolves — regression-verified against the three specs that call them
(`test_credential_type_specific_form_fields`, `test_credential_secret_password_toggle`
pass; `test_credential_duplicate_mismatch_validation` is the pre-existing
sanctioned-RED `#1004` signature, unchanged).
