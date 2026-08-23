# Surface digest — Remote MCP (`/mcps/...`)

> Handle cache from live exploration. Verify each handle as you use it — this
> is a cache, not a source of truth. Last updated: 2026-08-02 (ELITEA-1934 /
> ELITEA-1937 implementer session, fix round 2 — testid gaps resolved via
> `add-data-testid`; originally created 2026-08-01, analyst session, cluster
> dispatch, `approved-top10` batch). **Appended 2026-08-24 during
> ELITEA-1923/1924 combined analysis+implementation** — create-form validation
> handles + the Save-button gating mechanism (see the two new sections at the
> end).

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
| Connection-status indicator ("Not Connected"/"Connected!") | `toolkit-connection-status` | `McpAuthStatus.jsx`, wrapping `Typography` — added via `add-data-testid` for ELITEA-1934 (2026-08-02). Live on `automation/testids` (EliteaUI@a467c0ac); **not yet on `main`** — human cherry-pick pending, see PR closure record. |
| Error toast (mcp_sync_tools failure) | `toast-message` | reuses the existing app-wide `Toast.jsx` component (same as `artifacts_page.py`/`skills_list_page.py`/`skill_detail_page.py`) — confirmed live, no new testid needed. Already on `main`. |
| Model selector NAME (not the button) in Test Settings panel, `variant="field"` branch | `model-selector-name` | `LLMModelSelector.jsx` — now applies in the `"field"` branch too (previously `"default"`-only), fixed via `add-data-testid` for ELITEA-1937 (2026-08-02), scoped to only this testid since that's the one ELITEA-1937's test reads. Live on `automation/testids` (EliteaUI@a467c0ac); **not yet on `main`**. |

## Confirmed testid GAPS (flag to `add-data-testid`, don't build raw fallbacks into new code without a stop+flag reason)

| Element | Where | Recommended name | Issue |
|---|---|---|---|
| Model selector BUTTON (trigger) in Test Settings panel, `variant="field"` branch | `LLMModelSelector.jsx` — `data-testid="model-selector-button"` still only applies in the `variant="default"` branch, NOT `"field"` (the one actually rendered here) | reuse the existing `model-selector-button` string, extend it into the `"field"` branch (same pattern `model-selector-name` just followed) | **#1088 — OPEN, confirmed regression on already-merged ELITEA-1866**: `toolkit_test_settings_page.py`'s `model_selector_button` `LocatorDescriptor` is asserted at ELITEA-1866 step 25 and is CONFIRMED red against the `approved-top10` batch trunk (re-run 2026-08-02) for exactly this reason — pre-existing, not introduced by ELITEA-1934/1937's PR. Needs a dedicated `add-data-testid` + `adjust-automated-test` fix on the ELITEA-1866 spec. |

Two of the three gaps found during the ELITEA-1934/1937 analysis session
(connection-status indicator, error toast) are fully resolved — see
Confirmed-stable handles above. The third (`model-selector-name`/`-button`
pair, #1088) is only half-resolved: `model-selector-name` is fixed and in
Confirmed-stable handles; `model-selector-button` is still open, listed here.

## State machine — `TestTools.jsx` (governs BOTH Remote MCP and Artifact toolkit Test Settings panels — same shared component)

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
