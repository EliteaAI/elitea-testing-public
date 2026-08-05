# Test Case: Edit Remote MCP — Modify Configuration via Raw JSON

## Metadata
- **TMS ID**: ELITEA-1927
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `priority: critical`; case body text itself
  says "**Priority:** medium" — a pre-existing internal inconsistency in the
  source case file, not introduced by this analysis; the frontmatter (`critical`)
  is treated as authoritative, matching the same disposition already recorded in
  the sibling ELITEA-1929 AFS for the identical inconsistency)
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
  `${ELITEA_PROJECT_ID}`, confirmed `399` live).
- An existing Remote MCP toolkit must be open on its detail page
  (`/mcps/all/{id}`). **Confirmed live**: the project already had 6+
  pre-existing Remote MCPs (leftovers from prior manual/automated exploration
  sessions), but per Hard Rule 10 (read-only preferred) this case still seeded
  its own dedicated toolkit rather than mutating a shared leftover — editing +
  saving is inherently destructive to whatever toolkit is used, so a
  dedicated, disposable toolkit is the safe choice (same pattern already used
  by the sibling ELITEA-1929 case's shipped implementation, and by
  `test_mcp_view_toggle.py`'s `_seed_mcp_via_ui` helper).

## Test Data

| Field | Value |
|-------|-------|
| Updated Description | `Updated via raw JSON` (per case's own Test Data table) |

### generate-shared-with-cleanup
- An MCP toolkit is created per test run via the existing `McpFormPage` create
  flow (`navigate_to_create` → `select_remote_mcp_type` → `fill_name` +
  `fill_url` → `save_and_wait_for_created`), matching the same helper pattern
  as `test_mcp_view_toggle.py`'s `_seed_mcp_via_ui` and the sibling
  ELITEA-1929 case's shipped implementation. Torn down via
  `ToolkitAPI.delete_toolkit()` in a `finally` block — required because
  `ToolkitAPI.list_all_toolkits()` returns empty on this environment
  regardless of auth method (documented quirk, see `config.py`'s
  `remote_github_mcp_toolkit_id` comment and
  `.agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md`),
  so there is no reliable read-only way to rediscover an existing toolkit's id
  at runtime.
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (from `.env.test`, confirmed live via the
  sidebar's project textbox).

## Test Steps

1. Navigate to `${BASE_URL}/mcps/all/{toolkit_id}` for an existing Remote MCP
   (localhost: `APP_PREFIX` is empty, no `/app` prefix). Wait for the detail
   GET (`GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`)
   to resolve and the Form view to render real data (not the "Edit Toolkit"
   placeholder).
   - **Verify**: page loads in Form view (`toolkit-form-view-toggle` pressed);
     `toolkit-detail-title` shows the toolkit's name.
2. Click the "Raw Json" toggle button (`toolkit-raw-json-view-toggle`).
   - **Verify**: `toolkit-raw-json-editor-content` (CodeMirror `.cm-content`
     node) becomes visible.
3. Read and parse `toolkit-raw-json-editor-content`'s text content as JSON;
   inspect the object.
   - **Verify**: JSON contains `name`, `description`, and `settings` with
     `url`, `timeout`, `cache_ttl`, `ssl_verify`, `enable_caching`,
     `selected_tools`. **`available_mcp_tools` does NOT appear anywhere in the
     live schema** (top level or under `settings`) — confirmed live on 2 fresh
     toolkits, and consistent with the sibling ELITEA-1922 AFS's own
     exhaustive Raw Json schema assertions (also never lists this field). This
     is case-text drift, not a product defect — see § Known Defects Found /
     CLARIFICATION filed as
     [`EliteaAI/elitea-testing-public#574`](https://github.com/EliteaAI/elitea-testing-public/issues/574).
     Assert the 8 fields that ARE present; do not assert `available_mcp_tools`.
4. Click into the Raw Json editor and modify the `"description"` value to
   `"Updated via raw JSON"`, leaving the rest of the JSON structurally intact.
   - **Verify**: `toolkit-raw-json-editor-content`'s parsed JSON reflects the
     new description value; no "Invalid JSON format" validation message is
     shown.
   - **Automation hint (CodeMirror editing mechanics — no `fill_raw_json()`
     method exists yet in `McpFormPage`, see § Blocked Steps / Concrete
     Handles)**: the editor is a CodeMirror `.cm-content` node, one `<div>`
     line per JSON line — NOT a single contenteditable blob. `Ctrl+A` /
     `Ctrl+Home`+`Ctrl+Shift+End` do **not** reliably select the entire
     document in this environment (confirmed live: selecting and deleting via
     that sequence left a stray character behind — see § Known Defects Found
     / automation-hint note). The reliable, confirmed-live approach is
     **per-line**: click the specific line's `<div>` (each line has its own
     DOM node, addressable the same way `headers_editor_content`'s existing
     select→Backspace→type pattern works), press `Home`, then `Shift+End` to
     select just that line's content, then type the full replacement line
     (including trailing comma/brace) to overwrite the selection. This
     mirrors `fill_headers_json`'s existing select-then-type discipline, just
     scoped to a single CodeMirror line instead of the whole editor.
5. Read the Save button's state
   (`toolkit-detail-save-button`).
   - **Verify**: Save button transitions from `disabled` to enabled once the
     description edit lands (confirmed live).
6. Click Save.
   - **Verify**: `PUT /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`
     fires and returns `200 OK`. No new console errors appear beyond the two
     pre-existing, unrelated dev-mode warnings already documented in the
     ELITEA-1922 AFS (see § Known Defects here). The page auto-switches back
     to Form view after Save resolves (confirmed live — not a case
     requirement, but a UI side-effect worth encoding as a wait signal).
7. Click "Form" toggle button (`toolkit-form-view-toggle`); read
   `toolkit-form-description-input`'s value.
   - **Verify**: `toolkit-form-description-input.value === "Updated via raw JSON"`.
8. Reload the page (full navigation to the same detail URL, or `page.reload()`
   equivalent) and wait for the Form view to re-render real data; then switch
   to Raw Json view and re-parse.
   - **Verify**: `toolkit-form-description-input.value === "Updated via raw JSON"`
     (Form view, post-reload) AND the parsed Raw Json's
     `description === "Updated via raw JSON"` (Raw Json view, post-reload) —
     confirms server-side persistence in both views, not just client-side
     state.

## Expected Results
- A Remote MCP's `description` field can be edited directly through the Raw
  Json view's CodeMirror editor.
- The Save button enables once the JSON is validly edited, and clicking it
  fires a successful `PUT` (`200 OK`).
- The edited description is reflected in the Form view immediately after Save.
- The edited description persists in BOTH the Form view and the Raw Json view
  after a full page reload (server-side persistence).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, existing Remote MCP open on its detail page | detail page loads | step 1 | `step 1`: Form view pressed, detail title shows name | asserted |
| 1 Open an existing Remote MCP detail page | Detail page loads | step 1 | `step 1` | asserted |
| 2 Click "Raw Json" toggle button — verify JSON editor appears | JSON editor is visible | step 2 | `step 2`: `toolkit-raw-json-editor-content` visible | asserted |
| 3 Verify JSON contains current config (name, description, settings with url, timeout, cache_ttl, ssl_verify, enable_caching, selected_tools, available_mcp_tools) | All expected fields are present in the JSON | step 3 | `step 3`: 8 of 9 listed fields confirmed present; `available_mcp_tools` confirmed ABSENT from the live schema | clarification filed (see Known Defects / #574) — case text lists a field the live product never renders, in this case or its ELITEA-1922 sibling; asserting its presence would reverse-mask a stale case, so the AFS asserts the 8 real fields only |
| 4 Modify "description" value in JSON editor to "Updated via raw JSON" | JSON editor reflects the change | step 4 | `step 4`: parsed JSON `description` updated, no "Invalid JSON format" message | asserted |
| 5 Verify Save button becomes enabled | Save button is clickable | step 5 | `step 5`: `toolkit-detail-save-button` not disabled | asserted |
| 6 Click Save | Operation completes successfully | step 6 | `step 6`: `PUT .../tool/.../{id}` → `200 OK` | asserted |
| 7 Click "Form" toggle button — verify Description field shows "Updated via raw JSON" | Form view reflects the updated description | step 7 | `step 7`: `toolkit-form-description-input.value` | asserted |
| 8 Reload page — verify change persisted in both Form and Raw Json views | Both views show "Updated via raw JSON" after reload | step 8 | `step 8`: Form input value + re-parsed Raw Json `description`, both post-reload | asserted |
| Expected Final State: description change visible in Form view and persists after reload | — | steps 7–8 | steps 7–8 | asserted |
| Pass/Fail criteria: all steps complete without errors; JSON edit reflected in Form view and persists after reload | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- `step 4` documents the CodeMirror per-line edit mechanics as an
  **automation hint** rather than a bare assertion — *added: no existing
  `McpFormPage` method edits the Raw Json editor (`fill_headers_json` exists
  for the Headers sub-editor only), and the naive whole-document
  select-then-delete approach (`Ctrl+A`/`Ctrl+Home`+`Ctrl+Shift+End`) was
  tried live and produced silent data corruption (a stray character survived
  a full-document delete — see § Known Defects Found). Without this note the
  implementer would rediscover the same failure mode from scratch.*
- `step 6` asserts the exact `PUT` endpoint and `200` status for the Save
  click — *added: the case text only says "Operation completes successfully";
  pinning the real network call
  (`PUT /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`) gives
  the implementer a concrete, non-UI-poll wait signal, consistent with the
  ELITEA-1922 and ELITEA-1929 AFS's own automation-hint pattern for this same
  form.*
- `step 6` notes the page auto-switches back to Form view after Save resolves
  — *added: observed live, not in the case text; worth documenting as a wait
  signal / expected side-effect so the implementer doesn't need to explicitly
  re-click the Form toggle before step 7 if the test structure follows the
  live UI's actual behavior.*
- `step 3` documents the `available_mcp_tools` field gap explicitly with a
  disposition of "clarification filed" rather than silently dropping it from
  the assertion — *added: per the reverse-masking guard, a case element that
  doesn't hold live must be visibly tracked, not quietly omitted.*

## Blocked Steps

None — the case executed end-to-end with no blocking defect. The only gap is
a **missing automation capability**, not a blocked case step: `McpFormPage`
has no `fill_raw_json()` (or per-line raw-json-edit) method yet. This is
implementer work, not an analyst blocker — see § Concrete Handles /
Automation Hints in step 4 above for the confirmed-live mechanics the
implementer should encode into that new method.

## Cleanup

1. The seeded toolkit (created per § Test Data's `generate-shared-with-cleanup`)
   is deleted via `ToolkitAPI.delete_toolkit(toolkit_id)` in a `finally` block
   — same pattern as the sibling ELITEA-1929 case's shipped implementation.
   **Confirmed live**: this analyst session's seeded toolkit
   (`autotest_mcp_rawjson_1927`, id `1346`) was deleted via the UI's
   overflow-menu → Delete → type-name-to-confirm flow (no dedicated API
   cleanup helper was invoked in this manual session since the browser's
   auth is cookie-based, not exposed to a standalone API client outside the
   pytest fixture chain) — confirmed absent from `/mcps/all` afterward.
2. This case makes no other persistent changes — the edited `description`
   value lives only on the disposable seeded toolkit, which is fully deleted
   by item 1. No restoration step is needed (unlike ELITEA-1929's
   toggle-and-restore pattern).

## Concrete Handles (discovered during exploration)

All testids below already exist in the live app (added during the ELITEA-1922
session; `ToolBaseProperty.jsx` is the same shared schema-driven field
renderer used by both create and detail/edit forms, and the Raw Json /
`toolkit-detail-save-button` testids are shared with the sibling ELITEA-1929
case). No new testids were needed for this case's own elements.

| Element | Recommended Locator | Fallback |
|---|---|---|
| Raw Json view toggle | `[data-testid="toolkit-raw-json-view-toggle"]` | none |
| Form view toggle | `[data-testid="toolkit-form-view-toggle"]` | none |
| Raw Json editor content (CodeMirror, whole-editor read/parse) | `[data-testid="toolkit-raw-json-editor-content"]` — editable `.cm-content` node | none |
| Description field (Form view) | `[data-testid="toolkit-form-description-input"]` | none |
| Detail page Save button | `[data-testid="toolkit-detail-save-button"]` (added ELITEA-1929, EliteaUI PR #572) | none |
| Detail page title heading | `[data-testid="toolkit-detail-title"]` | none |

**Gap — no per-line Raw Json edit locator exists (this is expected, not a
defect):** the Raw Json CodeMirror editor renders one `<div>` per JSON line
inside `toolkit-raw-json-editor-content`; there is no per-line testid (nor
should there be — these are CodeMirror-internal render nodes, not stable UI
elements). The implementer's new `fill_raw_json`-style method should locate
the target line via `page.get_by_text(...)` scoped inside
`raw_json_editor_content` (matching the existing `fill_headers_json` pattern's
reliance on the editor's own text-selection API — see step 4's automation
hint), not by adding a new testid.

## Network Behavior
- `GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}?` — fires
  on detail-page load/reload; confirms persisted values render (wait for this
  before asserting field state, not a fixed timeout — mirrors the existing
  `navigate_to_detail` pattern already in `McpFormPage`).
- `PUT /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}` — fires
  on the Save click; `200 OK` on success. Confirmed live for the
  description-edit-and-save flow (step 6).
- Several `GET .../toolkit_available_tools/...` and
  `GET .../toolkit_validator/...` calls also fire on load/save
  (tools-list + schema validation) — not required for this case's assertions,
  informational only (same pattern noted in the ELITEA-1922 / ELITEA-1929
  AFS's).

## Known Defects Found During Exploration

**No functional defect in the Raw Json edit/save/persist flow itself.** All 8
case steps produced the expected result: the description was editable via Raw
Json, the Save button correctly gated on a dirty+valid state, the save
succeeded (`200 OK`), the change appeared in Form view immediately, and it
persisted in both views after a full page reload.

**CLARIFICATION filed**
([`EliteaAI/elitea-testing-public#574`](https://github.com/EliteaAI/elitea-testing-public/issues/574),
per the reverse-masking guard — case-text drift, not a product defect): the
case's Step 3 lists `available_mcp_tools` as an expected field in the Raw
Json's `settings` object. The live product never renders this field (not on
this case's toolkits, nor on the sibling ELITEA-1922 AFS's exhaustively
schema-asserted create-form toolkit) — the case text is the stale artifact,
not the product.

**Automation-hint finding (not a product defect — a CodeMirror interaction
gotcha)**: attempting a whole-document select via `Ctrl+A` or
`Ctrl+Home`+`Ctrl+Shift+End` followed by `Delete`/`Backspace` on the Raw Json
editor did **not** reliably clear the entire document in this environment —
one edit attempt left a single stray character behind mid-document (`"headers":
nul,` instead of `"headers": null,` after a supposedly-complete
select-all-and-delete). This was caught live via the editor's own
`Invalid JSON format` validation message (the malformed JSON was visibly
flagged, and the Save button correctly stayed available only once the JSON
was fixed and re-validated — confirming the app's own JSON-validation gating
worked correctly throughout). Not filed as a defect: this is normal CodeMirror
multi-line-editor selection behavior (each line is its own DOM node), not a
product bug — captured here purely as an automation hint (see step 4) so the
implementer's `fill_raw_json()`-style method uses the per-line approach from
the start instead of rediscovering this the hard way.

The same two pre-existing, low-severity console warnings already filed as
`EliteaAI/elitea-testing-public#291` (React dev-mode: missing `key` prop in
list rendering; invalid `<p>`-in-`<p>` DOM nesting in `ToolBaseProperty.jsx`'s
tooltip) and `#549` (`MUI: The value provided to the Tabs component is
invalid`) were observed during this session — not new, not tied to this
case's actions, already tracked. No new console-error defect filed.

## Evidence

- Raw Json content post-edit-pre-save (validation state):
  `test-results/json/ELITEA-1927-step4-raw-json-post-edit.json` (captured via
  live `textContent` read during this session, reproduced here inline in
  step 4's verification and in the Known Defects note above).
- Network: `PUT /api/v2/elitea_core/tool/prompt_lib/399/1346` → `200 OK`
  (confirmed via live network-request listing during this session).
- Post-reload confirmation: Form view `toolkit-form-description-input.value`
  and Raw Json `description` both read `"Updated via raw JSON"` after a full
  page navigation reload (not `page.reload()` client-side re-render) —
  confirms genuine server-side persistence.
