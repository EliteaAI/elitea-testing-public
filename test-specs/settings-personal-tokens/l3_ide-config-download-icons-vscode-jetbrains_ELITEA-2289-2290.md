# Test Case (family): IDE download icons generate a downloadable configuration file

## Metadata
- **TMS IDs**: **ELITEA-2289** (VSCode) · **ELITEA-2290** (JetBrains) — one family AFS
- **Source cases**: `.agents/automation/settings-w04/cases/ELITEA-2289.md`,
  `.agents/automation/settings-w04/cases/ELITEA-2290.md` (intake snapshots)
- **Priority**: l3 (both frontmatters `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session
  (ELITEA-2285/2289/2290/2291), 2026-08-27
- **Status**: **ready-for-automation** (ELITEA-2289 carries one sanctioned soft-assert —
  see § Known Defects; ELITEA-2290 asserts hard throughout)
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: **#1884** — the VSCode download embeds the **masked** token
  (`eliteacode.authToken: "...XXXXXXX"`), so the generated `settings.json` cannot
  authenticate.
- **Testid work**: **NONE.** Every handle below is already on `EliteaAI/EliteaUI` `main`.
- **Family shape**: both cases run the identical 4 steps against the identical row and
  differ **only in data** — which icon is clicked, the resulting filename/MIME, and the
  content grammar. Downstream this is ONE parameterized spec (`@pytest.mark.parametrize`)
  with the § Parameter table below as its param set.

## Why this is NOT already covered

`tests/ui/admin/test_personal_tokens_page_layout.py` (ELITEA-2277, merged to
`origin/automation/base`) asserts only that `token-action-vscode-button` and
`token-action-jetbrains-button` are **present** on a row (`EXPECTED_ACTION_ICONS`,
lines 28-31). Neither icon is clicked anywhere in the merged suite, and no spec captures
an IDE-config download. Fresh implementation.

## Preconditions
- Logged-in user on `/settings/tokens` with the table in its **populated** branch.
- **`showDownload` must be true**, or neither icon renders. It is
  `!!model.configuration_uid && selectedProjectId !== PUBLIC_PROJECT_ID`
  (`PersonalTokens.jsx:267`) — a page-level boolean, not per-row. True on project 399.
- **The test creates its own token** (see § Test Data). ELITEA-2289 needs the *real*
  token value as its oracle, and the only place the product ever reveals it is the
  "New token generated!" dialog — a pre-existing row's real token is unknowable.

## Test Data

- One token created via the real UI create flow — `PersonalTokensPage.click_add_button()`
  → `CreatePersonalTokenPage.fill_name(...)` → `click_generate()`, and **capture the full
  token string from `generated-token-dialog-token-value` before closing the dialog** —
  then `close_dialog()`. Same shape as merged ELITEA-2280.
- Name: `autotest-token-{uuid4().hex[:8]}`. A unique name is load-bearing — ELITEA-2288
  proved duplicate names are legal, so a literal name can match more than one row.
- Observed live: the dialog value is a **226-char JWT** beginning `eyJhbGciOiJI`.
- **`finally:` cleanup deletes the token** (`token-action-delete-button` → type the exact
  name → `delete-confirm-button`), so no row leaks into shared data.

## The product's actual download contract (source + live confirmed)

Both icons call the **same** handler, `onIdeSettingsDownload(token, ide)`
(`PersonalTokens.jsx:192-241`), wired per-row in `TokensTable.jsx:140-141` as
`onDownload(row?.token || '')` (JetBrains) and `onVsCodeDownload(row?.token || '')`
(VSCode). It builds the content as a string, wraps it in a `Blob`, and clicks a
synthesized `<a download>` — a **pure client-side blob download, no network request**.
Playwright's `page.expect_download()` captures it normally (verified live: the MCP
browser reported `Downloading file settings.json` / `elitea.xml`).

### ⚠️ The masked-token trap — read before writing ELITEA-2289's assertion

`GET /api/v2/auth/token/` returns each token's `token` field **already masked**. That is
precisely why `TokensTable.jsx:119` can render the display mask as
`'...' + row.token.substring(row.token.length - 4)`. Verified live end-to-end: for a token
whose real value ends `…7FrjdGrGvQ`, `row.token` was `"...jdGrGvQ"` and the table cell
showed `"...rGvQ"` — a mask of a mask.

`onIdeSettingsDownload` passes that same `row.token` straight into
`eliteacode.authToken` / `eliteacode.LLMAuthToken`. So the downloaded `settings.json`
contains a masked, non-functional token (**#1884**).

**Do not "fix" this by asserting the masked value.** ELITEA-2289's own expected result is
*"valid configuration content referencing the correct token"*; asserting `authToken ==
"..." + token[-4:]` would encode the bug as the contract and go green forever. The
assertion asserts the **correct** behaviour — `authToken == the full token captured from
the generation dialog` — with `expect.soft()` + `# Known defect: #1884`.

### Live observations (2026-08-27, real clicks on the `for_ui_tests` row)

`settings.json` — 601 bytes:

```json
{
  "eliteacode.providerServerURL": "https://dev.elitea.ai",
  "eliteacode.LLMServerUrl": "https://dev.elitea.ai",
  "eliteacode.modelName": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "eliteacode.LLMModelName": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "eliteacode.authToken": "...TX2UWzA",
  "eliteacode.LLMAuthToken": "...TX2UWzA",
  "eliteacode.projectId": 399,
  "eliteacode.integrationUid": "1_eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "eliteacode.defaultViewMode": "split",
  "eliteacode.verifySsl": false,
  "eliteacode.displayType": "split",
  "eliteacode.debug": false
}
```

`elitea.xml` — 631 bytes:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="EliteASettings">
    <option name="displayType" value="SPLIT" />
    <option name="integrationName" value="Project 1" /> 
    <option name="integrationUid" value="1_eu.anthropic.claude-sonnet-4-5-20250929-v1:0" />
    <option name="llmCustomModelEnabled" value="true" /> 
    <option name="llmCustomModelName" value="eu.anthropic.claude-sonnet-4-5-20250929-v1:0" />
    <option name="llmServerUrl" value="https://dev.elitea.ai" />
    <option name="projectId" value="399" />
    <option name="provider" value="ELITEA_EYE" />
  </component>
</project>
```

Note the XML carries **no token field at all**, by design (`getJetBrainsSettings` never
receives one) — so ELITEA-2290 is entirely unaffected by #1884 and asserts hard.

Console across both downloads: **0 errors produced by the flow**.

## Parameter table (one row per TMS case — the spec's param set)

| Param | **ELITEA-2289 — VSCode** | **ELITEA-2290 — JetBrains** |
|---|---|---|
| `case_id` | `ELITEA-2289` | `ELITEA-2290` |
| Icon testid | `token-action-vscode-button` | `token-action-jetbrains-button` |
| Icon colour (case text) | blue | red |
| `suggested_filename` | `settings.json` | `elitea.xml` |
| Blob MIME | `application/json` | `application/xml` |
| Grammar | JSON — parse with `json.loads` | XML — parse with `xml.etree.ElementTree.fromstring` |
| Structural assertion | all 12 `eliteacode.*` keys present | root `<project version="4">` containing `<component name="EliteASettings">` with 8 `<option>` children |
| Server-URL field | `eliteacode.providerServerURL` **and** `eliteacode.LLMServerUrl` | `llmServerUrl` |
| Project-id field | `eliteacode.projectId` (int) | `projectId` (string) |
| Model-name field | `eliteacode.modelName` **and** `eliteacode.LLMModelName` | `llmCustomModelName` |
| Integration-uid field | `eliteacode.integrationUid` | `integrationUid` |
| Fixed-value fields | `defaultViewMode`/`displayType` == `split`, `verifySsl` is `False`, `debug` is `False` | `displayType` == `SPLIT`, `llmCustomModelEnabled` == `true`, `provider` == `ELITEA_EYE` |
| Token field | `eliteacode.authToken` == `eliteacode.LLMAuthToken` == **the full token** — **SOFT, `# Known defect: #1884`** | *(none — the format carries no token; assert the full token appears **nowhere** in the file)* |

## Test Steps (identical for both cases; substitute from the Parameter table)

0. **Setup (not a case step — its own allure.step "Setup").** Create one token via the UI
   create flow; **capture the full token value from `generated-token-dialog-token-value`**;
   close the dialog. Assert `get_row_by_name(token_name)` has count 1.
   - **Verify (guard)**: the captured token is a non-empty string of length > 100 — it
     must be the real JWT, not a mask. If the product ever stopped showing the full value
     in the dialog, every assertion below would silently become vacuous.

1. **Step 1 — Navigate to Settings → Personal Tokens with at least one token.**
   `PersonalTokensPage.navigate()`.
   - **Verify**: `personal-tokens-page-title` text == `Personal Tokens`.
   - **Verify**: `token_row` count >= 1 and the created row is present.
   - **Verify (precondition guard)**: the row exposes the parameterized icon testid —
     i.e. `showDownload` is true. Absent ⇒ fail loudly with that reason, never skip.

2. **Step 2 — Click the parameterized icon in the Actions column of the token row.**
   Wrap in `with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:` around
   `get_row_action_icon(row, ICON_TESTID).click()` — same shape as the merged
   `PipelineDetailPage.export_pipeline_via_menu_and_download`
   (`automation/pages/pipeline_detail_page.py:2437`).

3. **Step 3 — Verify a file is downloaded.**
   - **Verify**: `download.suggested_filename == EXPECTED_FILENAME`.
   - **Verify**: the saved file exists and its byte length is **> 0** (the case's "not
     empty"; observed 601 / 631 bytes).

4. **Step 4 — Verify the file is not empty and contains valid configuration content
   referencing the correct token and server URL.**
   Read the file text and parse it with the grammar for this param.
   - **Verify (hard)**: it parses — `json.loads` / `ET.fromstring` succeeds. A substring
     check would pass on a truncated or malformed file; parsing is what "valid" means.
   - **Verify (hard)**: the structural assertion for this param (all 12 keys / the
     `EliteASettings` component with its 8 options).
   - **Verify (hard)**: the **server URL** field(s) equal the config-derived origin —
     `urlparse(settings.elitea_api_base)` → `f"{scheme}://{netloc}"` (observed
     `https://dev.elitea.ai`). ELITEA-2289 asserts both URL keys and that they are equal.
   - **Verify (hard)**: the project-id field equals `settings.elitea_project_id`
     (compare as `str` for JetBrains, as `int` for VSCode).
   - **Verify (hard)**: model-name field(s) non-empty; for VSCode, the two model keys are
     equal. Integration-uid field non-empty.
   - **Verify (hard)**: the fixed-value fields for this param hold their expected literals.
   - **ELITEA-2289 only — Verify (SOFT, `# Known defect: #1884`)**:
     `eliteacode.authToken == eliteacode.LLMAuthToken == <the full token captured in Setup>`.
     This is the case's own "referencing the correct token" and is the **correct** expected
     behaviour; it currently reads the masked form.
   - **ELITEA-2290 only — Verify (hard)**: the full token string does **not** appear
     anywhere in `elitea.xml`. The JetBrains format legitimately carries no credential;
     pinning that is what keeps a future "helpful" change from leaking one.

5. **Axis 2 — No console errors** across the flow
   (`utils/console_errors.collect_console_errors`). 0 produced live.

## Handles Reference

| Element | Handle (testid) | Page-object member | PROVENANCE |
|---|---|---|---|
| Token row (repeatable) | `token-row` | `PersonalTokensPage.token_row` | on-main ✓ |
| Row name cell | `token-name-cell` | `TOKEN_NAME_CELL_SELECTOR` / `get_row_name_cell()` | on-main ✓ |
| Row VSCode icon (ELITEA-2289) | `token-action-vscode-button` | `get_row_action_icon(row, ...)` | on-main ✓ |
| Row JetBrains icon (ELITEA-2290) | `token-action-jetbrains-button` | `get_row_action_icon(row, ...)` | on-main ✓ |
| Row delete icon (cleanup) | `token-action-delete-button` | `get_row_action_icon(row, ...)` | on-main ✓ |
| Page title | `personal-tokens-page-title` | `page_title` | on-main ✓ |
| Add (+) button | `personal-tokens-add-button` | `add_button` / `click_add_button()` | on-main ✓ |
| Create-form name input | `create-personal-token-name-input` | `CreatePersonalTokenPage.name_input` | on-main ✓ |
| Generate button | `create-personal-token-generate-button` | `generate_button` / `click_generate()` | on-main ✓ |
| Generated-dialog token value | `generated-token-dialog-token-value` | `dialog_token_value` / `get_dialog_token_value_text()` | on-main ✓ |
| Generated-dialog close (X) | `generated-token-dialog-close-button` | `dialog_close_button` / `close_dialog()` | on-main ✓ |
| Delete dialog name field | `delete-confirm-name-input` | `delete_confirm_name_input` | on-main ✓ |
| Delete dialog confirm | `delete-confirm-button` | `delete_confirm_button` / `confirm_delete()` | on-main ✓ |

Provenance verified 2026-08-27 with `cd ../EliteaUI && git fetch origin` + the two-stage
`git grep` from `.agents/workflow.md` § Closure record against **both** `origin/main` and
`origin/automation/testids` — full output pasted in the ELITEA-2291 AFS's
§ Handles Reference. **`main:YES testids:YES` on every row above; no testid work.**

## Automation Hints

- Target file: a **new** `automation/tests/ui/admin/test_personal_token_ide_config_download.py`
  with ONE parameterized test over the § Parameter table. `pytest.param(..., id="vscode")`
  / `id="jetbrains"`, and put the TMS id in the param id so a failure names its case.
- Page object: **no new fields needed** — `get_row_action_icon(row, testid)` already
  covers both icons. A thin `download_ide_settings(row, icon_testid, timeout)` helper on
  `PersonalTokensPage` wrapping `expect_download` is optional and welcome; if added, the
  icon testid stays a **parameter**, not a new hardcoded locator.
- Markers: `ui`, `admin`, `p2`, `regression`.
- Every step wrapped in `with allure.step("Step N — …"):`; Setup and the `finally:`
  cleanup follow ELITEA-2280's existing shape.
- **Read the download via `download.path()`** (Playwright's temp copy) or
  `download.save_as(tmp_path / name)`; do not assume a fixed download directory.
- **No network wait exists for this action** — the download is a client-side Blob, no
  request fires. `expect_download` IS the wait. Never add a sleep.
- `DOWNLOAD_TIMEOUT`: reuse the artifacts specs' constant shape (they already do exactly
  this — `tests/ui/artifacts/test_artifacts_download_all_files_select_all_zip.py:332`).
- **No substitution anywhere.** The file under assertion is produced by the product from
  real session state, and the token oracle comes from the product's own dialog — do not
  hand-write an expected payload, and do not `route.fulfill` the token list.

## Coverage Map

### Axis 1 — every element of the TMS cases

| Case element | Case | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Precondition: user logged in | both | — | `auth_state` | fixture | covered |
| Step 1 — Navigate to Settings → Personal Tokens with at least one token | both | Page loads | Step 1 | `navigate()` + title + row present + icon precondition guard | covered |
| Step 2 — Click the VSCode (blue) icon in the Actions column | 2289 | Control responds | Step 2 | click inside `expect_download` | covered |
| Step 2 — Click the JetBrains (red) icon in the Actions column | 2290 | Control responds | Step 2 | click inside `expect_download` | covered |
| Step 3 — Verify a file is downloaded | both | Condition holds | Step 3 | `suggested_filename` + file exists | covered |
| Step 4 — File is not empty | both | Condition holds | Step 3/4 | byte length > 0 | covered |
| Step 4 — Contains valid configuration content | both | Condition holds | Step 4 | parses + full structural key/option assertion + fixed-value literals | covered |
| Step 4 — …referencing the correct **token** | 2289 | Condition holds | Step 4 | `authToken == LLMAuthToken == full token` — **SOFT, #1884** | **covered — soft-asserted against open defect #1884** |
| Step 4 — …referencing the correct **server URL** | 2289 | Condition holds | Step 4 | both URL keys == config-derived origin, and equal to each other | covered |
| Expected Final State — file not empty + valid content (+ token/server URL for 2289) | both | — | Step 4 | same | covered |
| Icon **colour** (blue / red) in the case text | both | — | — | not asserted | **out-of-scope** — colour is the icon SVG's own artwork, not a state the product computes; the testid identifies the control unambiguously. Asserting a fill would test the asset, not the behaviour. |

### Axis 2 — observables asserted BEYOND the cases

| Extra observable | Why it is grounded |
|---|---|
| The file **parses** as JSON / XML (not a substring match) | The cases say "valid configuration content"; substring checks pass on truncated or malformed output, which is the realistic failure mode of a string-concatenated XML template. |
| `projectId` == `settings.elitea_project_id` | "Valid content" is meaningless if the config points at another project. Config is an independent oracle, not a second read of the same DOM. |
| Fixed-value fields (`provider == ELITEA_EYE`, `displayType`, `verifySsl`, `debug`) | These are the constants an IDE plugin actually keys off; they are exactly what a careless template edit breaks, and nothing else in the suite covers them. |
| VSCode's duplicate key pairs are equal (`providerServerURL`/`LLMServerUrl`, `modelName`/`LLMModelName`, `authToken`/`LLMAuthToken`) | The object deliberately writes each value under a legacy and a current key; a regression populating only one is invisible to per-key checks. |
| ELITEA-2290: the full token appears **nowhere** in `elitea.xml` | The JetBrains format carries no credential by design. Pinning the absence turns "we happened not to include it" into an enforced invariant — the cheap half of the #1884 story. |
| Setup guard: the captured token is > 100 chars | Without it, a product change that masked the generation dialog too would make ELITEA-2289's whole token assertion vacuous while still passing. |
| Icon precondition guard (`showDownload`) | Page-level boolean; a false value removes the icon and would surface as an opaque locator timeout instead of the real cause. |
| No console errors across the flow | Standard side-channel axis. |

## Known Defects

- **#1884 (ELITEA-2289 only, soft-asserted)** — the VSCode IDE settings the product
  generates embed the **masked** token in `eliteacode.authToken` / `LLMAuthToken`, so the
  file cannot authenticate. Root cause: `GET /api/v2/auth/token/` returns `token` already
  masked, and both `onIdeSettingsDownload` (`PersonalTokens.jsx`) and
  `SettingsPreview.getVSCodeSettings` pass it through unchanged. The
  `|| 'Your_Personal_Token'` fallback in `SettingsPreview` shows the UI *intends* a real
  token. Affects the eye-preview panel identically.
  → Step 4's token assertion is `expect.soft` + `# Known defect: #1884`, asserting the
  correct value. Per `.agents/testing.md` § Merge gate the **ELITEA-2289 param** is
  **sanctioned-RED** on that one signature until the fix ships; the JetBrains param stays
  green. Note `expect.soft` failures ARE pytest FAILEDs — the closure record must record
  the exception and the case stays `blocked-on-#1884`, not `automated`.
- **#1885 (context only — NOT asserted here)** — the eye-preview panel's
  `integrationUid` is always `""`. Owned and soft-asserted by the ELITEA-2291 AFS. The
  **row-level** downloads specced here write the real value, so nothing to assert.

## Blocked Steps
None.
