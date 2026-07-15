# Test Case: Create Remote MCP — All Fields Populated

## Metadata
- **TMS ID**: ELITEA-1922
- **Linked Story**: none
- **Priority**: l1
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths the dev server, confirmed "Elitea is connected" in the sidebar after page load)
- **Analyst**: qa-engineer (agent), session 2026-07-15
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (on localhost this is automatic via `VITE_DEV_TOKEN`; on deployed envs, standard Keycloak login via `${TEST_USER}`).
- Project context is set (sidebar shows `Project: <name>`; project id read from `${ELITEA_PROJECT_ID}`).
- No precondition data needs seeding — MCP creation is a self-contained create flow.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Toolkit Name: `autotest_remote_mcp_full` — recommend suffixing with a per-run unique token (e.g. `f"autotest_remote_mcp_full_{uuid4().hex[:8]}"`) since uniqueness constraints were not explored; a colliding name from a prior failed run could cause a false failure. Uniqueness was NOT verified live (out of scope for this case) — implementer should verify empirically on first run and drop the suffix only if the backend confirms names aren't unique-constrained.
- Description: `Full configuration test MCP`
- URL: `https://mcp.example.com/sse`
- Headers JSON: `{"Authorization": "Bearer test123"}`
- Client Id: `test_client_id`
- Client Secret: `test_secret_value`
- Scopes: `read,write`
- Timeout: `600` (default observed: `300`)
- Cache TTL: `120` (default observed: `300`)
- Enable Caching: leave checked (confirmed default = checked/`true`)
- Ssl Verify: uncheck (confirmed default = checked/`true`; target state = unchecked/`false`)

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.

## Test Steps

1. Navigate to `${BASE_URL}/mcps/create` (localhost: `APP_PREFIX` is empty, so no `/app` prefix).
   - **Verify**: "Choose the MCP type" heading is visible; `Local` / `Remote` category tabs are present.
2. Click the Remote MCP type card (`[data-testid="toolkit-type-card-mcp"]`).
   - **Verify**: URL becomes `${BASE_URL}/mcps/create/mcp`; page title becomes "New Remote MCP"; "Configuration" accordion section is expanded and visible.
3. Fill Toolkit Name (`[data-testid="toolkit-form-name-input"]`) with the generated name.
   - **Verify**: field displays the typed value.
4. Fill Description (`[data-testid="toolkit-form-description-input"]`) with `Full configuration test MCP`.
   - **Verify**: field displays the typed value.
5. Fill Url (`[data-testid="toolkit-field-url-input"]`) with `https://mcp.example.com/sse`.
   - **Verify**: field displays the typed value.
6. Click into the Headers JSON editor (`[data-testid="toolkit-field-headers-editor"]`, a CodeMirror instance nested inside an expandable "Headers" accordion — the accordion is expanded by default; the editable `.cm-content` node itself carries its own `[data-testid="toolkit-field-headers-editor-content"]`, see Concrete Handles), select-all (`Ctrl/Cmd+A`) to clear the default `{}`, then type `{"Authorization": "Bearer test123"}`.
   - **Verify**: editor content shows the typed JSON with CodeMirror line numbers/gutter.
7. Fill Client Id (`[data-testid="toolkit-field-client_id-input"]`) with `test_client_id`.
   - **Verify**: field displays the typed value.
8. Fill Client Secret (`[data-testid="toolkit-field-client_secret-input-field"]` — the real `<input>`, not the `toolkit-field-client_secret-input` wrapper `<Box>`) with `test_secret_value`. The field is in "Password" view by default (masked visually; the toggler also offers a "Secret" view for referencing a stored platform secret — not used by this case).
   - **Verify**: field accepts input (value is visually masked but present in the DOM value).
9. Fill Scopes (`[data-testid="toolkit-field-scopes-input"]`) with `read,write`. The field auto-normalizes to `read, write` (comma+space) on input — this is cosmetic formatting, not a data change (see Coverage Map).
   - **Verify**: field shows the (possibly reformatted) value.
10. Clear and fill Timeout (`[data-testid="toolkit-field-timeout-input"]`) with `600`, replacing the default `300`.
    - **Verify**: field shows `600`.
11. Verify Enable Caching checkbox (`[data-testid="toolkit-field-enable_caching-checkbox-field"]` — the real `<input>` carrying `.checked`; the `toolkit-field-enable_caching-checkbox` testid is the MUI `<span>` click target only) is checked by default.
    - **Verify**: `input.checked === true`.
12. Clear and fill Cache TTL (`[data-testid="toolkit-field-cache_ttl-input"]`) with `120`, replacing the default `300`.
    - **Verify**: field shows `120`.
13. Verify Ssl Verify checkbox (`[data-testid="toolkit-field-ssl_verify-checkbox-field"]` for the `.checked` assertion; click the `[data-testid="toolkit-field-ssl_verify-checkbox"]` span to toggle it) is checked by default, then click it to uncheck.
    - **Verify**: before click, `input.checked === true`; after click, `input.checked === false`.
14. Click Save (`[data-testid="toolkit-form-save-button"]`).
    - **Verify**: `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` returns `201 Created`; page navigates to `${BASE_URL}/mcps/all/{id}?name={toolkit_name}`.
15. On the MCP detail page (title read from `[data-testid="toolkit-detail-title"]`), verify the page title contains the toolkit name and the Form view shows all values persisted:
    - **Verify**: `h1`/heading text = generated toolkit name; Toolkit Name, Description, Url, Headers, Client Id, Scopes, Timeout (`600`), Cache TTL (`120`) fields show the saved values; Enable Caching checked; Ssl Verify unchecked. Client Secret field on the detail page shows the secret-reference **hex id bare** (`[0-9a-f]{32}`, e.g. `dcd2cc2335674b9ba848368c9a247929`), NOT the literal `test_secret_value` and NOT the `{{secret.<hex>}}` wrapper syntax (that wrapper only appears in the Raw Json view, see step 16) — this is correct, intentional secret-management behavior (see Coverage Map / Known Defects). **CLARIFICATION (implementer Phase 4, reverse-masking guard):** this line originally claimed the Form view shows the full `{{secret.<hex>}}` wrapper too — live product confirmed at implementation time shows the bare hex on the Form view's `<input>` DOM value instead; corrected here per live observation, not case-text assumption.
16. Switch to "Raw Json" view (`[data-testid="toolkit-raw-json-view-toggle"]`) on the detail page; read the JSON from the CodeMirror editor's editable node (`[data-testid="toolkit-raw-json-editor-content"]`).
    - **Verify**: JSON contains `"name": "<toolkit_name>"`, `"description": "Full configuration test MCP"`, `"settings.url": "https://mcp.example.com/sse"`, `"settings.headers": {"Authorization": "Bearer test123"}`, `"settings.client_id": "test_client_id"`, `"settings.client_secret": "{{secret.<hex>}}"` (reference token, not plaintext), `"settings.scopes": ["read", "write"]`, `"settings.timeout": "600"` (string, not number — see Coverage Map), `"settings.cache_ttl": "120"` (string), `"settings.enable_caching": true`, `"settings.ssl_verify": false`, `"type": "mcp"`.

## Expected Results
- The Remote MCP toolkit is created successfully and the detail page (`/mcps/all/{id}`) loads with the correct name.
- Every configured field is correctly reflected in BOTH the Form view and the Raw Json view.
- `client_secret` is never displayed or persisted as plaintext — the Raw JSON shows the `{{secret.<hex>}}` wrapper, the Form view's `<input>` DOM value shows the same hex bare, no wrapper (intentional platform secret-management behavior; the two representations differ in syntax but carry the same hex id — cross-check them for equality rather than asserting an exact string on either alone).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, navigated to MCP creation, selected Remote MCP | form loads at `/mcps/create/mcp` | steps 1–2 | `step 2` | asserted |
| 1 Navigate to MCP creation page and select "Remote MCP" | form loads at `/mcps/create/mcp` | steps 1–2 | `step 2`: URL + heading | asserted |
| 2 Fill Toolkit Name | field displays input | step 3 | `step 3` | asserted |
| 3 Fill Description | field displays input | step 4 | `step 4` | asserted |
| 4 Fill Url | field displays URL | step 5 | `step 5` | asserted |
| 5 Expand Headers, enter JSON | editor accepts input | step 6 | `step 6` | asserted |
| 6 Fill Client Id | field displays input | step 7 | `step 7` | asserted |
| 7 Fill Client Secret (Password view default) | field accepts masked input | step 8 | `step 8` | asserted |
| 8 Fill Scopes | field displays input | step 9 | `step 9` | asserted *(reformats to `read, write` — cosmetic, see Axis 2)* |
| 9 Change Timeout 300→600 | field updates to 600 | step 10 | `step 10` | asserted |
| 10 Verify Enable Caching checked by default | checkbox checked | step 11 | `step 11` | asserted |
| 11 Change Cache TTL 300→120 | field updates to 120 | step 12 | `step 12` | asserted |
| 12 Verify Ssl Verify checked by default, uncheck it | checkbox becomes unchecked | step 13 | `step 13` | asserted — **case text's own preconditions-row-12 ambiguity resolved by live observation: default IS checked, matching the case's "checked by default" language; no drift.** |
| 13 Click Save | operation succeeds, detail page loads | step 14 | `step 14`: 201 + navigation | asserted |
| 14 Verify MCP created, detail page loads with correct name | detail page accessible | step 15 | `step 15`: heading text | asserted |
| 15 Switch to Raw Json, verify all configured values | JSON shows name, description, url, timeout:600, cache_ttl:120, ssl_verify:false, enable_caching:true | step 16 | `step 16` | asserted — **timeout/cache_ttl are persisted as JSON strings (`"600"`/`"120"`), not numbers; case text doesn't specify type. Live product is source of truth — assert string equality, not numeric.** |
| Expected Final State: MCP created, all fields persisted, Raw JSON reflects every value | — | steps 14–16 | steps 14–16 | asserted |
| Pass/Fail criteria: all steps complete without error, all values correct in both views | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- `step 6` / `step 16` assert `client_secret` is stored as a `{{secret.<hex>}}` reference, never plaintext — *added: this is a security-relevant behavior the case text doesn't call out explicitly ("accepts masked input" only covers the UI input, not the persisted-value shape); worth guarding so a future regression that leaks the plaintext secret into the JSON is caught.*
- `step 9` notes the Scopes field auto-reformats `read,write` → `read, write` on input — *added: observed during exploration; not a functional defect (the persisted array `["read","write"]` is correct either way) but the implementer should assert against the array in the Raw JSON, not exact input-field string equality, to avoid a flaky test tied to this cosmetic reformatting.*
- `step 16` asserts `timeout`/`cache_ttl` are JSON strings, not numbers — *added: observed during exploration (both fields round-trip through the UI's tel-input handling as strings); the case text's "timeout:600" is ambiguous on type, and asserting `=== 600` (number) would be a false failure against the live product's actual, intentional string-typed schema field.*
- No console-error assertion added — the app has two pre-existing, unrelated React dev-mode warnings (missing `key` prop in `CategorySection`/`GroupedCategory`; invalid `<p>`-in-`<p>` DOM nesting from `InfoTooltip` inside `Typography` in `ToolBaseProperty`) that fire on load regardless of this case's actions. Filed as a single low-severity clarification/defect (see Known Defects) rather than folded into this test's assertions, to avoid coupling this functional test to unrelated cosmetic React warnings.
- `step 14` asserts the `beforeunload` nav-blocker fires when leaving a dirty, unsaved form — *added: observed while re-verifying testids (navigating away from a filled-but-unsaved form triggers a native "leave site?" confirm dialog). Not required by the case, but worth a light mention in Automation Hints since a test harness that navigates away mid-test (e.g., on failure/cleanup) will hit this dialog and hang unless it's handled.*

## Cleanup

1. This case creates a persistent MCP toolkit (server-side `tool` entity, confirmed via `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` → `201 Created` with a numeric `id` in the response body, e.g. `id: 1244`).
2. Delete it in test teardown via the existing `ToolkitAPI.delete_toolkit(toolkit_id)` client (`automation/api/client.py`, confirmed present — calls `DELETE {ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`). Capture the `id` from the Save response (network wait) or from the post-save detail-page URL (`/mcps/all/{id}`) and pass it to teardown.
3. No credential/secret cleanup needed — the Client Secret round-trips through the platform's own secret-reference mechanism (`{{secret.<id>}}`); whether that underlying secret record itself needs separate deletion was NOT explored in this case (out of scope — this case only verifies the MCP-toolkit form, not secret lifecycle) and should be flagged to the lead if secret accumulation becomes a concern across the suite.
4. During manual exploration, one MCP toolkit was created on the local DEV backend (id `1244`, name `autotest_remote_mcp_full`) and was **not deleted** by this analysis session (analyst does not have automation authoring/cleanup authority — see workflow.md; the implementer's test + teardown is the durable cleanup mechanism). Flag to the implementer: either delete id `1244` manually via `DELETE ${ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${ELITEA_PROJECT_ID}/1244` before the automated test's own data starts accumulating, or ignore it as harmless manual-exploration residue (it is a `Private`-project-scoped Remote MCP with a name that won't collide unless the implementer's generated names aren't uniquified).

## Concrete Handles (discovered during exploration)

All testids below were added during this session (draft PR `EliteaAI/EliteaUI#554` → `main`, already committed to `automation/testids` — commit `1e04dc9`, live on the dev server now). `ToolBaseProperty.jsx` is a **shared, schema-driven field renderer** used by every toolkit/MCP/application creation form in the platform — the dynamic `toolkit-field-{k}-*` testids therefore also apply to any other toolkit type sharing the same schema property key, which is expected reuse, not scope creep (this case only touches the MCP schema's actual rendered fields).

| Element | Recommended Locator | Fallback |
|---|---|---|
| Remote MCP type-selector card | `[data-testid="toolkit-type-card-mcp"]` | none — testid-only policy; card has no stable text/role fallback (label "Remote MCP" is duplicated by a category-header text node, which is why a naive `getByText` match resolved to the wrong ancestor during initial exploration — see Known Defects for the false-positive writeup) |
| Toolkit Name input | `[data-testid="toolkit-form-name-input"]` | none |
| Description input | `[data-testid="toolkit-form-description-input"]` | none |
| Url input | `[data-testid="toolkit-field-url-input"]` | none |
| Headers JSON editor (CodeMirror) | `[data-testid="toolkit-field-headers-editor"]` — testid is on the editor's wrapping `<Box>`; the editable `.cm-content` node itself now carries its own `[data-testid="toolkit-field-headers-editor-content"]` (added during implementer exploration, see below) — use that testid directly for typing/reading, no CSS-class sub-selector needed | none |
| Client Id input | `[data-testid="toolkit-field-client_id-input"]` | none |
| Client Secret input | `[data-testid="toolkit-field-client_secret-input-field"]` — the real `<input>` element, addressable directly (added during implementer exploration; supersedes the originally-recommended `toolkit-field-client_secret-input` wrapper `<Box>` + `.locator('input')` chain below the table) | none |
| Scopes input | `[data-testid="toolkit-field-scopes-input"]` | none |
| Timeout input | `[data-testid="toolkit-field-timeout-input"]` | none |
| Cache TTL input | `[data-testid="toolkit-field-cache_ttl-input"]` | none |
| Enable Caching checkbox | `[data-testid="toolkit-field-enable_caching-checkbox"]` — MUI `<span>` wrapper, click target; for `.checked` assertions use the real `<input>`'s own `[data-testid="toolkit-field-enable_caching-checkbox-field"]` directly (added during implementer exploration; supersedes the `.locator('input')` chain) | none |
| Ssl Verify checkbox | `[data-testid="toolkit-field-ssl_verify-checkbox"]` — MUI `<span>` wrapper, click target; for `.checked` assertions use `[data-testid="toolkit-field-ssl_verify-checkbox-field"]` directly (added during implementer exploration; same pattern as Enable Caching above) | none |
| Form / Raw Json view toggle | `[data-testid="toolkit-form-view-toggle"]` / `[data-testid="toolkit-raw-json-view-toggle"]` | none |
| Raw Json editor content (CodeMirror) | `[data-testid="toolkit-raw-json-editor-content"]` — the editable `.cm-content` node, addressable directly for reading the persisted JSON (added during implementer exploration) | none |
| Save button | `[data-testid="toolkit-form-save-button"]` | none |
| Detail page title heading | `[data-testid="toolkit-detail-title"]` — plain MUI `Typography`, not an `h1`; renders an "Edit Toolkit" placeholder until the tool-detail GET resolves (added during implementer exploration) | none |

> **Implementer exploration note (same-PR AFS amendment, `docs(afs)` commit):** five native-input/content testids (`toolkit-field-client_secret-input-field`, `toolkit-field-enable_caching-checkbox-field`, `toolkit-field-ssl_verify-checkbox-field`, `toolkit-field-headers-editor-content`, `toolkit-raw-json-editor-content`) plus `toolkit-detail-title` were added to EliteaUI during implementation specifically to eliminate the `.locator('input')` / `.locator('.cm-content')` wrapper-chaining this table originally recommended (see rows above) — chaining an untested CSS selector off a wrapper testid violates the testid-only locator policy (`.claude/rules/page-objects.md`). All references above are updated to point at the new testids directly; no wrapper-chaining remains anywhere in this spec.

## Network Behavior
- `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` — fires on Save click; `201 Created` on success; response body's `id` is the new toolkit id, needed for teardown and for constructing the expected detail-page URL.
- `GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}?` — fires on detail-page load; confirms persisted values (this is effectively what the Form/Raw JSON views render from — wait for this to resolve before asserting persisted values, not a fixed timeout).
- `GET /api/v2/elitea_core/toolkit_available_tools/prompt_lib/${PROJECT_ID}/{id}` (×2) and `GET /api/v2/elitea_core/toolkit_validator/prompt_lib/${PROJECT_ID}/{id}` also fire on detail-page load (tools-list + schema validation) — not required for this case's assertions, informational only.

## Known Defects Found During Exploration

**None found in the MCP toolkit creation/persistence feature itself.** All 15 case steps produced the expected result; all field values persisted correctly in both Form and Raw JSON views; the Client Secret's secret-reference-token behavior is intentional platform design, not a defect.

Two low-severity, pre-existing findings were filed as separate issues in `elitea-testing-public` (not blocking this case, both disposition = informational/clarification, `expect.soft()` recommended if ever asserted against):

- **[MINOR] React dev-mode console warnings on the MCP/Toolkit creation form** — filed as `EliteaAI/elitea-testing-public#291` (label `bug`). Two warnings fire on every load of `/mcps/create` and `/mcps/create/mcp` regardless of this case's actions: (1) missing `key` prop in `CategorySection`/`GroupedCategory` list rendering (`ToolkitTypeSelector.jsx`); (2) invalid DOM nesting `<p>` cannot appear as a descendant of `<p>` from `InfoTooltip` rendered inside a `Typography` in `ToolBaseProperty.jsx`. Both are dev-build-only warnings (no user-visible impact observed), not tied to any of the case's 15 steps. Recommend `expect.soft()` if a future test asserts zero console errors on this page — do not block on this case.
- No CLARIFICATION filed for the case-text ambiguity in Preconditions row 12 ("Ssl Verify checkbox is checked by default") — resolved directly via live observation (`input.checked === true` confirmed for both checkboxes before any interaction); the case text and live product agree, so this was a non-issue, not an ambiguity requiring a tracked decision.

## Blocked Steps

None. All 15 case steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`).
- No existing page object for MCP/Toolkit creation forms (`automation/pages/` has `toolkit_detail_page.py` for the detail/read side, but nothing for the create flow) — this is a **new page object**, e.g. `mcp_form_page.py` (or extend `toolkit_detail_page.py` if the lead prefers unifying create+detail, since Form/Raw Json view toggling and field locators are identical between create and detail — confirmed during exploration: `toolkit-field-*` testids are present and behave identically on both `/mcps/create/mcp` and `/mcps/all/{id}`).
- Use `ToolkitAPI` (`automation/api/client.py`) for teardown (`delete_toolkit(toolkit_id)`) — already exists, no new API client code needed.
- Wait strategy: wait for the `POST .../tools/prompt_lib/{project}` response (`201`) before asserting navigation to the detail page, not a fixed timeout or URL-poll — the save button's `onClick` triggers an async event-emitter chain (`ToolEvents.SaveEvent`) with a `setTimeout(..., 0)` inside (`CreateToolkitToolTabBar.jsx`), so a network-response wait is the correct signal, not a UI-state poll.
- Headers JSON editor is CodeMirror, not a plain `<textarea>` — clearing existing content requires `Ctrl/Cmd+A` then type, not `.fill()`.
- Client Secret masked-field assertions: never assert the literal secret value, and never a bare `!= plaintext` check (lets an empty/garbage render pass undetected). The two views use **different syntax for the same hex id** — Raw JSON (`settings.client_secret`) is the full `{{secret\.[A-Za-z0-9_]+}}` wrapper (regex: `^\{\{secret\.([A-Za-z0-9_]+)\}\}$`, confirmed at `SecretField.jsx` line 20's `secretRegex` in EliteaUI source), while the Form view's `toolkit-field-client_secret-input-field` DOM value is the **bare hex** (`^[0-9a-f]{32}$`, no wrapper — confirmed live at implementer Phase 4, corrects this AFS's earlier claim that the Form view also shows the wrapper). Match each view against its own shape, then cross-check the two extracted hex ids are equal — that equality is what actually proves the Form-view value is the secret-reference id and not a coincidentally hex-shaped string.
- If the test harness ever navigates away from a filled-but-unsaved form (e.g., on a mid-test failure path), expect a native `beforeunload` confirm dialog — register a `page.on('dialog', d => d.accept())` handler or an equivalent Playwright dialog-auto-accept fixture before that navigation, or the run will hang.
