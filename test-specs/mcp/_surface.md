# Surface digest — Remote MCP (`/mcps/...`)

> Handle cache from live exploration. Verify each handle as you use it — this
> is a cache, not a source of truth. Last updated: 2026-08-02 (ELITEA-1934 /
> ELITEA-1937 implementer session, fix round 2 — testid gaps resolved via
> `add-data-testid`; originally created 2026-08-01, analyst session, cluster
> dispatch, `approved-top10` batch). **Appended 2026-08-24 during
> ELITEA-1923/1924 combined analysis+implementation** — create-form validation
> handles + the Save-button gating mechanism (see the two new sections at the
> end).
>
> ⚠️ **Appended 2026-08-24 (ELITEA-1938/1939/1940 cluster analysis, batch
> `mcp-w02`): the Test Settings surface was REFACTORED on 2026-08-20 by
> EliteaAI/EliteaUI@cb030b7d (`EL-6277`, #803). It is now its own ROUTE with a
> two-column layout. The `TestTools.jsx` state-machine section below is
> SUPERSEDED — read § Test Settings is now its own ROUTE (EL-6277) first.**

## Confirmed-stable handles (testid-based)

| Handle | Testid | Notes |
|---|---|---|
| Remote MCP type card | `toolkit-type-card-mcp` | `/mcps/create` type picker |
| Toolkit Name input | `toolkit-form-name-input` | shared create/detail |
| Url input | `toolkit-field-url-input` | shared create/detail |
| Save (create form) | `toolkit-form-save-button` | |
| Load Tools button | `toolkit-load-tools-button` | |
| Discovered tool pill (dynamic) | `toolkit-tool-chip-{tool_name}` | `data-selected` attr for checked state |
| Empty-state "Select Tool" button | `toolkit-test-empty-tool-select` | ONLY entry point into Test Settings — panel does not mount until a tool is chosen (EL-5947, gates BOTH MCP and Artifact surfaces) |
| Dropdown option (dynamic) | `select-option-{tool_value}` | shared pattern, MCP tool picks + empty-state tool picks |
| Test Settings Tool select (post-selection) | `toolkit-test-tool-select` | |
| Tool parameter field (dynamic) | `toolkit-test-param-{fieldKey}` | schema-property-keyed |
| Run button | `toolkit-test-run-tool-button` | **visible text is "Run Test", not "RUN TOOL"** — issue #1087, cosmetic only, locate via testid |
| Run Results container | `chat-message-list` | only exists in DOM AFTER Run is clicked — shared `ChatMessageList.jsx`, same testid the Artifact-toolkit surface uses |
| Run Results item | `chat-message-list li.MuiListItem-root` | scoped class constant, not a fresh testid |
| Url validation helper text | `toolkit-field-url-input-helper-text` | **Added/confirmed during ELITEA-1923 implementation (2026-08-24):** pre-existing, emitted generically by `ToolBaseProperty.jsx:610` as ``helperTextTestId={`toolkit-field-${k}-input-helper-text`}`` — so EVERY schema-driven toolkit field has one for free. Text is exactly `Field is required`; carries `Mui-error`. Element is UNMOUNTED (not hidden) once the field becomes valid — assert absence with `to_have_count(0)`. |
| Toolkit Name validation helper text | `toolkit-form-name-input-helper-text` | **Added during ELITEA-1924 implementation (2026-08-24)** — EliteaAI/EliteaUI@35440c78 on `automation/testids`, **not yet on `main`**. The Name field renders through `NameDescriptionInput.jsx`, NOT `ToolBaseProperty.jsx`, so it did NOT inherit the generic helper testid above; one-line additive `helperTextTestId` prop (`InputBase.jsx:101,270`). Description field intentionally left untouched (#511). |
| Raw Json view toggle | `toolkit-raw-json-view-toggle` | |
| Raw Json editor content | `toolkit-raw-json-editor-content` | CodeMirror virtualizes — use `get_raw_json_full()`, not `get_raw_json()`, for payloads >~30 lines |
| Detail title heading | `toolkit-detail-title` | shows "Edit Toolkit" placeholder until real data lands — poll text, don't trust visibility alone |
| Connection-status indicator ("Not Connected"/"Connected!") | `toolkit-connection-status` | `McpAuthStatus.jsx`, wrapping `Typography` — added via `add-data-testid` for ELITEA-1934 (2026-08-02). Born on `automation/testids` (EliteaUI@a467c0ac); **now on `main` ✓ since 2026-08-12** — promoted in EliteaAI/EliteaUI@bf4a13ad (400-testid bulk promotion, EliteaUI PR #753). *Corrected 2026-08-24 during ELITEA-1936 implementation: the previous "not yet on `main`" claim went stale at that promotion and was copied into ELITEA-1936's AFS. Re-verify provenance per case; never inherit it.* |
| Error toast (mcp_sync_tools failure) | `toast-message` | reuses the existing app-wide `Toast.jsx` component (same as `artifacts_page.py`/`skills_list_page.py`/`skill_detail_page.py`) — confirmed live, no new testid needed. Already on `main`. |
| Model selector NAME (not the button) in Test Settings panel, `variant="field"` branch | `model-selector-name` | `LLMModelSelector.jsx` — now applies in the `"field"` branch too (previously `"default"`-only), fixed via `add-data-testid` for ELITEA-1937 (2026-08-02), scoped to only this testid since that's the one ELITEA-1937's test reads. Born on `automation/testids` (EliteaUI@a467c0ac); **now on `main` ✓ since 2026-08-12** — same EliteaAI/EliteaUI@bf4a13ad bulk promotion (verified 2026-08-24). |

## Confirmed testid GAPS (flag to `add-data-testid`, don't build raw fallbacks into new code without a stop+flag reason)

| Element | Where | Recommended name | Issue |
|---|---|---|---|
| Model selector BUTTON (trigger) in Test Settings panel, `variant="field"` branch | `LLMModelSelector.jsx` — `data-testid="model-selector-button"` still only applies in the `variant="default"` branch, NOT `"field"` (the one actually rendered here) | reuse the existing `model-selector-button` string, extend it into the `"field"` branch (same pattern `model-selector-name` just followed) | **#1088 — OPEN, confirmed regression on already-merged ELITEA-1866**: `toolkit_test_settings_page.py`'s `model_selector_button` `LocatorDescriptor` is asserted at ELITEA-1866 step 25 and is CONFIRMED red against the `approved-top10` batch trunk (re-run 2026-08-02) for exactly this reason — pre-existing, not introduced by ELITEA-1934/1937's PR. Needs a dedicated `add-data-testid` + `adjust-automated-test` fix on the ELITEA-1866 spec. |

Two of the three gaps found during the ELITEA-1934/1937 analysis session
(connection-status indicator, error toast) are fully resolved — see
Confirmed-stable handles above. The third (`model-selector-name`/`-button`
pair, #1088) is only half-resolved: `model-selector-name` is fixed and in
Confirmed-stable handles; `model-selector-button` is still open, listed here.

## ~~State machine — `TestTools.jsx`~~ — SUPERSEDED 2026-08-20 by EL-6277

> ⚠️ **HISTORICAL ONLY — do not use for new work.** `TestTools.jsx` was deleted by
> EliteaAI/EliteaUI@cb030b7d (`EL-6277`, #803, 2026-08-20). The three-state machine
> below no longer describes the product: results no longer REPLACE the settings
> form, and there is no back-arrow. Kept because it explains the shape of the
> merged ELITEA-1866/1933/1937 specs and the #1086 clarification. **For current
> behaviour read § Test Settings is now its own ROUTE (EL-6277), below.**

### (historical) State machine — `TestTools.jsx` (governed BOTH Remote MCP and Artifact toolkit Test Settings panels)

Three mutually-exclusive states, driven by `selectedTool` + `hasRealMessages || isRunning`:

1. `!selectedTool` → `TestToolsEmptyState` — "Test toolkit" / "Choose a tool
   from the list to configure parameters and run the test." + the
   `toolkit-test-empty-tool-select` button. **This is NOT the "Welcome!
   Select a tool..." string** — that string exists in `indexChat.helpers.js`
   but isn't reachable from this flow (confirmed via source read).
2. `selectedTool && !hasRealMessages && !isRunning` → `TestToolSettings` — the
   plain form (Tool/Model/params/Run button). **No chat/welcome area exists
   in this state** — don't expect `chat-message-list` to be present yet.
3. `selectedTool && (hasRealMessages || isRunning)` → "Run Results" view —
   `ChatMessageList` (`chat-message-list` testid) replaces the settings form
   entirely (not a side-by-side column). A back-arrow button returns to
   state 2/3 (`handleClearChat`).

**Gotcha for anyone writing/reviewing a Test Settings assertion:** there is
NO state where a tool is selected, nothing has run, AND a welcome/chat message
is visible. If a case's own text implies otherwise, it's very likely
case-text drift (see #1086) — verify against this state machine before
concluding a defect.

## Fixtures

- **Public, auth-free, stable MCP server**: `https://mcp.deepwiki.com/mcp` — 3
  tools (`read_wiki_structure`, `read_wiki_contents`, `ask_question`).
  `read_wiki_structure`/`read_wiki_contents` need only a plain-string
  `repoName`; `ask_question` additionally needs `question` and its `repoName`
  is an `anyOf` (string-or-array) — more complex to automate, prefer the
  other two unless the `anyOf` shape is specifically under test. Confirmed
  live to return real content for `repoName: "AsyncFuncAI/deepwiki-open"`.
- **Guaranteed-unresolvable URL for negative/DNS-failure cases**:
  `https://nonexistent.invalid/mcp` — deterministic DNS failure, no
  flakiness risk from a transient real-domain hiccup.
- Tavily-based fixtures (`tavily_search` etc., referenced in some TMS case
  texts) require an API-key credential not provisioned in this environment —
  substitute the DeepWiki fixture and note it in the AFS Preconditions, same
  precedent set at ELITEA-1933.

## Save-button gating on the toolkit/MCP create form — the mechanism (settled 2026-08-24)

**Appended during ELITEA-1923/1924 combined analysis+implementation.** Read this before
writing ANY assertion about the create form's Save button — it has now cost two separate
sessions (ELITEA-1921, then ELITEA-1923/1924).

Source of truth, `src/pages/Toolkits/CreateToolkitToolTabBar.jsx:43-45`:

```js
const shouldDisableSave = useMemo(() => {
  return isLoading || !formik?.dirty;
}, [isLoading, formik?.dirty]);
```

**Save's disabled state is purely dirty-based.** It never consults required-field
validity, and never consults the Toolkit Name specifically. Therefore, confirmed live:

| Form state | `save_button.disabled` |
|---|---|
| Pristine, nothing touched | `true` |
| Toolkit Name filled only (Url empty) | `false` |
| Url filled only (Toolkit Name empty) | `false` |
| Both filled | `false` |

**Submission is still correctly gated** — clicking Save with any required field empty
fires **no** `POST .../tools/prompt_lib/{project}` at all; Formik/Yup renders an inline
`Field is required` under the offending field (`aria-invalid="true"`) and the page stays
on `/mcps/create/mcp`. `showValidation` flips to `true` on the Save click
(`onClickSave` → `setShowValidation(true)`), which is why NO error text is visible before
the first Save attempt no matter how long a required field sits empty.

**Consequences for anyone writing or reviewing an assertion here:**

- Only two Save-button states are safe to assert: **disabled on the pristine form**, and
  **enabled once anything is touched**. Any "still disabled after a partial fill"
  assertion is false against the live product.
- Tracked on **OPEN issue #633** (label `bug`, `[INFO]`). ELITEA-1924's case text asserts
  the false reading as its *entire Objective, step 4 and a Pass criterion*, so its
  automation carries a sanctioned-RED `expect.soft()` + `# Known defect: #633` and the
  case is `blocked-on-#633`, not `automated`, until a human rules product-vs-case-text
  (see the AFS at `test-specs/mcp/l2_create-remote-mcp-validation-missing-required-field_ELITEA-1923-1924.md`
  § Known Defects, and issue #633's 2026-08-24 comment).
- Do NOT assert that the pristine-form disabled state is *caused by* empty required
  fields — the cause is `!formik.dirty`.

## Create-form validation errors — how to assert them (2026-08-24)

- Message text is exactly `Field is required` for both Name and Url.
- **Assert the text exactly, not by visibility or substring.** The Scopes field renders a
  permanent, unrelated `Enter scopes separated by commas or spaces` helper in the same
  `.MuiFormHelperText-root` family — a loose "a helper text is visible" check passes on it.
- The error node is **removed from the DOM** when the field becomes valid, not hidden →
  `to_have_count(0)`, not `not_to_be_visible()`.
- The invalid input itself carries `aria-invalid="true"` — a useful second, testid-anchored
  signal (the attribute sits on the element that already has the field testid).
- Errors only appear **after** a Save click (`showValidation` gate) — never before.

## Fixtures (addendum, 2026-08-24)

- `https://mcp.example.com/sse` is fine for any case that only **stores** a URL (create /
  validation / persistence). It is never dialled unless Load Tools is clicked, so its
  unreachability is irrelevant there — reserve the DeepWiki fixture for cases that
  actually discover tools.
- Toolkit-name length: `MAX_NAME_LENGTH = 32` is enforced as `inputProps.maxLength` and
  **silently truncates**. Compute the uuid-suffix length against the case's literal base
  name every time (`autotest_validation_no_url` = 26 → 4-hex suffix = 31 ✓).
- After a fresh `goto('/mcps/create')` the type-card mounts **asynchronously** — an
  immediate DOM read misses `toolkit-type-card-mcp`. Observed twice this session. Rely on
  framework auto-waiting; never an immediate `query_selector`.

## MCP DETAIL page: configuration fields are COLLAPSED (found 2026-08-24)

**Appended during ELITEA-1923/1924 implementation. This currently breaks three merged
specs — read it before writing or debugging any detail-page field assertion.**

The create form (`/mcps/create/mcp`) renders every schema-driven field inline. The
**detail** page (`/mcps/all/{id}`) does not: it renders **no `toolkit-field-*` element at
all** until the `toolkit-configuration-show-more` control is clicked. Verified live — the
DOM of a freshly created MCP was polled for 15 s and contained **zero** `toolkit-field-*`
testids; only after clicking show-more did `toolkit-field-url-input` appear, holding the
persisted value.

Use `McpFormPage.expand_configuration_section()` (added ELITEA-1923/1924; a no-op when
already expanded — the toggle unmounts once clicked) before ANY detail-page assertion on
`url` / `client_id` / `timeout` / `cache_ttl` / `enable_caching` / `ssl_verify` / ….

### Already-merged specs currently RED on `automation/base` because of this

Confirmed by control runs against the **unmodified base** page object:

| Spec | Symptom |
|---|---|
| `test_mcp_create_remote.py::test_create_remote_mcp_all_fields_populated` | `Locator.input_value` timeout on `toolkit-field-*` |
| `test_mcp_create_remote.py::test_create_remote_mcp_minimal_required_fields` | same |
| `test_mcp_edit_toggle_enable_caching.py` | `Locator.is_checked` timeout on `toolkit-field-enable_caching-checkbox-field` |

Each needs one `expand_configuration_section()` call — an `adjust-automated-test` pass,
not a hand-fix inside an unrelated case's PR.

## `_wait_for_detail_data_rendered()` was a no-op on MCP pages (fixed 2026-08-24)

EliteaUI keeps one detail-title `fallbackLabel` **per entity type**
(`src/[fsd]/shared/lib/constants/breadcrumb.constants.js`): `"Edit Toolkit"` (line 15) for
`/toolkits`, `"Edit MCP"` (line 47) for `/mcps`. The page object's wait excluded only
`"Edit Toolkit"`, so on every `/mcps/all/{id}` caller it returned immediately and callers
read `"Edit MCP"` as the toolkit name. Now driven by `DETAIL_TITLE_PLACEHOLDERS`. If a new
entity type appears (`/apps`?), check `breadcrumb.constants.js` and extend that tuple.

## MCP DETAIL page: Save/Discard gating, header refresh, and (no) success toast (2026-08-24)

**Appended during ELITEA-1925/1926 combined analysis+implementation.** These are the
*detail* page's behaviours — do NOT carry the create-form's #633 lesson across, they are
different components with different gates.

- **Save AND Discard both gate on `isFormDirtyExcluding`** —
  `src/[fsd]/features/toolkits/ui/toolkits-tab-bar/ToolkitsTabBarContainer.jsx:102-109`
  (`shouldDisableSave = isSaving || !isFormDirtyExcluding || reasonFor === saveNewVersion
  || hasValidationErrors`) and `:157-160` for Discard. Confirmed live: both disabled on a
  pristine detail page, both enabled after touching a single field. So unlike the create
  form (#633), a "Save becomes enabled after editing" assertion IS honest here — and the
  pristine-disabled baseline is real too.
- **The detail header (`toolkit-detail-title`) lags the Save.** Read immediately after the
  `PUT` resolves, it still shows the OLD name; ~5 s later it shows the new one and stays
  (stable at +2/+5/+10 s and across a full reload). Not a defect — a re-render/cache-refresh
  delay with no user action needed. **Assert it with a retrying web-first assertion**
  (`expect(form.detail_title).to_have_text(...)`); a bare `get_detail_heading_text()` read
  right after Save is a guaranteed flake (it failed on probe 1, passed on probe 2 only
  because an unrelated 5 s lookup sat in between).
- **No success toast is rendered on the MCP detail Save.** `ToolkitsTabBarContainer.jsx`
  calls `toastSuccess('The toolkit has been updated successfully')` on `isSaveSuccess`, but
  `toast-message` never appears within a 5 s wait — confirmed on two independent probes.
  Assert the `PUT` 200 + the updated state instead; never wait on a toast here.
- **The configuration section re-collapses after `reload_and_wait()`** — call
  `expand_configuration_section()` again after every reload, not just on first load.

## `McpListPage.open_card_by_name()` does NOT wait for the detail page (2026-08-24)

**Resolved/added during ELITEA-1925 implementation (fix round 1):** `open_card_by_name()`
clicks the card and waits only for that click's own network settle — its docstring
explicitly assigns the destination page's ready-wait to the caller. Any read taken
immediately after it races the detail page's `"Edit MCP"` title placeholder and an
unpopulated Name field. **Always follow it with `McpFormPage.wait_for_page_load()`**
(which delegates to `_wait_for_detail_data_rendered()`), and prefer retrying
`expect(...)` assertions over bare `text_content()` / `input_value()` reads afterwards —
the header lags on this surface (see the section above).

## MCP DETAIL page: Discard is CONFIRMED through a modal (2026-08-24)

**Appended during ELITEA-1928/1930 combined analysis+implementation.**

Clicking `toolkit-detail-discard-button` does **not** revert anything. It opens a
confirmation modal (`Button.DiscardButton` → `Modal.BaseModal`,
`src/[fsd]/shared/ui/button/DiscardButton.jsx`) reading:

```
Warning
Are you sure you want to discard changes?
Cancel   Discard
```

The form still holds the edited value and both buttons stay enabled until the
modal's own **Discard** is clicked; then the modal **unmounts** (detached, not
hidden), the edited field reverts, and Save + Discard both return to disabled.
Verified live 2026-08-24 on toolkit 3029 — and **no `PUT` is issued anywhere in
the flow** (network log showed only the seed POST and the detail GETs), so a
discard is genuinely server-side inert.

| Handle | Testid | Notes |
|---|---|---|
| Discard-confirm modal | `toolkit-detail-discard-confirm-modal` | **Added 2026-08-24** — EliteaAI/EliteaUI@a51c9318 on `automation/testids`, **not yet on `main`**. Lands on the MUI `Dialog` root, so `text_content()` includes the title and both button labels → assert with `in`, never `==`. |
| Discard-confirm "Discard" button | `toolkit-detail-discard-confirm-button` | Same commit. |

Both were added by passing `modalDataTestId` / `confirmButtonDataTestId` — props
the shared `Button.DiscardButton` already accepts and the **credentials** tab bar
already supplies (`credential-discard-confirm-modal` / `-button`) — at the
toolkit-detail call site (`ToolkitsTabBarContainer.jsx:158`). Two additive props,
no new DOM node, no hook, no behaviour change. Per #511, `cancelButtonTestId` /
`closeButtonTestId` / `modalTitleTestId` were deliberately left unpassed.

**Case-text note:** ELITEA-1928's step 5 (`Click Discard → Discard action is
triggered`) omits this modal entirely. Filed as a clarification, not a bug — the
Credentials surface (ELITEA-1971) has the identical modal and is already automated
against it.

## The description field is INLINE on the detail page (2026-08-24)

Do not reach for `expand_configuration_section()` for it. Only the schema-driven
`toolkit-field-*` handles are collapsed; `toolkit-form-name-input` and
`toolkit-form-description-input` render inline on the detail page because they go
through `NameDescriptionInput.jsx`, not `ToolBaseProperty.jsx` (the same split
that made ELITEA-1924 need its own `helperTextTestId`).

## `toolkit-configuration-show-more` MOUNTS LATE — the expand helper could no-op (fixed 2026-08-24)

**Resolved/added during ELITEA-1930 implementation.** Polled live immediately
after a `goto` on `/mcps/all/{id}`: `toolkit-detail-title` had already resolved to
the real toolkit name while `toolkit-configuration-show-more` was still absent; it
appeared ~1 s later (10 × 500 ms poll, absent at the pre-poll read, present from
t=0 of the poll onward). So a title-based readiness wait does **not** imply the
toggle has mounted.

`McpFormPage.expand_configuration_section()` early-returned on
`configuration_show_more.count() == 0` — a non-waiting read — so calling it too
early silently no-op'd and every following `toolkit-field-*` read then timed out
with a misleading "element not found". Fixed by inverting the early-return to key
off the **fields** instead of the toggle: return immediately when `url_input`
already exists (create form, or an already-expanded section), otherwise
`wait_for(state="visible")` the toggle before clicking it. The three existing call
sites (`test_mcp_edit_url.py:116,155`, `test_mcp_create_validation.py:310`) were
re-run against the change — see PR.

## Ssl Verify — confirmed behaviour (ELITEA-1930, 2026-08-24)

- Defaults to **checked** on a freshly created Remote MCP (`settings.ssl_verify:
  true`).
- Expanding the configuration section does **not** dirty the form (Save/Discard
  stay disabled) — safe to expand before capturing a pristine baseline.
- Unchecking → Save → `PUT /tool/prompt_lib/{project}/{id}` 200 with
  `settings.ssl_verify: false`; survives a full reload; Raw Json (376-char
  payload, no virtualization risk) shows the boolean `false` under `settings`.

## Headers JSON editor + Client Secret secret-toggle (ELITEA-1931 / ELITEA-1932, 2026-08-24)

**Appended during the ELITEA-1931/1932 combined analysis+implementation.** Both fields
live inside the *Configuration* section, so everything in § MCP DETAIL page:
configuration fields are COLLAPSED applies before any of these handles resolves.

| Handle | Testid | Notes |
|---|---|---|
| Headers JSON editor wrapper / content | `toolkit-field-headers-editor` / `-content` | pre-existing, on `main`. CodeMirror. |
| Client Secret wrapper (SecretField root) | `toolkit-field-client_secret-input` | the real `<input>` is `...-input-field` and exists **only in Password mode** |
| Secret / Password toggle buttons | `toolkit-field-client_secret-input-toggle-secret` / `-toggle-password` | emitted generically by `SecretField.jsx:342` → `Toggle.jsx` (`testIdPrefix = "<field-testid>-toggle"`), so EVERY secret schema field gets the pair for free. State = `aria-pressed`. **Verified during ELITEA-1932 fix round 1 (2026-08-24): the whole mechanism is `automation/testids`-only** — EliteaAI/EliteaUI@5892ae48 (EL-1967). `Toggle.jsx` on `origin/main` carries NO testid at all and `SecretField.jsx` on `main` passes no `testIdPrefix`, so any case using this pair is green on localhost and NOT deployed-env promotable. The literal never appears in `src/` on either ref (three-level composition) — check provenance on the composing FILE, not by grepping the testid string. |
| Vault select (Secret mode only) | `toolkit-field-client_secret-input-combobox` | mounts in place of the native input |
| Saved-secret option (dynamic) | `select-option-{{secret.<name>}}` | same grammar `CredentialCreatePage.SECRET_SAVED_OPTION` already uses |

- **The Headers editor commits on BLUR — this is the trap.** With focus still in the
  editor after typing valid JSON, `toolkit-detail-save-button` stays **disabled**;
  clicking any other control flips Save + Discard to enabled. Same class as the
  credentials `scopes` field. On blur the editor also **pretty-prints** the JSON, so
  `text_content()` becomes `{  "X-Custom-Header": "test-value"}` (CodeMirror line
  `<div>`s concatenate with no newline) — always `json.loads` it, never string-compare.
- `McpFormPage.fill_headers_json()` deliberately does **not** blur (its merged
  ELITEA-1922 caller reads the editor text pre-format); use the additive
  `blur_headers_editor()` before Save.
- **Switching Raw Json → Form view keeps the configuration section expanded.** Only a
  full reload re-collapses it.
- **Client Secret mode is derived, not stored.** `SecretField.jsx` re-enters Secret mode
  after a reload only when the stored value matches `/^{{secret\.([A-Za-z0-9_]+)}}$/`
  **and** that name is still in the project vault; otherwise it falls back to Password
  mode. `auth_token` is the stable read-only vault entry in project 399 (also used by
  the merged credentials case ELITEA-1968).
- The credentials dropdown-close defect **#1047 does not reproduce here** — selecting a
  saved secret closed the dropdown normally on the MCP detail page.
- **Case-text divergence (ELITEA-1931 step 2):** there is no "Headers accordion" — the
  case's step is satisfied by expanding the single Configuration section. Filed as
  clarification #1719 (also records the commit-on-blur behaviour).

## Connection status + `selected_tools` via Raw Json (ELITEA-1935 / ELITEA-1936, 2026-08-24)

**Appended during the ELITEA-1935/1936 cluster analysis.**

### There is NO connection badge on MCP list cards

An MCP list card's complete testid inventory is `entity-card-icon`,
`entity-card-name`, `entity-card-tag-chip`, `mcp-pin-toggle-button-<id>`.
`entity-card-tag-chip` renders the **type** (`Remote`), not a connection state.
A page-wide text probe for `Disconnected` / `Not Connected` / `Connected!` on
`/mcps/all` returns **false for all three** (18 cards, verified live). Source
agrees: `grep -rn "Disconnected" src/` hits only the chat-participants feature
(`mcpIsDisconnected`, a different surface — issue #687) and the guided-tour
markdown. Connection status exists **only on the detail page**.
ELITEA-1936's step 2 asserts otherwise — filed as clarification **#1723**.

### The Login button is fully automatable — no OAuth window for a no-OAuth server

`McpAuthStatus.jsx` → `onLogin` → `useMcpAuthCheck.runAuthCheck` emits a
**socket `test_mcp_connection`** event (protocol-level `tools/list`). For a
public server (DeepWiki) it succeeds in-page: `setConnectionVerified(url)` runs
and the indicator flips. **No external window, no redirect, no credential.**
Only a server that actually demands OAuth opens `McpAuthModal`.

| Observable | Value |
|---|---|
| Status text | `Not Connected` → `Connected!` (**trailing `!`** — case texts omit it) |
| Button label | `Login` → `Logging in...` (transient) → `Logout` |
| Round-trip time | **< 500 ms** against DeepWiki — do NOT assert the `Logging in...` label, it is a guaranteed flake |

### ⚠️ Connection state lives in `sessionStorage`, keyed by SERVER URL

```
sessionStorage["elitea_mcp_tokens_v1"]
  = {"https://mcp.deepwiki.com/mcp": {"access_token": "__connection_verified__",
     "issued_at": …, "expires_at": …, "connection_verified": true}}
```

Per-context, so a fresh Playwright context gives an honest `Not Connected`
baseline — **but it is keyed by URL, not by toolkit**, so a unique per-test
toolkit name does NOT isolate you. Any earlier test in the same context that
connected to the same fixture URL leaves the next one already `Connected!`.
Clear the key in setup or take a fresh context.

### `available_mcp_tools` is CONDITIONAL, not absent (corrects #574)

The blanket claim "the live product never renders `available_mcp_tools`" came
from toolkits explored **before Load Tools**. Once tools are discovered the
field is present and fully populated (`label` / `value` / `args_schema` per
tool) — confirmed both in the editor and via `get_raw_json_full()`.
Commented on #574. No change needed to `test_mcp_edit_raw_json_description.py`
(its fixture has no tools loaded, so absence is correct there).

### Editing `selected_tools` through the Raw Json editor

`selected_tools` renders **one array element per line**, sorted, all discovered
tools selected by default after Load Tools.

- **Removing** a tool = deleting its whole line. Target a **non-last** element —
  removing the last one strands the preceding line's trailing comma and the JSON
  becomes invalid. `ask_question` sorts first with the DeepWiki fixture.
- `Home` in CodeMirror is **smart-home** (first non-whitespace), so
  `Home` → `Shift+End` → `Backspace` leaves the indentation behind. That
  whitespace-only line is valid JSON and the server normalises it away on save.
- **Re-adding** is a one-line replacement with the existing
  `fill_raw_json_line('"read_wiki_contents",', '"ask_question", "read_wiki_contents",')`
  — JSON is whitespace-insensitive, two names on one line is valid, server
  reformats. Verified live end-to-end.
- `McpFormPage` has **no line-delete helper** — ELITEA-1935's AFS specs
  `delete_raw_json_line()` (same shape as `fill_raw_json_line`, `Backspace`
  instead of `type`, inheriting its declared #579 exception).

### Three traps that each cost a probe this session

1. **`get_raw_json_full()` leaves the editor scrolled to the BOTTOM.** A
   `fill_raw_json_line()` afterwards fails with `Locator.click: Timeout` — the
   target line has been virtualized out of the DOM. **Do per-line edits BEFORE
   any full read**, or scroll back to the top first.
2. **Never `.fill()` the raw-JSON editor.** It is a contenteditable CodeMirror
   root, so `fill()` replaces the **entire document** (observed: 29 lines → 1).
   Per-line editing only. (Nothing saves in that state — Save goes disabled —
   but recovery needs a reload.)
3. **`is_save_button_disabled()` targets the CREATE-form Save**
   (`toolkit-form-save-button`), which does not exist on the detail page — it
   times out after 10 s. Use `detail_save_button` there.

### Tool chips: selection is an ATTRIBUTE, not presence

Deselecting a tool does **not** remove its chip — the chip list is driven by
`available_mcp_tools`, the selection by `selected_tools`. All 3 chips stay
rendered; the deselected one flips to `data-selected="false"`. Chip `innerText`
is **empty** — never assert on chip text. Use
`McpFormPage.is_tool_chip_selected(name)`.

### `toolkit-type-card-mcp` mount delay is longer than previously logged

Observed **3.5 s** this session (the earlier note said ~1 s). Rely on framework
auto-waiting; never an immediate `query_selector` after `goto('/mcps/create')`.

## Resolved/added during ELITEA-1935 / ELITEA-1936 implementation (2026-08-24)

*Implementer-appended, attributed per the digest's one-writer rule — these are
implementation-time facts, not a rewrite of the analyst's behaviour claims.*

### New testid: `toolkit-connection-status-icon`

The `OnlineIcon` svg sitting next to the connection-status text in
`McpAuthStatus.jsx` had no testid, and chaining a raw `svg` selector off
`toolkit-connection-status` is forbidden. Added as one additive attribute —
EliteaAI/EliteaUI@55dc4f66 on `automation/testids`, **not yet on `main`**
(human cherry-pick pending). Zero functional impact: no new DOM node, no hook,
no removed markup.

### ⚠️ Fourth Raw-Json trap: CodeMirror's **selectionMatch** makes a line locator ambiguous

`fill_raw_json_line()` / `delete_raw_json_line()` select a line with
`Home`/`Shift+End`. The instant that selection lands, CodeMirror's
`selectionMatch` extension wraps **every other occurrence of the selected text**
in a `cm-selectionMatch` `<span>` — so re-resolving the same
`get_by_text(..., exact=True)` locator for the selection wait raises
`strict mode violation: ... resolved to 3 elements`.

It bites on any document where the line text recurs — which is *every*
tools-loaded MCP, because a tool name appears both in `selected_tools`
(`"ask_question",`) and in `available_mcp_tools` (`"value": "ask_question",`,
whose selectionMatch span is exactly `"ask_question",`).

**Fix, now shipped in both methods:** resolve the `ElementHandle` BEFORE the
click and wait on that handle via the new
`_wait_for_line_selection_applied_handle()`. `fill_raw_json_line()` carried this
latent bug since ELITEA-1927 (its only merged caller edits a `"description"`
line, which never recurs) — re-run green after the fix.

### New helper: `McpFormPage.scroll_raw_json_to_top()`

Trap 1 above ("`get_raw_json_full()` leaves the editor scrolled to the BOTTOM")
says to edit before reading — but ELITEA-1935's own step order is read (step 3)
then edit (step 4), so that isn't available. The helper re-uses
`get_raw_json_full()`'s scrollable-ancestor walk and sets `scrollTop = 0`. Call
it before any per-line edit that follows a full read.

### New helper: `McpListPage.get_card_texts()`

Absence assertions on the list page (#1723: "no card renders a connection
badge") have no testid to bind to, because the element does not exist. Reading
each card's own text through the testid-anchored `entity-card` container is the
closest testid-only shape; page-wide `get_by_text` would be a new raw handle.

### Confirmed live this session

- `available_mcp_tools` entries carry `label` / `value` / `args_schema`; the
  `value` is the raw tool name (matches the chip testid suffix and the
  `selected_tools` entries).
- The detail Save's `PUT` response body carries the full `settings`, so
  `selected_tools` can be asserted from the **response** as well as the DOM.
- `sessionStorage["elitea_mcp_tokens_v1"]` is empty at test start under the
  standard `page` fixture (fresh browser context per test) — the `Not Connected`
  baseline needs no explicit clearing, and the record dies with the context.
- The Login round-trip against DeepWiki settles well inside the 20 s
  `SAVE_RESPONSE_TIMEOUT`; the whole ELITEA-1936 spec runs in ~24 s.


## Test Settings is now its own ROUTE (EL-6277) — read this before ANY Test-panel work

**Confirmed live 2026-08-24** (ELITEA-1938/1939/1940 cluster analysis, batch
`mcp-w02`), against `EliteaAI/EliteaUI` @ `automation/testids`, MCP id 2140.
Supersedes the `TestTools.jsx` state-machine section above.

`EliteaAI/EliteaUI@cb030b7d` — `feat: [EL-6277] move indexes into the details
right panel (#803)`, 2026-08-20 — replaced `TestTools.jsx` with
`src/[fsd]/features/toolkits/ui/toolkit-test/ToolkitTestPanel.jsx`:

- **The Test surface is a ROUTE**, `/mcps/all/{id}/test` (toolkits:
  `/toolkits/all/{id}/test`) — **not** a right-hand region of the detail page.
  Reached from the detail **action bar** (`toolkit-action-bar`) via
  `toolkit-test-button` (aria-label `Test MCP`). Direct URL navigation works too.
- **Two-column layout, side by side**: left header `Test Settings`, right header
  `Results`. Results no longer REPLACE the settings form — both are visible at
  once, so the old "run-results view swaps in / back-arrow returns" model is gone.
- **Both column headers are plain `Typography` with NO buttons.** The only
  buttons on the page: the connection-status `toolkit-connection-login-button`,
  the Model Settings gear (no testid), `toolkit-test-run-tool-button`, and —
  after a run — `chat-copy-button`.
- The tool-selection gating from EL-5947 is unchanged: with no tool selected the
  left column renders `ToolkitTestEmptyState` and `toolkit-test-empty-tool-select`
  ("Select Tool") is the only route into the settings form.
- `ToolkitTestResults.jsx` renders `null` while `messages.length === 0`, so
  `chat-message-list` still does not exist in the DOM before the first run
  (#1086 holds after the refactor).

### The trio of header controls the ELITEA-1938/1939/1940 case texts describe is GONE

Pre-EL-5947 `TestTools.jsx@0cff136d^` really did render all three in the panel
header (lines 191/195/196): `FullScreenToggle`, `ChatButton.ClearChatButton`,
`ViewRunHistoryButton`. Two deliberate commits dismantled it:

| Control | Fate | Today |
|---|---|---|
| **Clear the chat** (trash) | removed by `EL-5947` (@0cff136d, 2026-07-30), demoted to an unlabelled back-arrow; that back-arrow removed by `EL-6277` | **no control at all** — `handleClearChat` is still exposed by `useToolkitTestRunner` but consumed by nothing. Clarification **#1725**, ELITEA-1938 `blocked` |
| **Fullscreen mode** | removed by `EL-5947`; never returned | **no control at all**. `FullScreenToggle.jsx` still lives and is still wired on `SkillTestPanel.jsx` / `IndexChat.jsx` / Applications `ConfigurationTab.jsx` — and carries **no testid** there either. Clarification **#1726**, ELITEA-1939 `blocked` |
| **View run history** | **relocated**, not removed | lives in the DETAIL **action bar** (`ToolkitForm.jsx:562`, rendered when `isDetailsActionBar`). Clarification **#1727**, ELITEA-1940 `ready-for-automation` |

**Before filing "control X is missing" on this surface, check this table** — two
cases already spent a session rediscovering it.

## Run History on the MCP / toolkit surface (2026-08-24, ELITEA-1940)

| Handle | Testid | Notes |
|---|---|---|
| Run History button | `pipeline-history-tab` | In the DETAIL action bar. aria-label `view run history`, label "Run History". **The `pipeline-` prefix is a shared-component default** (`ViewRunHistoryButton.jsx:16`, `testId = 'pipeline-history-tab'`) — it is correct on the MCP surface too; already used by `PipelineDetailPage`. Do not rename. |
| Run-history row | `run-history-list-item` | Same literal testid on EVERY row — distinguish positionally. Default sort Date-descending ⇒ index 0 = most recent. |
| Row selected state | `[data-testid="run-history-list-item"][data-selected="true"]` | `RunHistoryListItem.jsx:151`. Testid + state attribute, the policy-compliant shape. |
| Row overflow menu | `run-history-menu-menu-button` | present; wire only if a case's executed path calls it (#511) |
| Detail pane | `chat-message-list` / `chat-message-item` | 2 items per run: the input (`Calling '<tool>' with parameters:` + JSON) and the output |

- **Route:** clicking it navigates to **`/toolkits/all/{id}/history?isMCP=true`** —
  a full PAGE, not a drawer. MCPs deliberately reuse the toolkit route with an
  `isMCP` query flag (`useToolkitDetailNavigation.hooks.js`'s own doc comment
  says so). Breadcrumb reads `Toolkits & Indexes / <name> / Run History`.
- **Columns are `Date` + `Duration`** (e.g. `24-08-2026, 06:17 AM` / `1.19 s`).
  No `Version` column here — the Agent surface's ELITEA-1876/#1282 note records
  Date/Version/Duration; that is a DIFFERENT surface. Assert per surface.
- **Row 0 is auto-selected on mount** (`RunHistoryContainer.jsx`: selects
  `historyRows[0]` when nothing is selected). A "click an entry → details show"
  assertion that clicks row 0 proves nothing — click a *different* row and assert
  the `data-selected` flip AND the detail-content change. Needs ≥2 runs to be
  meaningful.
- Already automated on two OTHER surfaces with the same component — reuse the
  shape: `pages/pipeline_detail_page.py:57,69-71,6897-7000` (ELITEA-2011/2070)
  and `AgentDetailPage` (ELITEA-1876/1877).

### Resolved/added during ELITEA-1940 implementation (2026-08-24)

- **One Run History row is one CONVERSATION, not one Run Test click.**
  `useToolkitChat.executeRunTool` creates a conversation only when
  `!activeConversation`, so N runs inside a single mount of the Test panel all
  land in ONE history row. To produce two rows, leave and re-enter the Test
  route between runs (detail page -> `toolkit-test-button` -> re-select the
  tool -> Run) — that remounts the panel and clears `activeConversation`.
  Measured live: two back-to-back Run Test clicks produced exactly 1 row.
- The Test panel's Results list **appends** across runs within a mount
  (`setChatHistory(prev => [...prev, ...])`), so
  `ToolkitTestSettingsPage.wait_for_tool_result()` (which reads `.last`) can
  return the PREVIOUS run's already-completed ✅ message if a second run is
  started in the same mount. Another reason to remount between runs.
- Page objects added/extended: new `ToolkitRunHistoryPage`
  (`automation/pages/toolkit_run_history_page.py`) for the
  `/toolkits/all/{id}/history` route; `McpFormPage.action_bar` / `.test_button`
  / `.run_history_button` + `open_test_route()` / `open_run_history()` /
  `is_test_button_disabled()`; `ToolkitTestSettingsPage.set_param_field()`
  (additive sibling of `fill_param_field`, which types into whatever is already
  there and therefore APPENDS on a re-run).
- **Merged spec `tests/ui/toolkits/test_mcp_test_settings_select_and_run_tool.py`
  (ELITEA-1937) is RED on localhost** as of 2026-08-24, independently of this
  case's branch: it waits for `toolkit-test-empty-tool-select` on the DETAIL
  page, which EL-6277 moved to the `/mcps/all/{id}/test` route. Verified by
  running it standalone (fails in Step 2: `Timeout 10000ms exceeded waiting for
  get_by_test_id("toolkit-test-empty-tool-select")`). Needs an
  `adjust-automated-test` pass — reported to the lead, not fixed here.

## Sequencing gotchas on the MCP detail page (2026-08-24, both cost real time)

1. **`toolkit-test-button` is disabled while the detail form is dirty** —
   `ToolkitForm.jsx` passes `isTestDisabled={dirty}`. Clicking **Load Tools**
   dirties the form, so a flow that loads tools must click
   `toolkit-detail-save-button` and WAIT for `toolkit-test-button` to re-enable
   before it can reach the Test route. Otherwise the button never becomes
   clickable and the flow hangs on a disabled element.
2. **The action bar mounts asynchronously after a client-side navigation back to
   the detail page** — `pipeline-history-tab` returned *"does not match any
   elements"* on an immediate click and appeared on a subsequent poll. Same class
   as the existing `toolkit-type-card-mcp` note in § Fixtures (addendum). Rely on
   framework auto-waiting / an explicit `wait_for(state="visible")`.

> **Digest size note (2026-08-24):** this file is now ~600 lines, well past the
> comfortable-single-read threshold the `test-case-analysis` skill flags (~150).
> A split into an index + per-subarea files (create-form / detail-page /
> test-surface / run-history / fixtures) is overdue. Not done in this batch —
> several merged AFS files reference this path, so the restructure wants its own
> unit rather than a mid-wave edit. Flagged to the lead.

---

## MCP DETAIL three-dot ("controls") menu — full inventory + Copy link / Pin to top (2026-08-24)

**Appended during ELITEA-1946 / ELITEA-1959 cluster analysis, batch `mcp-w02`.** Everything
below was observed live against `http://localhost:5173`, MCP `2140`, project `399`.

### Menu inventory (owner viewMode, private project)

Rendered by `src/[fsd]/features/toolkits/ui/toolkits-tab-bar/ToolkitsControls.jsx:60-73`,
in this DOM order:

| # | Label | testid | State |
|---|---|---|---|
| 1 | `Export` | **none** | `aria-disabled="true"` (hardcoded `disabled: true` at `ToolkitsControls.jsx:51`) |
| 2 | `Fork` | `toolkit-actions-fork-menuitem` | `aria-disabled="true"` (hardcoded) |
| 3 | `Copy link` | `Copy link-menuitem` ⚠️ | enabled |
| 4 | `Pin to top` / `Unpin from top` | **none** | enabled |
| 5 | `Delete` | `toolkit-actions-delete-menuitem` | enabled |

Container handles: `controls-menu-button` (trigger) + `controls-menu` (popup) — both
already `McpFormPage` fields, both on `main` ✓.

**Menu items get their testid from their `key`:** `DotMenu.jsx:422` wires `testId: item.key`
and `DotMenu.jsx:58` renders `data-testid={testId ? \`${testId}-menuitem\` : undefined}`.
So the full testid string **never appears in EliteaUI source** — a closure-record grep must
search the **key** (`toolkit-actions-delete`), not the composed value. Both existing keys are
on `main` ✓ (`DeleteToolkitButton.jsx:72`, `ForkEntityButton.jsx:26`).

### Three testid gaps on this menu (work orders, not waivers)

| Element | Recommended testid | One-line fix |
|---|---|---|
| `Export` | `toolkit-actions-export-menuitem` | `useExportToolkitMenu()` (`ExportToolkitButton.jsx:38-40`) builds its menuItem with **no `key` at all** → no testid renders. Add an **optional** `key` param (same shape `usePinMenu` already uses) and pass `key: 'toolkit-actions-export'` from `ToolkitsControls.jsx:51`. |
| `Copy link` | `copy-link-toolkit-menuitem` | Today's `Copy link-menuitem` is the **label leaking into the testid, space and all** — `useCopyLinkMenu()` defaults `key: key \|\| label` (`CopyLinkToEntityButton.jsx:44`). The hook already accepts `key`; pass `key: 'copy-link-toolkit'` at `ToolkitsControls.jsx:43`. Verified 0 references to the old string anywhere in `automation/` — the rename is safe. |
| `Pin to top` | `pin-toggle-toolkit-menuitem` | `usePinMenu()` already supports an optional `key` (added for ELITEA-2049); `ToolkitsControls.jsx:45-49` is the one caller not passing one. Mirror credentials' existing `pin-toggle-credential`. |

Testid = **stable identity**; the pinned/unpinned state is read from the item's **text**
(`Pin to top` / `Unpin from top`), never from a state-flavoured testid variant.

### Confirmed behaviours

- **Copy link → toast** `toast-message` = exactly `The link has been copied to the clipboard.`
  (trailing period; the TMS case texts omit it). Auto-dismisses in a few seconds — wait for it
  **in the same synchronous chain as the click**; a DOM read one turn later finds nothing
  (this bit twice during analysis).
- **Copied URL shape:** `{origin}{APP_PREFIX}/{projectId}/mcps/all/{id}?viewMode=owner&name={encoded name}`.
  Observed: `http://localhost:5173/399/mcps/all/2140?viewMode=owner&name=autotest_mcp_run_tool`.
  Built by `useProjectEntityLink()` (`src/hooks/useProjectEntityLink.js:12-14`) as
  `origin + getBasename() + details.projectPath + (details.search || '?viewMode=' + viewMode)`,
  and `usePageDetails().projectPath` carries `PROJECT_ID_URL_PREFIX`. **The `/{projectId}`
  segment is real and by design** — ELITEA-1959's case text omits it, filed as CLARIFICATION
  [#1729](https://github.com/EliteaAI/elitea-testing-public/issues/1729). Never hardcode the
  host or project id; build from `settings.app_base_url` + `settings.elitea_project_id`.
- **Opening that URL in a new tab works**, via a `ProjectSwitcher` hard `window.location.replace()`
  that strips the `/{projectId}` prefix — final URL settles at `/mcps/all/{id}?viewMode=owner&name=…`.
  Assert on the settled state, never on the URL right after `goto`. Same hop documented for ELITEA-1898.
- **Any menu-item click closes the menu** (`DotMenu.jsx`'s `withClose`). Consequence: to test
  Escape-to-close you must **re-open the menu first**, or the assertion passes vacuously
  (the ELITEA-2049 review-round-1 lesson, re-confirmed here).
- **`Escape` closes the menu by UNMOUNTING it** → assert `to_have_count(0)`, not `not_to_be_visible()`.
- **Pin from the detail menu:** `POST /api/v2/social/pin/prompt_lib/{project}/toolkit/{id}` → **201 Created**;
  unpin → `DELETE` same path → **204 No Content**. Same asymmetric shape as credentials/pipelines.
  After pinning, re-opening the menu shows `Unpin from top`, and `/mcps/all` puts the MCP at
  **index 0** (verified: it jumped from index 3 to index 0 with no reload beyond the navigation).
- **List-row pin toggle** is `mcp-pin-toggle-button-{id}` (`PinButton.jsx:98`,
  `${getPinTestIdSlug(entityType)}-pin-toggle-button-${entityId}`, on `main` ✓). Its state is
  in `aria-label` (`Pin to top` / `Unpin from top`) — a clean, testid-anchored state read.
- **Pin timing is asymmetric** (consistent with the merged credential/pipeline pin tests):
  pinning re-sorts immediately; **unpinning does not** — the entity stays at the top until a
  fresh navigate/re-fetch, even though its label flips back instantly.
- **State of project 399 as of 2026-08-24:** 19 MCPs, none pinned, default sort newest-first
  (id-descending). A freshly created MCP is therefore already at index 0 — **a pin test must
  create TWO MCPs** (A then B, pin A) or the "moves to top" assertion is vacuous.

### Clipboard, in this repo

- `conftest.py:303` already grants `clipboard-read` + `clipboard-write` suite-wide; the merged
  tests re-grant defensively per test. **Without the grant, `navigator.clipboard.readText()`
  raises `NotAllowedError: Read permission denied`** (reproduced verbatim in the Playwright-MCP
  context during this analysis — which is also why the analyst verified the copied string by a
  real `Meta+V` paste into the list's `agent-search-input` instead).
- **Never call `readText()` directly** — use `_copy_link_via_menuitem()` from
  `test_pipeline_three_dot_menu_actions.py:44-65` (clear → click → wait for toast →
  `page.wait_for_function` poll → read). A direct call hung ~30 min on a permission prompt during
  ELITEA-2049's exploration.
- **New tab must be `page.context.new_page()`**, not `browser.new_page()` — the latter is an
  unauthenticated context (`test_agent_hub_copy_link_from_modal.py:121-123`).

## Resolved/added during ELITEA-1946 / ELITEA-1959 implementation (2026-08-24)

**Testids added** — EliteaAI/EliteaUI@2c4107b4 on `automation/testids` (one additive commit,
`ToolkitsControls.jsx` only; the shared hooks are untouched so no other caller changed):

| Testid | Was |
|---|---|
| `toolkit-actions-export-menuitem` | nothing at all (`useExportToolkitMenu()` supplies no `key`, and `DotMenu.jsx` wires `testId: item.key`) |
| `copy-link-toolkit-menuitem` | `Copy link-menuitem` — `useCopyLinkMenu()` defaults `key: key \|\| label`, leaking the visible label (space included) |
| `pin-toggle-toolkit-menuitem` | nothing (`usePinMenu()` accepts an optional `key`; this caller passed none) |

The compliant shape is naming the `key` **at the call site's items array** —
`{ ...pinMenuItem, key: 'pin-toggle-toolkit' }` — exactly as `SkillControls.jsx`
(`pin-toggle-skill`) and `CredentialsControls.jsx` (`pin-toggle-credential`) already do. Do NOT
add a `key` param to the shared hook for this: the call-site spread is smaller, scoped, and has
precedent. Not yet on `main` — awaiting a human cherry-pick.

**The controls menu unmounts behind MUI's close TRANSITION.** `DotMenu.jsx`'s `withClose` fires
on every item click, but a `controls_menu.count()` read in the click's own tick still returns
`1` — the first ELITEA-1959 run failed exactly there. Wait on the condition first:
`McpFormPage.wait_for_controls_menu_closed()` (`wait_for(state="detached")`), then assert
`count() == 0`. Same applies after `Escape`.

**The `/mcps/create` type-picker emits a React dev-mode console error on every mount** —
`Each child in a list should have a unique "key" prop` from
`src/[fsd]/shared/ui/category/CategorySection.jsx` via `ToolkitTypeSelector.jsx`. Already
tracked as [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656). Consequence for
any MCP test that seeds its own MCP through the UI create flow **and** asserts
`assert not console_errors`: register the console listener **after** setup, or the assertion
fails on scaffolding rather than on the surface under test. (Detail-page and deep-link flows
themselves were clean — 0 console errors across both cases.)

**Both cases green as written** — the analyst's menu inventory, `aria-disabled` states, exact
toast text (`The link has been copied to the clipboard.`), the `/{projectId}` clipboard URL
shape, the `ProjectSwitcher` strip on the deep-linked tab, and the pin → index-0 reorder all
reproduced first try under pytest.

---

## The MCP detail page has NO back button — it's a BREADCRUMB TRAIL now (2026-08-24, ELITEA-1961)

**Appended during ELITEA-1961 analysis, batch `mcp-w02`. Read this before writing any
"back button" / detail-to-list navigation assertion on ANY toolkit-family surface.**

`src/pages/Toolkits/EditToolkit.jsx:390-403` renders exactly one of two headers:

```jsx
{hasBreadcrumbTrail ? <Breadcrumbs /> : (<><BackButton /><Typography data-testid="toolkit-detail-title"/></>)}
```

`useHasBreadcrumbTrail()` (`src/[fsd]/shared/lib/hooks/useBreadcrumbTrail.hooks.js:35`) is
**purely route-based** — `resolveBreadcrumbTrail(pathname).length > 0` — and `/mcps/all/:id`
declares a trail (`src/[fsd]/shared/lib/constants/breadcrumb.constants.js:48`). So
**`<BackButton/>` is unreachable on this route no matter how the user arrived** (card click
and deep link both verified live). `document.querySelector('[data-testid="back-button"]')`
→ `null` on `/mcps/all/{id}`.

`toolkit-detail-title` still exists — but it now renders as the **last (non-clickable) crumb
inside the trail**, emitted from `breadcrumb.constants.js`, not from the `EditToolkit.jsx:398`
`<Typography>` (which is in the dead branch). Same testid, different owner.

| Handle | Testid | Notes |
|---|---|---|
| Breadcrumb nav (detail pages ONLY) | `breadcrumbs` | `<nav>`, text `MCPs/{name}`. **Absent on `/mcps/all`** — a clean detail-vs-list discriminator. On `main` ✓ |
| Parent crumb link | `breadcrumb-item` | `<a>`, text `MCPs`. Exactly **1** on the MCP detail page — assert `to_have_count(1)` before reading. Clicking it navigates to `/mcps/all` client-side. On `main` ✓ |
| Current crumb | `toolkit-detail-title` | last crumb, not a link. On `main` ✓ |

Breadcrumbs are recent — `breadcrumb.constants.js` was last touched on `main` by `1facc163`
(`feat: [EL-6293] dedicated index search page`, 2026-08-21), same redesign era as EL-6277.
Filed as CLARIFICATION [#1731](https://github.com/EliteaAI/elitea-testing-public/issues/1731)
against ELITEA-1961's step 3/4 text. **No page object binds `breadcrumbs`/`breadcrumb-item`
yet** — ELITEA-1961's AFS specs them onto `McpFormPage`.

## MCP list state across a detail round-trip: filter SURVIVES, scroll does NOT (2026-08-24)

Measured live, twice, two different search terms:

| List state | Survives detail → back? | Mechanism |
|---|---|---|
| Search filter (term + filtered card set) | **YES ✅** | the term lives in the redux slice `src/slices/search.js` (in-memory). Survives a client-side route change; would **NOT** survive a `page.reload()`. |
| Scroll position | **NO ❌** | `#EliteACustomTabPanel` `scrollTop` 99 → 0 on return, still 0 at +2 s. No list scroll-restoration code exists anywhere in `src/` — never implemented, not regressed. |

Two consequences for anyone writing a list-page assertion here:

1. **The filter is NEVER in the URL.** `/mcps/all` carries no query string while filtered
   (verified). Read the filter from `agent-search-input`'s value + the rendered card set,
   never from `location.search`.
2. **Never `reload()` mid-flow** in a case that depends on the filter surviving — the redux
   store dies with the page and the filter silently resets.

The scroll half is CLARIFICATION
[#1732](https://github.com/EliteaAI/elitea-testing-public/issues/1732) (case-text vs product
scope, human ruling pending). ELITEA-1961's AFS deliberately asserts it in **neither**
direction: asserting preservation reverse-masks, asserting reset-to-0 cements a possibly
unintended behaviour, and the scroller carries an `id` not a `data-testid` (so asserting it
at all would need a blanket-add on an element no case touches).

**List-page baseline (project 399, 2026-08-24):** 19 MCPs, card view default, scroller
`scrollHeight` 900 vs `clientHeight` 801 at 1920×1080 — i.e. only **~99 px** of scroll range.
Any future scroll-dependent case must assert `scrollHeight > clientHeight` first or seed more
MCPs; at a smaller card count the list does not scroll at all and the observable is vacuous.

## MCP DETAIL page top-left control is a BREADCRUMB, not a back arrow (ELITEA-1961, 2026-08-24)

**Resolved/added during ELITEA-1961 implementation** (analyst-discovered, confirmed
green in the automated flow). Read this before writing any "back to the list"
assertion on `/mcps/all/:id`.

`EditToolkit.jsx:390-403` renders `hasBreadcrumbTrail ? <Breadcrumbs/> :
(<BackButton/> + <Typography data-testid="toolkit-detail-title"/>)`.
`useHasBreadcrumbTrail()` is **purely route-based** and `/mcps/all/:id` declares a
trail (`breadcrumb.constants.js:48`), so the `<BackButton/>` branch is **unreachable
on this route no matter how the user arrived** (card click or deep link). Case-text
drift, not a defect — CLARIFICATION #1731.

| Handle | Testid | Notes |
|---|---|---|
| Breadcrumb nav (detail only) | `breadcrumbs` | on `main` ✓ (`shared/ui/breadcrumbs/Breadcrumbs.jsx:20`). `<nav>`; `text_content()` concatenates to `MCPs/{name}` with no separating whitespace. **Absent on `/mcps/all`** — the cleanest detail-vs-list discriminator. |
| Parent crumb link | `breadcrumb-item` | on `main` ✓ (`BreadcrumbItem.jsx:30`). `<a>` reading `MCPs`; exactly **one** renders on the MCP detail page — assert count-then-text, not `.first`. |
| Back arrow | `back-button` | on `main` ✓ but **count 0 on this route** — bind it only for the absence assertion. |

Bound on `McpFormPage` as `breadcrumbs_nav` / `breadcrumb_parent_link` /
`back_button` + `get_breadcrumb_text()` / `click_breadcrumb_parent()`. Kept on
`McpFormPage` rather than promoted to `BasePage`: the trail is app-shell and a
future cross-surface case may want it there, but promoting now would bind a testid
no other current spec touches (#511 scope rule).

### List filter state survives the round trip; scroll position does NOT

- The list's search filter lives in **redux** (`src/slices/search.js`), in-memory and
  **not in the URL** — `/mcps/all` carries no query string while filtered. It survives
  a client-side route change (which is exactly why the detail→list round trip keeps the
  filter) but would NOT survive `page.reload()`. Never reload mid-flow, never read the
  filter off the URL.
- **Scroll position is not restored** (`scrollTop` 99 → 0; no list scroll-restoration
  code exists anywhere in `src/`). ELITEA-1961 deliberately asserts it in **neither**
  direction — CLARIFICATION #1732 is open for a human ruling.
- Proving the breadcrumb navigates **client-side** needs no `page.evaluate`: a full
  document load fires Playwright's page `"load"` event and an SPA route change does
  not, so watching for that event's ABSENCE across the click is an honest,
  product-produced signal.

## MCP DASHBOARD — "Types" filter panel (Local / Remote) — added 2026-08-24

**Appended during the ELITEA-1942/1943 cluster analysis (batch `mcp-w03`).
Verified live on `/mcps/all`, project 399, 19 MCPs (all Remote).**

| Handle | Testid | Provenance (fetched 2026-08-24) | Notes |
|---|---|---|---|
| Type filter chip (dynamic) | `tags-panel-chip-{TypeName}` → `…-Local`, `…-Remote` | **on-main ✓** | `components/Categories.jsx:336`. Shared with the Credentials Types panel — `CredentialsListPage.TYPE_FILTER_CHIP` is the same constant. |
| "Clear all" | `tags-panel-clear-all` | **on-main ✓** | `Categories.jsx:299`. Rendered ONLY while ≥1 chip is selected ⇒ **its presence is the product's own "a filter is active" signal**; unmounted (not hidden) when nothing is selected → `to_have_count(0)`. |
| Card type badge, page-wide collection | `entity-card-tag-chip` | on-main ✓ | `McpListPage` today only has the per-card **scoped** `CARD_TAG_CHIP_SELECTOR`; a page-wide `LocatorDescriptor` + `get_visible_type_badges()` is needed for filter assertions — copy `credentials_list_page.py:~487`. |

**Mechanics (source-confirmed, `[fsd]/features/toolkits/lib/hooks/useLoadToolkits.hooks.js`):**

- The MCP Types chip list is **HARDCODED to exactly `Local` + `Remote`**
  (`tagList`, `isMCP` branch, ~lines 181-198) — it is NOT data-derived. Both
  chips always render, whatever the project holds. (Credentials' panel *is*
  data-derived — do not carry that assumption across.)
- Selecting a chip is **URL-driven**: `useTypes` pushes `?tags[]=<Name>`
  (`replace: true`) and the list re-queries. Selected state lives ONLY in an
  emotion CSS class hash (`css-1oy09ev` selected vs `css-16qy5qb` idle) —
  **no `aria-selected`, no `data-*` attribute**. Never bind to the class.
  Assert "a filter is active" via the URL param + `tags-panel-clear-all`.
  (Known gap: a `data-selected` attribute on `StyledChip` would be the policy
  shape if a case ever needs to prove *which* chip is lit; not needed yet.)
- Filtering is **server-side**: Remote ⇒ `GET …/tools/prompt_lib/{project}?…&toolkit_type=mcp`.
  (Contrast: the search box on the same page filters **client-side** —
  ELITEA-1941.)
- **The chips mount AFTER the page's load signal.** `McpListPage.navigate()`
  waits on the card-view toggle, at which point `tags-panel-chip-Remote` is
  still absent (a click there fails with "does not match any elements",
  observed live). Wait for the chip itself.
- Re-clicking a selected chip deselects it; `tags-panel-clear-all` clears all.
  Both verified to restore the full list.

**⚠ Product defect #1737 (OPEN, filed 2026-08-24) — the `Local` chip does not
filter.** `selectedMcpTypes = rows.filter(t => t !== 'mcp')` is `[]` when the
project has no pre-built `mcp_*` type, and an empty type set is treated as
"no filter" ⇒ the list query goes out with **no `toolkit_type` at all** and
every Remote MCP stays on screen while the Local filter is visibly active.
Reproduced 2/2 including a pristine `goto('/mcps/all?tags[]=Local')`.

**⚠ Environment fact — there are NO Local MCPs and none can be created here
(question #1738).** `GET /toolkit_types/prompt_lib/{project}?mcp=true` →
`{"rows": ["mcp"], "total": 1}`; `/mcps/create` offers exactly one type card
(`toolkit-type-card-mcp`, "Remote MCP"). Any case text naming ADO /
FileSystem / PlaywrightMCP as available Local MCPs is unsatisfiable in this
environment — check this before planning such a case.

**Resolved/added during ELITEA-1942 implementation (2026-08-24, implementer):**
every handle above worked verbatim — no testid was added for this case.
Three implementation-time facts the analyst pass could not see:

- **Settle signal for a chip click is the list GET's `toolkit_type=` param.**
  `McpListPage._expect_list_response(action, filtered=…)` awaits
  `/tools/prompt_lib/{project}` GET whose URL either contains `toolkit_type=`
  (select) or does not (deselect / Clear all). Both fire reliably; no sleep is
  needed anywhere in the flow.
- **The restored list renders a tick AFTER the unfiltered GET resolves** — a
  synchronous `get_card_names()` right after the response can read an empty
  grid (the same race `CredentialsListPage._settle_unfiltered_list` documents).
  `McpListPage._settle_restored_list()` (network + first card visible) is the
  fix; `remove_type_filter()` / `clear_all_type_filters()` call it for you.
- **`page.url` percent-encodes the param** — it reads `tags%5B%5D=Remote`, so
  assert on `urllib.parse.unquote(page.url)` containing `tags[]=Remote` rather
  than on the raw string.

New `McpListPage` members (all testid-only, all additive): `TYPE_FILTER_CHIP`,
`tags_clear_all_button`, `entity_card_tag_chip`, `type_filter_chip()`,
`wait_for_type_panel()`, `click_type_filter()`, `remove_type_filter()`,
`clear_all_type_filters()`, `is_type_filter_active()`,
`get_visible_type_badges()`.

---

## MCP LIST card pin/unpin + type-filter counts (2026-08-24)

**Appended during ELITEA-1945 / ELITEA-1958 cluster analysis, batch `mcp-w03`.** All observed
live against `http://localhost:5173/mcps/all`, project 399 (19 MCPs, all Remote, none pinned
before and after the run).

### Card pin toggle — `mcp-pin-toggle-button-{id}`

| Fact | Detail |
|---|---|
| Provenance | **on `main` ✓** — `origin/main:src/[fsd]/widgets/pin-toggler/ui/PinButton.jsx:98` (verified after `git fetch origin`, 2026-08-24) |
| State read | `aria-label` = `Pin to top` / `Unpin from top` (testid stable, state in the attribute) |
| **Hover-reveal** | **The button renders at `opacity: 0` until the card is hovered** (`pointer-events: auto` throughout, so a click works unhovered). ⚠️ Playwright's visibility definition ignores `opacity`, so `to_be_visible()` passes on an invisible control — assert `to_have_css("opacity","1")` after an explicit hover when a case says "the button is visible". |
| Tooltip | MUI `role="tooltip"` appears on hover carrying the same text (`Pin to top` → `Unpin from top`). **No testid, and none should be added** (#511) — `aria-label` is the testid-anchored equivalent. |
| Pin | `POST /api/v2/social/pin/prompt_lib/{project}/toolkit/{id}` → **201**; card jumps to index 0 **immediately, client-side** (observed 18 → 0, no reload, no list re-fetch). |
| Unpin | `DELETE` same path → **204**; label flips back instantly **but the list does NOT re-sort** — the card stays at index 0 until the next list fetch. After `page.goto('/mcps/all')` the original order returns byte-identical. Case-text gap filed as clarification **#1740**. |
| Vacuity trap | Default sort is newest-first, so a freshly created MCP is already index 0. A pin test must seed **two** MCPs (A then B) and pin **A**, asserting `index(A) < index(B)` afterwards. |
| Hygiene | The merged `test_mcp_three_dot_menu_actions.py` asserts "no MCP is pinned" as its own precondition — **never leak a pin**, and assert the same guard before pinning (a stray pin sits at index 0 and breaks the "moved to top" read for an unrelated reason). |
| Page object | `McpListPage.PIN_TOGGLE_BUTTON` + `get_pin_toggle_label(mcp_id)` already exist; a `click_pin_toggle(mcp_id)` returning the awaited pin/unpin `Response` is the missing piece (mirror `McpFormPage.click_pin_toggle_menu_item()`). |

**Added during ELITEA-1945 implementation (2026-08-24, PR against `tests/batch-mcp-w03`):**
`McpListPage` now carries the full card-pin vocabulary — `pin_toggle_button(mcp_id)` (Locator,
mirrors `CredentialsListPage`/`PipelinesListPage`), `hover_pin_toggle(mcp_id)`,
`click_pin_toggle(mcp_id) -> Response` (awaits the `/social/pin/…/toolkit/{id}` round trip),
`wait_for_pin_toggle_label(mcp_id, expected)` (retrying `aria-label` assertion — the flip lands a
render tick after the response), `wait_for_card_at_top(name)` (the pin's client-side re-sort is
immediate but one tick late), and `get_all_pin_toggle_labels()` off a new
`PIN_TOGGLE_BUTTON_ANY = '[data-testid^="mcp-pin-toggle-button-"]'` class constant, which is how
the "nothing is pinned" precondition guard is asserted without a raw handle. Everything the digest
predicted held live first run: 201/204, immediate pin re-sort, unpin non-re-sort, byte-identical
restored order after `navigate()`, 0 console errors. No new testids were needed.

### Type-filter counts — #1737 re-reproduced (3rd time)

| Filter | Cards | Badge set | List request |
|---|---|---|---|
| none | 19 | `{Remote}` | `…/tools/prompt_lib/399?query=&sort_by=created_at&sort_order=desc&mcp=true&limit=20&offset=0` |
| Remote | 19 | `{Remote}` | same **+ `&toolkit_type=mcp`** |
| **Local** | **19** | **`{Remote}`** | **byte-identical to unfiltered — no `toolkit_type` at all** |

So the count identity ELITEA-1958 asserts (`total == Remote + Local`) reads **19 == 19 + 19**
live. ELITEA-1958 is **blocked** on #1737 (product) + #1738 (no Local MCP exists in DEV, now
gating three cases). Occurrences were commented onto both existing issues; nothing re-filed.
`tags-panel-clear-all` is a verified equivalent to re-clicking the chip for clearing (2/2).

### Console

0 errors on `/mcps/all` across the whole pin/unpin flow *and* the whole filter flow. The known
`/mcps/create` React key warning (#656) is the only reason to scope a console listener — register
it **after** any UI-create seeding.

---

## MCP **type picker** (`/mcps/create`) — sections, Documentation link, filter chips (2026-08-24)

**Appended during the ELITEA-1948/1949 cluster analysis, batch `mcp-w03`.** Verified live
on `http://localhost:5173/mcps/create`, project 399. **Do NOT confuse this surface with the
MCP dashboard "Types" panel** (§ MCP DASHBOARD above) — different component, different
testids, different mechanics.

| Surface | Component | Chip testid | Filtering |
|---|---|---|---|
| `/mcps/all` dashboard | `components/Categories.jsx` | `tags-panel-chip-{Type}` | **server-side** (`?tags[]=`, `toolkit_type=`), has `tags-panel-clear-all` |
| `/mcps/create` type picker | `[fsd]/shared/ui/filter/CategoryFilter.jsx` | **`category-filter-tab` — shared by BOTH chips, non-unique** | **pure client-side re-grouping, NO network request**, no "clear all" |

### Confirmed handles on this surface

| Element | Testid | Provenance (fetched 2026-08-24) |
|---|---|---|
| Local empty-state message | `mcp-type-picker-local-empty-state` | **on-main ✓** (`ToolkitTypeSelector.jsx:176`) |
| Remote MCP type card | `toolkit-type-card-mcp` | **on-main ✓** (runtime-composed ``toolkit-type-card-${itemKey}``, `CategoryItemCard.jsx:14` — bare-string grep says "no", the template is there) |
| No-results title / description | `catalog-no-results-title` / `catalog-no-results-description` | **on-main ✓** (`NoResultsMessage.jsx`) |

### Testid GAPS on this surface (work orders in ELITEA-1949's AFS, not waivers)

| Element | Recommended name | Where |
|---|---|---|
| Heading `Choose the MCP type` | `mcp-type-picker-heading` | `CategoryFilter.jsx:33-39` — shared ⇒ add a `titleTestId` prop, plumb through `GroupedCategory.jsx` exactly as `searchInputTestId` already is, pass only when `isMCP` |
| Filter chips | `mcp-type-picker-filter-chip-local` / `-remote` **+ `data-selected`** | `CategoryFilter.jsx:66-81` — **mirror the sibling `CategoryRail.jsx:5-30`**, which already has `chipTestIdPrefix` + `slugifyCategory()` + `data-selected`. Keep `category-filter-tab` as the no-prefix fallback (other surfaces use it) |
| Documentation link | `mcp-type-picker-local-documentation-link` | `ToolkitTypeSelector.jsx:179-186` — our own JSX, direct attribute |

Chip selection state today lives **only** in an emotion class hash (`css-5yxssv` selected
vs `css-1n8j5hf` idle) / computed `background-color` — never bind to either.

**Resolved/added during ELITEA-1949 implementation (2026-08-24):** all three testids above
are now on `automation/testids` — EliteaAI/EliteaUI@f4ce7128 (the props + the doc link) and
EliteaAI/EliteaUI@989db4f0 (the scoping fix below). Not yet on `main`. Chip selection is now
readable as `data-selected="true|false"` on the chip's own testid, so the emotion-class
warning above is no longer a constraint on this surface — page-object handles:
`McpFormPage.type_picker_heading`, `.local_documentation_link`, `.no_results_title`,
`.no_results_description`, and the `TYPE_FILTER_CHIP` / `TYPE_FILTER_CHIP_SELECTED` class
constants with `type_filter_chip()` / `click_type_filter()` / `is_type_filter_selected()`.

**Trap the work order did not see — `ToolkitTypeSelector` has TWO call sites.** It is
rendered by the standalone `/mcps/create` page (`src/pages/Toolkits/CreateToolkit.jsx`) **and
by the in-chat MCP canvas** (`src/[fsd]/features/chat/ui/editors/ToolkitEditor.jsx:304`), and
both pass `isMCP`. Putting `chipTestIdPrefix={isMCP ? … : undefined}` inside
`ToolkitTypeSelector` therefore also renames the CANVAS chips, breaking the two merged specs
that bind `category-filter-tab` there (`tests/ui/chat/test_create_mcp_from_conversation.py`,
`…_discard_changes.py`, via `McpFormPage.select_remote_category_tab`). The shipped shape
hoists both props to the `CreateToolkit.jsx` call site; `ToolkitTypeSelector` only forwards
them. Anything else added to this surface's shared components must make the same check —
both chat specs re-ran green after the fix.

### Behaviours confirmed live

- **The chips are MULTI-SELECT** and there is no clear-all. Clicking `Local` then `Remote`
  leaves *both* lit. Re-clicking a lit chip deselects it.
- **⚠️ Selecting `Local` unmounts the Local section entirely** — heading, empty-state
  message and Documentation link all vanish, replaced by `No MCPs found` /
  `Try adjusting your search terms`. Source: `ToolkitTypeSelector.jsx` passes
  `allowEmptyCategory={isMCP}` and `GroupedCategory.jsx:56-62` keeps an empty category
  **only while `!selectedCategories.length`**. So the Local placeholder is an
  *unfiltered-view* affordance. Filed as clarification **#1742** (`question` +
  `case-text-drift`) — NOT a bug, and a sibling of (not a duplicate of) the dashboard
  bug #1737.
- Selecting `Remote` (alone or alongside `Local`) renders the single `Remote` section with
  `toolkit-type-card-mcp`.
- `toolkit-type-card-mcp` mount delay reconfirmed — framework auto-waiting only.
- **Console:** exactly one error on this route, the known #656 React `key` warning from
  `CategorySection.jsx` via `ToolkitTypeSelector.jsx`. Nothing else, including across both
  filter clicks.

---

## MCP DETAIL — Form ⇄ Raw Json is a live two-way projection (2026-08-24, ELITEA-1948)

**Appended during the ELITEA-1948/1949 cluster analysis, batch `mcp-w03`.** Verified live on
toolkit **3134** (`autotest_conn_tools_a1`). Nothing was persisted — the whole flow issued
**zero** `PUT`/`POST`/`PATCH`/`DELETE`.

- **The two views SWAP, they do not co-exist.** After `switch_to_raw_json_view()`,
  `toolkit-form-name-input` is **unmounted** (`to_have_count(0)`, not hidden), and vice
  versa. State reads on the toggles use `aria-pressed` (`toolkit-form-view-toggle` /
  `toolkit-raw-json-view-toggle`) — attribute on the testid'd element, compliant.
- **An unsaved Raw-Json edit reaches the Form view immediately** (no save, no reload) and
  survives a round trip back to Raw Json. Both Save and Discard flip to **enabled** the
  moment the edit lands — the product's own proof the edit entered the shared Formik model
  rather than just the CodeMirror buffer.
- **A view switch RE-SERIALISES the JSON from the form model.** Observed 30 → 29 → 30 lines
  across edit → Form → Raw Json → discard: CodeMirror's auto-indent artefact from a
  per-line edit is normalised away. ⇒ **assert on the parsed value**
  (`json.loads(get_raw_json_full())["description"]`), never on raw line text.
- **`description: null` in the JSON ⇄ `""` in the Form input.** An absent description
  serialises as `null`. Seed a NON-EMPTY description when a case needs "reverts to the
  original value" to be a real observable.
- **Discard reverts BOTH views** (after the modal confirm, § MCP DETAIL page: Discard is
  CONFIRMED through a modal): the editor goes back to `"description": null,`, the Form
  input to `""`, Save + Discard back to disabled, and **the active view does not change**
  (still Raw Json, `aria-pressed="true"`).
- **The `.fill()` trap reconfirmed the hard way this session:** Playwright MCP's
  `browser_type` maps to `locator.fill()`, which replaced the entire 30-line document with
  one line (invalid JSON, Save stays disabled, only a reload recovers). Per-line editing
  only — click the `.cm-line`, `End`, `Shift+Home`, `keyboard.type(...)`. In-repo:
  `McpFormPage.fill_raw_json_line()`.
- **Case-text gap:** ELITEA-1948's step 9 omits the Discard confirmation modal, exactly as
  ELITEA-1928's step 5 did. **Third case to hit it** — occurrence commented on the existing
  clarification **#1718**; nothing re-filed.

## Timeout / Cache TTL numeric fields — defaults, value TYPE asymmetry, info icon (2026-08-24, ELITEA-1956/1957)

**Appended during the ELITEA-1956/1957 cluster analysis (batch `mcp-w04`). Confirmed live
on a freshly seeded Remote MCP (toolkit 3247, `https://mcp.example.com/sse`).**

- **Defaults are real input VALUES, not just placeholders.** Both `toolkit-field-timeout-input`
  and `toolkit-field-cache_ttl-input` read `input_value() == "300"` on the create form AND on
  a freshly created MCP's detail page. They *also* carry `placeholder="300"` (derived from the
  schema default at `ToolBaseProperty.jsx:592-596`, `placeholder = schemaPlaceholder ||
  (isInteger && defaultValue !== undefined ? String(defaultValue) : undefined)` with
  `value={settings[k] ?? ''}`) — so a *genuinely empty* field would still show "300" greyed
  out. **Assert `input_value()`, never the placeholder.**
- **Value TYPE asymmetry — the one thing to know here.** An **untouched** default persists as a
  JSON **number**; a value **typed in the UI** persists as a JSON **string**:

  | State | `settings.timeout` | `settings.cache_ttl` |
  |---|---|---|
  | freshly created, untouched | `300` (int) | `300` (int) |
  | after typing 60 into Timeout | `"60"` (str) | `300` (int) — untouched sibling stays numeric |
  | after typing 600 into Cache TTL | `"300"` (str, from a prior edit) | `"600"` (str) |

  Same in the create POST body, the update PUT body and the Raw Json view. This is why
  merged `test_mcp_create_remote.py:196-199` asserts `== "600"` + `isinstance(..., str)`.
  TMS case texts (ELITEA-1956/1957) print bare numbers — that is **case-text drift**, not a
  defect. Assert with `str(raw["settings"][k]) == "<value>"`.
- **Round-trip confirmed both directions**: 300 → 60 → 300 (Timeout) and 300 → 600 → 300
  (Cache TTL), each with a PUT 200, each surviving `page.reload()`. Editing one field never
  touched the other.

### The label info icon has NO testid (work order, not a waiver)

Live DOM inside each field's `<label>`:
`<span data-info-tooltip="true"><svg width="16" height="16" …/></span>` — one SVG, **zero
`data-testid`** on `timeout`, `cache_ttl`, `url` (checked all three).

The plumbing is fully wired already — `ToolBaseProperty.jsx` → `Input.StyledInputEnhancer`
→ `InputBase` → `InfoTooltip`, and `InfoTooltip` accepts `testId` / `contentTestId`.
`ToolBaseProperty.jsx:615-618` already passes them, but **only for `k === 'bucket'`**
(`toolkit-field-bucket-info-icon`, already on `origin/main`). Adding an info-icon testid for
any other field = extend that per-key allow-list with two additive props. Do **not** make it
generic (blanket-add ban, `.agents/testing.md` § Locator policy) and do **not** add the
`-info-tooltip-content` sibling unless a case actually opens the tooltip (#511).

### Two traps this session

1. **`McpFormPage.is_save_button_disabled()` binds the CREATE form's
   `toolkit-form-save-button`** — it does not exist on the detail page, so calling it there
   times out after 30 s with a misleading "waiting for get_by_test_id(...)". On the detail
   page read `detail_save_button.is_disabled()` directly. (Pristine detail page: `true`;
   after touching one field: `false` — consistent with the Save/Discard gating section above.)
2. `expand_configuration_section()` is required **again after every `page.reload()`** — and
   again after `switch_to_form_view()` coming back from Raw Json.

### Console was clean

Zero `error`-type console messages across both full flows (seed → edit → save → reload →
Raw Json → restore, twice), headless, fresh context — including the `#291` React dev-mode
warnings and the `#549` MUI-Tabs warning that `test_mcp_edit_toggle_enable_caching.py` still
filters/soft-fails. **Not evidence they are fixed** (different render path / headless), but
worth re-checking the next time someone touches those filters.


### Resolved/added during ELITEA-1956/1957 implementation (2026-08-24, implementer)

- **The info-icon testid gap above is CLOSED.** `toolkit-field-timeout-info-icon` and
  `toolkit-field-cache_ttl-info-icon` now exist — EliteaAI/EliteaUI@25c47d7d on
  `automation/testids` (NOT yet on `main`: a human cherry-picks). Shipped as a second
  per-key spread beside the pre-existing `bucket` one in
  `ToolBaseProperty.jsx`, passing only `tooltipTestId`. Bound as
  `McpFormPage.timeout_info_icon` / `McpFormPage.cache_ttl_info_icon`. The same one-line
  pattern is now the proven recipe for any other schema field's info icon.
- **`save_and_wait_for_updated()`'s returned PUT body carries the full `settings` object**
  — `save_response["settings"]["timeout"]` is directly assertable, no extra GET needed
  (used for both the save and the restore step). A UI-typed value comes back as a JSON
  STRING there too, matching what Raw Json renders.
- **Console stayed clean again** across both parameterized rows (headless): zero
  error-type messages, so neither the `#291` filter nor the `#549` soft-fail branch fired.
  Still not evidence they are fixed.
- **Both rows ran green first try, 61.7 s for the pair** (seed → edit → save → reload →
  Raw Json → restore → API delete, twice), no reruns.

## Create form: CANCEL is a two-step gesture with its own confirm dialog (ELITEA-1960, 2026-08-24)

**Appended during ELITEA-1960 analysis (batch `mcp-w04`).** Distinct from the *detail*
page's Discard modal documented above — different component, different testids, same shape.

`CreateToolkitToolTabBar.jsx` renders the create form's Cancel as a shared
`Button.DiscardButton title="Cancel"`, so clicking it **cancels nothing**: it only opens

```
Warning
Are you sure you want to cancel creation of this toolkit?
Cancel   Discard
```

The form stays mounted and keeps both field values until the modal's own **Discard** is
clicked. All three handles are **on `origin/main` ✓** (EliteaAI/EliteaUI@bf4a13ad) —
nothing to add.

| Handle | Testid | Notes |
|---|---|---|
| Cancel button (create form) | `toolkit-form-cancel-button` | label exactly `Cancel`; enabled whenever `!isLoading` |
| Cancel-confirm dialog | `toolkit-form-cancel-confirm-dialog` | lands on the MUI `Dialog` **root** (`role="presentation"`) → `text_content()` == `WarningAre you sure you want to cancel creation of this toolkit?CancelDiscard`. **Assert with `in`, never `==`** |
| Cancel-confirm "Discard" button | `toolkit-form-cancel-confirm-button` | label exactly `Discard` |

### What confirming actually does — no navigation, no URL change

`onCancel` → `setWantToCancel(true)` → effect calls `onClearEditTool()` + `formik.resetForm()`.
At the MCP call site `onClearEditTool` is `() => setEditToolDetail(null)` (`CreateToolkit.jsx:141`)
— **pure component state; there is no `navigate()` anywhere in the cancel path.** Live result:

- every create-form handle **unmounts** (`toolkit-form-name-input`, `-description-input`,
  `toolkit-field-url-input`, `toolkit-form-save-button`, `toolkit-form-cancel-button` → count 0);
- the **type picker re-renders** (`mcp-type-picker-heading` == `Choose the MCP type`,
  `toolkit-type-card-mcp` present);
- the **URL stays `/mcps/create/mcp`** — it does NOT return to `/mcps/create`.

⇒ Assert the view (unmount + picker heading), **never the URL**. Filed as clarification
[#1747](https://github.com/EliteaAI/elitea-testing-public/issues/1747).
Zero `POST` fires anywhere in the flow — a cancelled creation is server-side inert.

### ⚠️ The MCP type picker emits a console ERROR on every mount (#656) — and a cancel flow mounts it TWICE

`CategorySection.jsx:35` via `ToolkitTypeSelector.jsx:36` logs React's
`Each child in a list should have a unique "key" prop` at **error** level on every
type-picker mount ([#656](https://github.com/EliteaAI/elitea-testing-public/issues/656)).
`test_mcp_back_navigation.py` dodges it by registering its listener after setup — a cancel
flow **cannot**, because returning to the picker IS the observable. Any console assertion on
this surface must **filter that signature by message** (plus the standing `socket.io`
CORS/502/503 noise to `dev.elitea.ai`), not drop the assertion and not run it unfiltered.

### Handle gotcha worth remembering

`toolkit-field-url-input`'s testid sits on the `<input>` **itself** — `[data-testid="toolkit-field-url-input"] input`
matches nothing. (`toolkit-form-name-input` is the opposite: wrapper, real input inside.)
