# Test Case: Eye icon opens the IDE configuration preview panel with correct content

## Metadata
- **TMS ID**: ELITEA-2291
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2291.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session
  (ELITEA-2285/2289/2290/2291), 2026-08-27
- **Status**: **ready-for-automation** (with one sanctioned soft-assert — see § Known Defects)
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: **#1885** — Settings Preview reads `model.integration_uid` instead of
  `configuration_uid`, so the previewed VSCode config always shows
  `"eliteacode.integrationUid": ""` while the row-level download writes the real value.
- **Testid work**: **7 new testids in `SettingsPreview.jsx`** — the whole component
  currently has ZERO testids and ZERO accessible names. See § Handles Reference.
- **Classification note (declared, per `.agents/testing.md` § Merge gate → analysis-time
  entry)**: #1885 is deterministic, single-cause and isolable to ONE assertion, and does
  not block any later step of this case. Per that bullet the AFS stays
  `ready-for-automation` and the affected assertion is written as the **correct**
  expected behaviour with `expect.soft()` + `# Known defect: #1885`, so the spec flips
  green when the fix ships. All other steps assert hard.

## Why this is NOT already covered

`tests/ui/admin/test_personal_tokens_page_layout.py` (ELITEA-2277, merged to
`origin/automation/base`) asserts only that the four action icons — including
`token-action-preview-button` — are **present** on a row (its `EXPECTED_ACTION_ICONS`
list, lines 28-31). It never clicks the eye icon. No merged spec opens the Settings
Preview panel, and the panel's component (`SettingsPreview.jsx`) is not referenced
anywhere in `automation/`. Fresh implementation.

## Preconditions
- Logged-in user on `/settings/tokens` with the table in its **populated** branch.
- **`showDownload` must be true**, or the eye icon does not render at all.
  `TokensSection`'s `showDownload` = `!!model.configuration_uid && selectedProjectId !==
  PUBLIC_PROJECT_ID` (`PersonalTokens.jsx:267`) — a single **page-level** boolean, not
  per-row. On project 399 ("Private", a default model resolved) it is `true` and all 5
  live rows show all 4 icons. A test running against the Public project, or against a
  project with zero model configurations, would find only the trash icon.
- **This case is read-only** — it may run against any existing row. Live rows observed
  2026-08-27: `for_ui_tests`, `Levon`, `Marian`, `New`, `uautomate`. Prefer the token
  the test creates itself only if a deterministic title is needed (see Step 3).

## The product's actual preview contract (source + live confirmed)

- Eye icon (`token-action-preview-button`) → `onPreviewSettings(token)`
  (`PersonalTokens.jsx:133-141`): sets `selectedTokenForPreview`, resizes the
  `react-split` panes to `[60, 40]` (or `[35, 65]` on a small window) and sets
  `showSettingsPreview = true`. **It is an in-page split pane, not a route change and
  not a modal** — the URL stays `/settings/tokens` and the token table stays mounted
  and interactive beside it.
- The panel is `src/[fsd]/features/settings/ui/personal-tokes/SettingsPreview.jsx`:
  header = close IconButton + title Typography + `SingleSelect` (IDE) + copy IconButton
  + download IconButton; body = a read-only `Field.CodeMirrorEditor`.
- **Title** = `` `${tokenName} • ${ideLabel} Settings` `` (`canvasTitle`, note the
  U+2022 BULLET with a space either side). `ideLabel` comes from
  `TokensConstants.SETTINGS_PREVIEW_LABELS` — `VSCode` / `JetBrains`
  (`src/[fsd]/features/settings/lib/constants/tokens.constants.js`). Default selected
  IDE is `VSCODE`, so the panel always opens on `… • VSCode Settings`.
- **Body** for VSCode = `JSON.stringify(..., null, 2)` of a fixed 12-key object;
  the editor language is `json`. Switching the IDE dropdown to JetBrains re-renders the
  body as XML (`elitea.xml` shape) and retitles to `… • JetBrains Settings`.
- **Close** = the header's first IconButton → `onCloseSettingsPreview`: sets sizes
  `[100, 0]` then, after a **50 ms `setTimeout`**, unmounts the panel
  (`PersonalTokens.jsx:143-149`). So the close is *animated then unmounted* — assert on
  the panel's disappearance with an auto-retrying expectation, never on an immediate read.

### Live observations (2026-08-27, real clicks on `for_ui_tests`)

| Moment | Observed |
|---|---|
| Eye icon clicked | URL unchanged (`/settings/tokens`); table still 5 rows; `react-split` gutter appears (`.gutter` count 0 → 1) |
| Panel title | `for_ui_tests • VSCode Settings` |
| IDE select | a `[role="combobox"]` whose text is `VSCode` |
| Header buttons | exactly **3** `<button>` elements — close, copy, download — **all with `aria-label` = null, `data-testid` = null** (this is why the testid work below is mandatory) |
| Body (VSCode) | valid JSON, 12 keys, 555 chars — see the block below |
| `undefined` / `null` literals in body | **none** (regex `/:\s*(undefined\|null)\b\|"undefined"/` → no match) |
| `eliteacode.integrationUid` | **`""`** — empty, while the row download writes `1_eu.anthropic.claude-sonnet-4-5-20250929-v1:0` (**defect #1885**) |
| `eliteacode.authToken` | `...TX2UWzA` — the masked token, not a usable one (**defect #1884**, owned by the ELITEA-2289 AFS) |
| Close clicked | `.cm-content` gone, title gone, `.gutter` count 1 → 0, table still 5 rows |

Body observed verbatim (`for_ui_tests`):

```json
{
  "eliteacode.providerServerURL": "https://dev.elitea.ai",
  "eliteacode.LLMServerUrl": "https://dev.elitea.ai",
  "eliteacode.modelName": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "eliteacode.LLMModelName": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "eliteacode.authToken": "...TX2UWzA",
  "eliteacode.LLMAuthToken": "...TX2UWzA",
  "eliteacode.projectId": 399,
  "eliteacode.integrationUid": "",
  "eliteacode.defaultViewMode": "split",
  "eliteacode.verifySsl": false,
  "eliteacode.displayType": "split",
  "eliteacode.debug": false
}
```

## Test Steps

1. **Step 1 — Navigate to Settings → Personal Tokens (with at least one token).**
   `PersonalTokensPage.navigate()` (already waits for the token-list GET **and** the
   first `token-row`, so the populated branch is proven, not assumed).
   - **Verify**: `personal-tokens-page-title` text == `Personal Tokens`.
   - **Verify**: `token_row` count >= 1.
   - **Verify (precondition guard, not a case step)**: the first row exposes
     `token-action-preview-button` — i.e. `showDownload` is true. If it is absent the
     test is running in the `showDownload == false` branch and must fail loudly with
     that message, never skip silently.

2. **Step 2 — Click the eye icon in a token row's Actions column.**
   Capture the row's name first (`get_row_name_cell(row).text_content()`) — Step 3's
   expected title is built from it, never hardcoded.
   `get_row_action_icon(row, "token-action-preview-button").click()`.
   - **Verify**: `token-settings-preview-panel` becomes visible.
   - **Verify**: `page.url` still ends `/settings/tokens` (it is a pane, not a route).

3. **Step 3 — Verify the side panel's title is `[token name] • VSCode Settings`.**
   - **Verify**: `token-settings-preview-title` text == `f"{row_name} • VSCode Settings"`.
     Build the expected string from the captured `row_name`; the separator is
     **U+2022 BULLET surrounded by single spaces**.

4. **Step 4 — Verify an IDE type dropdown is shown in the panel header.**
   - **Verify**: `token-settings-preview-ide-select-combobox` is visible.
   - **Verify**: its text == `VSCode` (the default selection).

5. **Step 5 — Verify a copy icon button and a download icon button are present in the header.**
   - **Verify**: `token-settings-preview-copy-button` is visible **and enabled**.
   - **Verify**: `token-settings-preview-download-button` is visible **and enabled**.

6. **Step 6 — Verify the panel shows a JSON configuration.**
   Read the body with **`inner_text()`**, not `text_content()` — see § Automation Hints.
   - **Verify**: `json.loads(body)` succeeds (this *is* the "shows a JSON configuration"
     assertion — a substring check would pass on malformed JSON).
   - **Verify**: the parsed object contains all 12 expected keys, exactly:
     `eliteacode.providerServerURL`, `eliteacode.LLMServerUrl`, `eliteacode.modelName`,
     `eliteacode.LLMModelName`, `eliteacode.authToken`, `eliteacode.LLMAuthToken`,
     `eliteacode.projectId`, `eliteacode.integrationUid`, `eliteacode.defaultViewMode`,
     `eliteacode.verifySsl`, `eliteacode.displayType`, `eliteacode.debug`.
   - **Verify**: `parsed["eliteacode.projectId"] == settings.elitea_project_id`.
   - **Verify**: `parsed["eliteacode.providerServerURL"]` == the config-derived server
     origin (`urlparse(settings.elitea_api_base)` → `scheme://netloc`) and equals
     `parsed["eliteacode.LLMServerUrl"]`.

7. **Step 7 — Verify no field shows `undefined` or a null value unexpectedly.**
   - **Verify (hard)**: no value in the parsed object is `None`, and the literal token
     `undefined` appears nowhere in the raw body text.
   - **Verify (hard)**: `parsed["eliteacode.modelName"]` is a non-empty string and
     equals `parsed["eliteacode.LLMModelName"]`.
   - **Verify (SOFT — `# Known defect: #1885`)**:
     `expect.soft` that `parsed["eliteacode.integrationUid"]` is a **non-empty** string.
     This is the correct expected behaviour: the row-level VSCode download writes the
     real `configuration_uid` for the same token/project/model, and the preview claims
     to show the same config. It currently reads `""` because `SettingsPreview.jsx`
     dereferences `modelData.integration_uid` while the model object carries
     `configuration_uid`. Assert the correct value, not the buggy one.

8. **Step 8 — Close the panel and verify it closes cleanly.**
   `token-settings-preview-close-button` click.
   - **Verify**: `token-settings-preview-panel` is **not visible** — use an
     auto-retrying `expect(...).to_have_count(0)` / `not_to_be_visible()`; the unmount
     is behind a 50 ms `setTimeout` after the pane animation.
   - **Verify**: `token-settings-preview-content` has count **0** (the CodeMirror editor
     really unmounted — the panel is not merely width-zero).
   - **Verify**: the token table is still intact and interactive — `token_row` count
     equals the count captured in Step 1 and the same row's `token-name-cell` still
     reads `row_name`.

9. **Axis 2 — No console errors** across the whole flow
   (`utils/console_errors.collect_console_errors`). 0 produced by this flow live.

## Handles Reference

**Every handle below is a `data-testid`.** `SettingsPreview.jsx` currently exposes NO
testid and NO accessible name on any of its 3 header buttons (confirmed live — all three
returned `aria-label: null`, `data-testid: null`), so there is no honest non-testid
handle here and none is permitted (`.agents/testing.md` § Locator policy).

| Element | Handle (testid) | Page-object member | PROVENANCE |
|---|---|---|---|
| Token row (repeatable) | `token-row` | `PersonalTokensPage.token_row` | on-main ✓ |
| Row name cell | `token-name-cell` | `TOKEN_NAME_CELL_SELECTOR` / `get_row_name_cell()` | on-main ✓ |
| Row eye (preview) icon | `token-action-preview-button` | `get_row_action_icon(row, ...)` | on-main ✓ |
| Page title | `personal-tokens-page-title` | `page_title` | on-main ✓ |
| Preview panel root | `token-settings-preview-panel` | **new** `LocatorDescriptor` | **added — EliteaAI/EliteaUI@efda0603** |
| Preview panel title | `token-settings-preview-title` | **new** `LocatorDescriptor` | **added — EliteaAI/EliteaUI@efda0603** |
| Preview close (X) button | `token-settings-preview-close-button` | **new** `LocatorDescriptor` | **added — EliteaAI/EliteaUI@efda0603** |
| Preview IDE select | `token-settings-preview-ide-select-combobox` | **new** `LocatorDescriptor` | **added — EliteaAI/EliteaUI@efda0603** |
| Preview copy button | `token-settings-preview-copy-button` | **new** `LocatorDescriptor` | **added — EliteaAI/EliteaUI@efda0603** |
| Preview download button | `token-settings-preview-download-button` | **new** `LocatorDescriptor` | **added — EliteaAI/EliteaUI@efda0603** |
| Preview body (CodeMirror content) | `token-settings-preview-content` | **new** `LocatorDescriptor` | **added — EliteaAI/EliteaUI@efda0603** |

Provenance verified 2026-08-27 with `cd ../EliteaUI && git fetch origin` followed by the
two-stage `git grep` from `.agents/workflow.md` § Closure record against **both**
`origin/main` and `origin/automation/testids`:

```
token-action-preview-button              main:YES  testids:YES
token-action-vscode-button               main:YES  testids:YES
token-action-jetbrains-button            main:YES  testids:YES
token-value-cell                         main:YES  testids:YES
token-name-cell                          main:YES  testids:YES
token-row                                main:YES  testids:YES
generated-token-dialog-token-value       main:YES  testids:YES
generated-token-dialog-copy-button       main:YES  testids:YES
generated-token-dialog-close-button      main:YES  testids:YES
personal-tokens-add-button               main:YES  testids:YES
token-settings-preview-panel             main:no   testids:no
token-settings-preview-content           main:no   testids:no
```

> **Amended at implementation time (test-automation-engineer, 2026-08-27).** All seven
> testids were added exactly as specced below and are live on
> `EliteaAI/EliteaUI` `automation/testids` as EliteaAI/EliteaUI@efda0603 (the dev server
> serves them; a human cherry-picks to `main`). The PROVENANCE column above now reads
> `added` rather than `needs-adding`; the `main:no testids:no` block is the
> analysis-time snapshot and is kept as the record of why the work was needed.

### Testid work — all SEVEN are pure call-site additions in `SettingsPreview.jsx`

No shared component needs a source change. Verified mechanisms:

| Target | How |
|---|---|
| root `Box` → `token-settings-preview-panel` | MUI `Box` spreads unknown props onto the DOM node — plain `data-testid=` at the call site |
| title `Typography` → `token-settings-preview-title` | same spread mechanism |
| close / copy / download `IconButton`s | same spread mechanism, one `data-testid=` each |
| `SingleSelect` → `token-settings-preview-ide-select` | `SingleSelect` **already accepts** a `data-testid` prop and wires `SelectDisplayProps={{'data-testid': \`${dataTestId}-combobox\`}}` (`src/[fsd]/shared/ui/select/SingleSelect.jsx:661-662`). Pass `data-testid="token-settings-preview-ide-select"`; the **combobox** node then carries `token-settings-preview-ide-select-combobox` — that suffixed form is what the locator uses (same shape as the merged `create-personal-token-expiration-measure-select-combobox`) |
| `Field.CodeMirrorEditor` → `token-settings-preview-content` | `CodeMirrorEditor` **already accepts** `contentTestId` and applies it straight onto the `.cm-content` node via `EditorView.contentAttributes` (`src/[fsd]/shared/ui/field/CodeMirrorEditor.jsx:83,276-283,331`). Pass `contentTestId="token-settings-preview-content"` — exactly the merged `toolkit-raw-json-editor-content` precedent (`ToolCustom.jsx:218`). **No `#579` raw-handle exception is needed or permitted here** |

All seven are on elements this test actually calls on its executed path (canon ruling
#511) — nothing blanket-added.

## Automation Hints

- Target file: a **new** `automation/tests/ui/admin/test_personal_token_settings_preview.py`
  (the ELITEA-2289/2290 family AFS is a separate spec file; nothing is shared but the
  page object).
- Page object: extend **`automation/pages/personal_tokens_page.py`** with the 7 new
  class-level `LocatorDescriptor` fields plus a small `open_settings_preview(row)` /
  `close_settings_preview()` pair. Locators are class fields only — no inline
  `get_by_test_id`, no `fallback=`.
- Markers: `ui`, `admin`, `p2`, `regression` (match `test_personal_tokens_page_layout.py`).
- Every step wrapped in `with allure.step("Step N — …"):`.
- **Read the editor body with `inner_text()`, NOT `text_content()`.** CodeMirror renders
  each line as its own `<div>`; `text_content()` concatenates them with no separator and
  the result will not parse as JSON. `inner_text()` preserved the newlines correctly live.
  The document is 13 lines, well under CodeMirror's virtualization threshold, so the whole
  body is in the DOM.
- **Never `sleep`.** The close is behind a 50 ms `setTimeout` — use
  `expect(panel).not_to_be_visible()` / `to_have_count(0)`, which auto-retries.
- Do **not** read the clipboard in this spec (Step 5 only asserts the copy button is
  present). If a future case does, note the digest's clipboard-read hang gotcha — the
  pytest `context` fixture grants `clipboard-read`/`-write` (`conftest.py:279`), ad-hoc
  browser sessions do not and will hang forever.
- **Do not add a `page.route()`/`evaluate()` substitution anywhere.** Every value this
  case asserts is produced live by the app from real session state; nothing here is hard
  to reach.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` (localhost `VITE_DEV_TOKEN`) | fixture | covered |
| Step 1 — Navigate to Settings → Personal Tokens with at least one token | Page loads | Step 1 | `navigate()` + title + `token_row >= 1` + eye-icon precondition guard | covered |
| Step 2 — Click the eye icon in a row's Actions column | Control responds; expected next state | Step 2 | click + panel visible + URL unchanged | covered |
| Step 3 — Side panel titled `[token name] • VSCode Settings` | Condition holds | Step 3 | title text == built-from-row-name string | covered |
| Step 4 — IDE type dropdown shown in the panel header | Condition holds | Step 4 | combobox visible + text == `VSCode` | covered |
| Step 5 — Copy icon button and download icon button present in the header | Condition holds | Step 5 | both visible + enabled | covered |
| Step 6 — Panel shows a JSON configuration | Condition holds | Step 6 | `json.loads()` parses + 12 expected keys + projectId/serverURL match config | covered |
| Step 7 — No field shows `undefined` or null unexpectedly | Condition holds | Step 7 | hard: no `None` values, no literal `undefined`, modelName non-empty **·** soft: `integrationUid` non-empty | **covered — one assertion soft-asserted against open defect #1885** |
| Step 8 — Close the panel; it closes cleanly | Action completes, expected UI state | Step 8 | panel not visible + editor count 0 + table intact | covered |
| Expected Final State — panel closes cleanly | — | Step 8 | same | covered |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it is grounded |
|---|---|
| URL still `/settings/tokens` after the eye click | The case calls it a "side panel"; the merged suite has no other assertion distinguishing a pane from a route/modal. Without it the test would pass if the product regressed to navigating away. |
| `eliteacode.projectId == settings.elitea_project_id` and the server URL matches the configured API host | Step 6 says "shows a JSON configuration" — parsing alone would pass on a config for the *wrong* project or server. These pin that the preview reflects the live session, and use config as an independent oracle rather than re-reading the DOM. |
| `providerServerURL == LLMServerUrl`, `modelName == LLMModelName` | The object deliberately duplicates each value into a legacy and a current key; a regression that populates only one is invisible to any per-key check. |
| `token-settings-preview-content` count 0 after close | Step 8's "closes cleanly" is satisfiable by a width-0 pane that never unmounted. Asserting the editor is gone is what makes "cleanly" mean something. |
| Table row count unchanged and row still readable after close | Guards the react-split restore — the pane manipulates the table's own container sizes, so a bad close could leave the table collapsed. |
| No console errors across the flow | Standard side-channel axis (skill § Execute step 3). |
| Eye-icon precondition guard in Step 1 | `showDownload` is a page-level boolean; without the guard, a false value silently removes the icon and the test fails with an opaque locator timeout instead of the real reason. |

## Known Defects

- **#1885 (this case's own, soft-asserted)** — Settings Preview reads
  `modelData.integration_uid` where the model object carries `configuration_uid`, so the
  previewed VSCode config always shows `"eliteacode.integrationUid": ""` while the
  row-level download writes `1_eu.anthropic.claude-sonnet-4-5-20250929-v1:0` for the same
  token. `|| ''` swallows the `undefined`, which is why nothing shows in the console.
  The JetBrains branch of the same file has the identical mismatch on `integration_uid`
  **and** `integration_name` — out of this case's scope (it never switches the dropdown),
  recorded in the issue.
  → Step 7's `integrationUid` assertion is `expect.soft` + `# Known defect: #1885`.
  Per `.agents/testing.md` § Merge gate this spec is **sanctioned-RED** on that one
  signature until the fix ships; the closure record must say so.
- **#1884 (context only — NOT asserted here)** — `eliteacode.authToken` in this panel is
  the masked token, not a usable one. That defect is owned and soft-asserted by the
  ELITEA-2289 family AFS, which has the full token in scope because it creates the token
  itself. This case must **not** duplicate that assertion: it reads an arbitrary
  pre-existing row whose real token is unknowable, so any assertion here would be either
  vacuous or a second red for one cause.

## Blocked Steps
None.
