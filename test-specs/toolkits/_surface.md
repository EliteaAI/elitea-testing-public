# Toolkits surface — exploration digest

Handle cache from live runs. **Verify each handle as you use it** — this is a cache, not
a source of truth. Update/prune what drifts.

_Created 2026-09-10 (qa-engineer, #2123 / ELITEA-1141) from live runs against
`http://localhost:5173` (EliteaUI `automation/testids`, DEV backend), project 399._

## Toolkit creation wizard — `/toolkits/create`

### Reaching the form

- **`GET /toolkits/create/{type}` does NOT render the form.** It renders the *type
  picker* (header reads "New Github Toolkit", body reads "Choose the toolkit type").
  The type card must be **clicked**. This is the opposite of the *credential* form,
  where `CredentialCreatePage.navigate_to_type()` deep-links fine.
- Use `ToolkitCreationPage.select_toolkit_type(search_term, type_key)` — search +
  `[data-testid="toolkit-type-card-{type_key}"]` click.
- The picker renders **71 cards** (12 category tabs) and takes ~1.2 s after navigation.
  Never locate a card by text: `get_by_text("GitHub").first` is ambiguous across
  categories and card labels.

### Confirmed testids (all on `origin/main`, verified 2026-09-10 after `git fetch`)

| element | testid |
|---|---|
| type-picker search | `toolkit-wizard-type-search-input` |
| category tab | `category-filter-tab` (one shared value) |
| type card | `toolkit-type-card-{type_key}` |
| Toolkit Name | `toolkit-form-name-input` |
| Description | `toolkit-form-description-input` |
| schema-driven field | `toolkit-field-{schema_key}-input` |
| schema-driven checkbox | `toolkit-field-{schema_key}-checkbox-field` |
| credential select (display) | `toolkit-credential-select-{type}` |
| credential select (combobox) | `toolkit-credential-select-{type}-combobox` |
| credential dropdown option | `select-option-{"kind":"saved","elitea_title":"…","private":…}` |
| Save | `toolkit-form-save-button` |
| Cancel | `toolkit-form-cancel-button` |
| Cancel confirm dialog / Discard | `toolkit-form-cancel-confirm-dialog` / `-confirm-button` |

`toolkit-field-*`, `toolkit-type-card-*`, `toolkit-credential-select-*` and
`select-option-*` are **runtime-composed** — a literal grep on `origin/main` returns
nothing. Verify via the generator (`ToolBaseProperty.jsx`, `CategoryItemCard.jsx`,
`CredentialsSelect.jsx`) plus the live DOM.

⚠️ **`select-option-…` values contain double quotes.** A `[data-testid="…"]` selector
with that value is a `SyntaxError`. Use single quotes, or the robust form:
`[data-testid^="select-option-"][data-testid*='"elitea_title":"<title>"']`.

### Schema fields seen per type (localhost, 2026-09-10)

| type | fields (`*` = required) |
|---|---|
| github | `repository`*, `active_branch` (default `main`), `base_branch` (default `main`) |
| jira | none |
| confluence | `space_key`*, `limit` (5), `labels`, `max_pages` (10), `number_of_retries` (2), `min_retry_seconds` (10), `max_retry_seconds` (60) |

Every credential-bearing form also renders a **second** credential select,
`toolkit-credential-select-pgvector` (section `vectorstorage`), plus an Embedding Model
select. `page.locator('[role="combobox"]').first` can land on the wrong one.

### Save-button semantics (the trap this surface is famous for)

`CreateToolkitToolTabBar.jsx`:

```js
shouldDisableSave = isLoading || !formik.dirty      // validity is NOT part of it (//@todo in source)
<DiscardButton title="Cancel" disabled={isLoading}/>  // Cancel: isLoading only
```

Measured live:

| state | Save | Cancel |
|---|---|---|
| form just rendered, nothing dirty | DISABLED | enabled |
| credential auto-selected, Name + required fields still empty | **enabled** | enabled |
| Save clicked while invalid — **no request fires** | enabled | enabled |
| create POST in flight | DISABLED | DISABLED |

- **`to_be_enabled()` is not a validity oracle here** (it is on the credential form).
- **Both buttons greyed ⟺ `isLoading` ⟺ a save is in flight.** This is the discriminator
  for triaging a "form filled, Save greyed" screenshot.

### Credential auto-selection

The form auto-selects the **newest** saved credential of the type
(`configurations?…sort_by=created_at&sort_order=desc` → `savedCredentialsMenuData[0]`),
~0.8–1.0 s after the form renders. No interaction needed.

⚠️ **KNOWN DEFECT [#2158](https://github.com/EliteaAI/elitea-testing-public/issues/2158):
clicking the option that is ALREADY selected toggles the credential off in form state,
while the select keeps displaying it and the option keeps `aria-selected="true"`. No
error is shown, Save stays enabled, and clicking it fires no request at all.** Assert
which credential is selected; only interact with the dropdown when it is the wrong one.

### Saving — waits

```
POST /api/v2/elitea_core/tools/prompt_lib/{project_id}  -> 201  (body.id = new toolkit id)
navigate to  /toolkits/all/{id}    then  /toolkits/all/{id}?name=<url-encoded name>
```

- **`wait_for_load_state("networkidle")` is useless on this app** — measured **0.05 s**
  (a persistent `/socket.io/` poll; see `.agents/testing.md` #1847). It is not a save
  signal, and pairing it with `wait_for_timeout(3000)` is a hard 3-second budget for a
  backend POST — the root cause of #2123's false RED.
- Wait on `page.expect_response(POST …/tools/prompt_lib/… )` and/or
  `wait_for_url(re.compile(r"/toolkits/all/\d+(\?.*)?$"))`. Regexes must tolerate the
  `?name=` query the app appends a beat later.
- `ToolkitCreationPage.save_creation()` already does click + `wait_for_url("**/toolkits/all/*")`
  and returns the parsed id.
- A `GET /elitea_core/toolkit_validator/prompt_lib/{project}/{id}` fires **after**
  navigation and has been seen returning both 200 and 400 on localhost — it is not part
  of the create observable.

## API notes

- `ToolkitAPI.list_toolkits()` returns **one page**. Use `list_all_toolkits()` when
  looking for a just-created toolkit — the single-page variant silently misses it on
  busy projects.
- Credentials for the parameterized specs are created through
  `toolkit_factories.CREDENTIAL_FACTORIES`; `CredentialAPI(browser_cookies=[])` falls
  back to the `ELITEA_API_TOKEN` bearer, which works fine for out-of-band setup.

## Project / environment

- `ELITEA_PROJECT_ID=399` is the test user's **personal ("Private")** project; 471 is
  "Elitea Testing Team", 400 "UI Testing". The picker options carry
  `select-option-{id}` testids on `project-selector-trigger-combobox`.
- Navigating to a project-scoped URL (`/399/toolkits/create/github`) redirects to the
  unscoped path and can leave the selected project changed — prefer the project
  selector.
