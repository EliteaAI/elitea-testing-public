# Test Case: Edit Remote MCP — Toggle Enable Caching

## Metadata
- **TMS ID**: ELITEA-1929
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `priority: critical`; case body text itself
  says "**Priority:** medium" — a pre-existing internal inconsistency in the
  source case file, not introduced by this analysis; the frontmatter (`critical`)
  is treated as authoritative per the dispatch instruction, hence `l1`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`
  auto-auths the dev server, confirmed "Elitea is connected" in the sidebar
  after page load)
- **Analyst**: qa-engineer (agent), session 2026-07-16
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (on localhost this is automatic via `VITE_DEV_TOKEN`; on
  deployed envs, standard Keycloak login via `${TEST_USER}`).
- Project context is set (sidebar shows `Project: <name>`; project id read from
  `${ELITEA_PROJECT_ID}`).
- At least one Remote MCP toolkit must already exist in the project and be
  reachable at its detail page (`/mcps/all/{id}`), with "Enable Caching" checked
  by default. **Confirmed live**: the project already had 6 pre-existing Remote
  MCPs (leftovers from prior manual/automated exploration sessions) — this case
  reused `autotest_remote_mcp_full` (toolkit id `1244`, the same toolkit created
  during the ELITEA-1922 AFS session) rather than creating a new one. If the
  project is ever empty, seed one via the existing `McpFormPage` create flow
  (see `test_mcp_view_toggle.py`'s `_seed_mcp_via_ui` helper) — Enable Caching
  defaults to checked on creation, matching this case's precondition.

## Test Data

> **Amended by implementer** (fix-only round R1, PR #548, 2026-07-16): this
> section originally classified the Remote MCP toolkit as `reuse-existing`
> (id `1244` / `autotest_remote_mcp_full`), matching the analyst's live
> session. During implementation, `ToolkitAPI.list_all_toolkits()` — the API
> the harness would need to rediscover `1244` (or any) toolkit id at test
> runtime without hardcoding a leftover manual-session id — returns an empty
> list on this environment regardless of auth method (same documented quirk
> as `config.py`'s `remote_github_mcp_toolkit_id` comment and
> `.agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md`).
> With no reliable read-only way to rediscover an existing Remote MCP's id at
> runtime, the implementer used the seed-and-teardown variant this AFS's own
> § Cleanup (option 3, below) already anticipated as a safe alternative —
> reclassifying the toolkit from `reuse-existing` to
> `generate-shared-with-cleanup` for automation purposes. No case behavior or
> assertion changed; toggling Enable Caching has no destructive effect on the
> toolkit's other fields either way.

### generate-shared-with-cleanup
- An MCP toolkit is created per test run via the existing `McpFormPage`
  create flow (same helper pattern as `test_mcp_view_toggle.py`'s
  `_seed_mcp_via_ui`) and torn down via `ToolkitAPI.delete_toolkit()` in a
  `finally` block. Enable Caching defaults to checked on creation
  (AFS-confirmed live), matching this case's stated precondition, so no
  additional setup is needed before Step 1.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (from `.env.test`, confirmed live via the
  sidebar's project textbox).

## Test Steps

1. Navigate to `${BASE_URL}/mcps/all/{toolkit_id}` for an existing Remote MCP
   (localhost: `APP_PREFIX` is empty, no `/app` prefix). Wait for the detail GET
   (`GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`) to
   resolve and the Form view to render real data (not the "Edit Toolkit"
   placeholder).
   - **Verify**: page loads in Form view (`toolkit-form-view-toggle` pressed);
     `toolkit-detail-title` shows the toolkit's name.
2. Read the Enable Caching checkbox state
   (`toolkit-field-enable_caching-checkbox-field`).
   - **Verify**: `input.checked === true` (confirmed live default for this
     toolkit — matches the case's stated precondition "checked by default").
3. Click the Enable Caching checkbox (`toolkit-field-enable_caching-checkbox`,
   the MUI `<span>` click target) to uncheck it.
   - **Verify**: `toolkit-field-enable_caching-checkbox-field`'s `input.checked`
     flips to `false`; the previously-disabled `Save`/`Discard` buttons become
     enabled (form is now dirty — no dedicated testid found for Save/Discard on
     the detail page; see § Concrete Handles for the accessible-name locator
     used and § Blocked Steps for the testid gap).
4. Click Save.
   - **Verify**: `PUT /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`
     fires and returns `200 OK`. No new console errors appear beyond the two
     pre-existing, unrelated dev-mode warnings already documented in the
     ELITEA-1922 AFS (see § Known Defects here).
5. Reload the page (full navigation to the same detail URL, or `page.reload()`
   equivalent) and wait for the Form view to re-render real data.
   - **Verify**: `toolkit-field-enable_caching-checkbox-field`'s `input.checked`
     is still `false` after reload — confirms server-side persistence, not just
     client-side state.
6. Switch to Raw Json view (`toolkit-raw-json-view-toggle`); read
   `toolkit-raw-json-editor-content`.
   - **Verify**: parsed JSON's `settings.enable_caching === false` (boolean, not
     string — confirmed live, same typing as the ELITEA-1922 AFS observed for
     this field).
7. Switch back to Form view (`toolkit-form-view-toggle`); click the Enable
   Caching checkbox again to re-check it; click Save.
   - **Verify**: before click, `input.checked === false`; after click,
     `input.checked === true`; Save fires a second
     `PUT /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}` →
     `200 OK`. Reload once more (or trust the same in-session state) and confirm
     `input.checked === true` persists — restoring the toolkit's original state
     (this doubles as this case's own cleanup, see § Cleanup).

## Expected Results
- The Enable Caching checkbox can be unchecked, saved, and the unchecked state
  survives a full page reload (server-side persistence, not just client state).
- The unchecked state is reflected as `"enable_caching": false` (boolean) in the
  Raw Json view.
- The checkbox can be re-checked and re-saved, restoring `"enable_caching": true`,
  confirmed via a second Save's `200 OK` response.
- No errors occur on any of the two `PUT` calls; no new console errors appear
  beyond the two pre-existing unrelated dev-mode warnings.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, Remote MCP detail page open in Form view, Enable Caching checked by default | detail page loads, checkbox checked | steps 1–2 | `step 1`: page load; `step 2`: `input.checked === true` | asserted |
| 1 Open a Remote MCP detail page in Form view | Detail page loads in Form view | step 1 | `step 1` | asserted |
| 2 Note current state of "Enable Caching" checkbox (checked by default) | Checkbox is checked | step 2 | `step 2`: `input.checked === true` | asserted |
| 3 Click "Enable Caching" to uncheck it | Checkbox becomes unchecked | step 3 | `step 3`: `input.checked === false` | asserted |
| 4 Click Save | Operation completes successfully | step 4 | `step 4`: `PUT .../tool/.../{id}` → `200 OK` | asserted |
| 5 Reload page — verify "Enable Caching" is unchecked | Checkbox remains unchecked after reload | step 5 | `step 5`: `input.checked === false` post-reload | asserted |
| 6 Switch to Raw Json — verify "enable_caching": false in JSON | JSON shows enable_caching as false | step 6 | `step 6`: `settings.enable_caching === false` | asserted |
| 7 Re-enable caching and save again | Checkbox is checked and saved | step 7 | `step 7`: `input.checked === true` pre-save-verify, second `PUT` → `200 OK` | asserted |
| Expected Final State: toggle persisted correctly in both views; setting restored to enabled after cleanup | — | steps 5–7 | steps 5–7 | asserted |
| Pass/Fail criteria: all steps complete without errors; state persisted and reflected correctly in Raw JSON | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- `step 4` / `step 7` assert the exact `PUT` endpoint and `200` status for each
  Save click — *added: the case text only says "Operation completes
  successfully" / "checkbox is checked and saved"; pinning the real network
  call (`PUT /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`)
  gives the implementer a concrete, non-UI-poll wait signal, consistent with
  the ELITEA-1922 AFS's own automation-hint pattern for this same form.*
- `step 6` asserts `enable_caching` is a JSON **boolean** (`false`/`true`), not a
  string — *added: observed live; the sibling `timeout`/`cache_ttl` fields on
  this same schema persist as strings (ELITEA-1922 AFS finding), so this is
  worth pinning explicitly rather than assuming boolean by default — a future
  regression that stringifies this field would otherwise slip past a loose
  truthy check.*
- `step 4` notes no new console errors beyond the two pre-existing dev-mode
  warnings — *added: same rationale as ELITEA-1922 AFS; confirms this edit flow
  doesn't introduce its own regression on top of the known, filed,
  non-blocking warnings.*
- `step 7`'s final re-check-and-save doubles as this case's own cleanup (see
  § Cleanup) — *added: the case's own "Expected Final State" already requires
  restoring the enabled setting, so no separate teardown call is needed beyond
  running step 7 to completion — worth calling out explicitly so the
  implementer doesn't add redundant teardown.*

## Cleanup

> **Amended by implementer** (fix-only round R1, PR #548, 2026-07-16): items
> 1–2 below describe the analyst's own live session, which reused the
> pre-existing `1244` toolkit and therefore needed no create/delete. The
> shipped implementation instead follows the option-3 seed-and-teardown
> variant (see § Test Data amendment above for why) — item 3 is the path
> actually taken, not just an available alternative.

1. This case's own step 7 IS its cleanup: it re-enables and re-saves Enable
   Caching, restoring the toolkit's original state. **Confirmed live**: after
   step 7, `input.checked === true` on both the in-session Form view and a
   follow-up reload — the reused toolkit (`autotest_remote_mcp_full`, id `1244`)
   was left in exactly the state it was found in during the analyst's session
   (screenshot: `test-results/screenshots/ELITEA-1929-step7-final-reenabled.png`).
   This still holds for the shipped implementation's seeded toolkit too — step
   7 restores its Enable Caching state before the `finally`-block delete runs.
2. The analyst's own exploration session created or deleted no toolkit (it
   reused an existing Remote MCP) — no `ToolkitAPI.delete_toolkit()` teardown
   call was needed for that session's data. The **shipped implementation**
   does not follow this path (see item 3).
3. **Shipped implementation**: seeds a dedicated toolkit per test run (same UI
   create flow as `test_mcp_view_toggle.py`'s `_seed_mcp_via_ui`) and tears it
   down via `ToolkitAPI.delete_toolkit(toolkit_id)` in `finally` — required
   because `ToolkitAPI.list_all_toolkits()` returns empty on this environment
   (see § Test Data amendment), leaving no reliable read-only way to
   rediscover `1244` or any other existing Remote MCP's id at runtime. Safe
   for this case's assertions since toggling Enable Caching has no
   destructive effect on other fields.

## Concrete Handles (discovered during exploration)

All testids below already exist in the live app (added during the ELITEA-1922
session, confirmed still present and functionally identical on the detail page
for this case — `ToolBaseProperty.jsx` is the same shared schema-driven field
renderer used by both the create and detail/edit forms). No new testids were
needed for this case.

| Element | Recommended Locator | Fallback |
|---|---|---|
| Enable Caching checkbox (click target) | `[data-testid="toolkit-field-enable_caching-checkbox"]` — MUI `<span>` wrapper | none |
| Enable Caching checkbox (`.checked` assertions) | `[data-testid="toolkit-field-enable_caching-checkbox-field"]` — the real `<input>` | none |
| Form / Raw Json view toggle | `[data-testid="toolkit-form-view-toggle"]` / `[data-testid="toolkit-raw-json-view-toggle"]` | none |
| Raw Json editor content (CodeMirror) | `[data-testid="toolkit-raw-json-editor-content"]` — editable `.cm-content` node | none |
| Detail page title heading | `[data-testid="toolkit-detail-title"]` | none |

**Gap (Save/Discard buttons on the detail page have no testid):** unlike the
create-form's `toolkit-form-save-button`, the **detail page's** Save/Discard
buttons (visible next to the toolkit title once the form is dirty) carry no
`data-testid` — during this session they were only reachable via
`page.getByRole('button', { name: 'Save' })`, which violates the project's
testid-only locator policy (`.agents/testing.md` § Locator policy). Per the
"missing testid ⇒ add it" escalation rule (not a stop+flag exception — the
element is inside `EliteaUI/src`, plainly placeable), **the implementer should
run `add-data-testid` first** to add stable testids (e.g.
`toolkit-detail-save-button` / `toolkit-detail-discard-button`) before writing
the page-object method, rather than shipping a role-based locator. This gap
also applies equally to the sibling ELITEA-1922 AFS's detail-page coverage
(that AFS's Concrete Handles table only lists the **create-form's**
`toolkit-form-save-button`, not a detail-page equivalent) — flagging here so it
isn't rediscovered per-case.

## Network Behavior
- `GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}?` — fires
  on detail-page load/reload; confirms persisted values render (wait for this
  before asserting checkbox state, not a fixed timeout — mirrors the
  ELITEA-1922 AFS's `navigate_to_detail` pattern already in `McpFormPage`).
- `PUT /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}` — fires on
  each Save click; `200 OK` on success. Confirmed live for both the
  uncheck-and-save (step 4) and re-check-and-save (step 7) calls.
- Several `GET .../toolkit_available_tools/...` and `GET .../toolkit_validator/...`
  calls also fire on load/save (tools-list + schema validation) — not required
  for this case's assertions, informational only (same pattern noted in the
  ELITEA-1922 AFS).

## Known Defects Found During Exploration

**None found in the Enable Caching toggle/persistence behavior itself.** All 7
case steps produced the expected result: the checkbox toggled, saved, survived
a full page reload, was correctly reflected as a JSON boolean in Raw Json, and
was successfully re-enabled and re-saved, restoring the original state.

The same two pre-existing, low-severity console warnings already filed as
`EliteaAI/elitea-testing-public#291` (React dev-mode: missing `key` prop in
list rendering; invalid `<p>`-in-`<p>` DOM nesting in `ToolBaseProperty.jsx`'s
tooltip) were observed on every page load/reload during this session — not
new, not tied to this case's actions, already tracked. No new defect filed.

## Blocked Steps

None. All 7 case steps were executed to completion against the live local
environment, reusing an existing Remote MCP (id `1244`).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- **Reuse `automation/pages/mcp_form_page.py` (`McpFormPage`) as-is** — it
  already exposes every locator and helper this case needs:
  `enable_caching_checkbox` / `enable_caching_checkbox_field`,
  `is_enable_caching_checked()`, `navigate_to_detail(toolkit_id, project_id)`,
  `switch_to_raw_json_view()` / `switch_to_form_view()`, `get_raw_json()`. No
  new page-object methods are strictly required except a `click_enable_caching_checkbox()`
  toggle helper (mirroring the existing `click_ssl_verify_checkbox()` pattern —
  same wait-on-real-`.checked` approach) and a Save-on-detail-page method once
  the testid gap above is closed.
- **Save button on the detail page has no testid yet** — see § Concrete Handles
  gap above; run `add-data-testid` before writing the implementation so the new
  page-object method doesn't ship a role-based locator.
- Use `ToolkitAPI` (`automation/api/client.py`) for any needed lookup/seed
  (`get_toolkit(toolkit_id)`, `delete_toolkit(toolkit_id)` if the implementer
  chooses the seed-and-teardown cleanup variant) — already exists, no new API
  client code needed.
- Wait strategy: wait for the `PUT .../tool/prompt_lib/{project}/{id}` response
  (`200`) before asserting the next state, not a fixed timeout — same rationale
  as the ELITEA-1922 AFS's `save_and_wait_for_created` for the create-form's
  `POST`.
- After `page.reload()` (step 5), wait for the detail GET to resolve AND for
  the checkbox's real DOM `.checked` state, not just page-load — `McpFormPage`
  already has `_wait_for_detail_data_rendered()` for the equivalent
  "past-placeholder" wait on the title; the checkbox itself has no such
  placeholder state so a direct `expect(locator).to_be_checked()` /
  `not_to_be_checked()` with the default Playwright auto-wait is sufficient.
