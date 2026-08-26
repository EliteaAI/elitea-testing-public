# Test Case: Edit Remote MCP — Change URL

## Metadata
- **TMS ID**: ELITEA-1926
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `priority: critical`; case body says
  "medium" — same pre-existing inconsistency recorded in the ELITEA-1929 AFS;
  frontmatter authoritative)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: `VITE_DEV_TOKEN` auto-auth)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated; project id from `${ELITEA_PROJECT_ID}`.
- A Remote MCP exists and its detail page is open in Form view.

## Test Data

### generate-shared-with-cleanup

Same reasoning as ELITEA-1925: no discoverable pre-existing Remote MCP
(`ToolkitAPI.list_all_toolkits()` returns empty on this environment), and editing
a URL is destructive to whatever toolkit is used → the test seeds its own
disposable Remote MCP through the UI create flow and deletes it in teardown
(precedent: ELITEA-1927, ELITEA-1929).

| Field | Value | Why |
|---|---|---|
| Seed name | `autotest_mcp_url_<6hex>` (23 chars) | ≤ `MAX_NAME_LENGTH = 32` |
| Original Url | `https://mcp.example.com/sse` | stored only; never dialled (no Load Tools in this case) |
| New Url | `https://new-mcp-server.example.com/sse` | **verbatim from the case's Test Data table** |

## Test Steps

Live-executed 2026-08-24 against `http://localhost:5173` (seeded toolkit id 3024).

| # | Action | Expected (case) | Observed live |
|---|---|---|---|
| 1 | Open the Remote MCP detail page in Form view | Detail page loads in Form view | `form_view_toggle` `aria-pressed == "true"`; detail title == seeded name |
| 2 | Note the current value of the "Url *" field | Current URL observed | **`toolkit-field-url-input` count == 0 until the configuration section is expanded** (digest § MCP DETAIL page: configuration fields are COLLAPSED). After `expand_configuration_section()`: value == `https://mcp.example.com/sse` |
| 3 | Clear the Url field and enter the new URL | Field displays the new URL | `url_input.input_value() == "https://new-mcp-server.example.com/sse"` (`McpFormPage.fill_url` clears + refills and waits for the value to settle) |
| 4 | Verify Save becomes enabled | Save clickable | `detail_save_button.is_disabled() is False` (dirty-gated, `ToolkitsTabBarContainer.jsx:102-109`) |
| 5 | Click Save | Operation completes successfully | `PUT /tool/prompt_lib/{project}/{id}` → **200**, response body `settings.url == "https://new-mcp-server.example.com/sse"` |
| 6 | Reload the page; verify the new URL persisted in the "Url *" field | Field shows the new URL | After `reload_and_wait()` the url field is **again count == 0 until expanded** (the collapse state is not remembered); after expanding, value == the new URL |
| 7 | Switch to Raw Json view; verify the `url` field matches | JSON `url` shows the updated URL | `get_raw_json()["settings"]["url"] == "https://new-mcp-server.example.com/sse"`. Note the URL lives under **`settings.url`**, not at the JSON root — the case text says only `"url" field`. |

## Expected Results
- The Url field is editable on the detail page and dirties the form.
- Save issues a `PUT` returning 200 whose body carries the new `settings.url`.
- The new URL survives a full page reload (server-side persistence, not client state).
- The Raw Json view shows the same new URL.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: logged in | precondition | framework `auth_state` |
| Precondition: existing Remote MCP open in Form view | precondition (substituted seed) | seeded via UI create flow — see § Test Data; Form view asserted in step 1 |
| Step 1 — detail page loads in Form view | asserted | `form_view_toggle` `aria-pressed == "true"` + detail title == seeded name |
| Step 2 — note current URL | asserted | `url_input.input_value() == "https://mcp.example.com/sse"` after expanding configuration |
| Step 3 — clear + enter new URL | asserted | `url_input.input_value() == new_url` |
| Step 4 — Save becomes enabled | asserted | `detail_save_button.is_disabled() is False` |
| Step 5 — Save completes | asserted | PUT 200 + body `settings.url == new_url` |
| Step 6 — reload; field persisted | asserted | post-reload `url_input.input_value() == new_url` |
| Step 7 — Raw Json `url` matches | asserted | `get_raw_json()["settings"]["url"] == new_url` |
| Pass criterion: no errors during the flow | asserted | console-error listener (known #291/#549 filtered/soft, sibling-spec pattern) |

### Axis 2 — Analyst additions

| Addition | Why grounded |
|---|---|
| Pristine Save assertion before editing (disabled) | Step 4 asserts Save *becomes* enabled — the baseline makes it meaningful; the gate is `!isFormDirtyExcluding`, read in source. |
| PUT-response body assertion | Step 5's "completes successfully" is otherwise only observable as "nothing visibly broke" — no toast is rendered on this surface (confirmed live on the sibling ELITEA-1925 probe). |
| Explicit `expand_configuration_section()` before every url read | The detail page renders **no** `toolkit-field-*` node until expanded — without this the case's steps 2/6 cannot be executed at all. |
| Console-error monitoring | Case Pass criterion "All steps complete without errors". |

## Cleanup
The seeded toolkit is deleted in a `finally:` block via
`ToolkitAPI.delete_toolkit(id)`. No shared state is mutated, so no other cleanup
is required (the URL change dies with the toolkit).

## Concrete Handles (discovered during exploration)

| Element | Handle | Provenance |
|---|---|---|
| Url input | `toolkit-field-url-input` | on-main ✓ (collapsed until show-more, see below) |
| Configuration show-more | `toolkit-configuration-show-more` | on `automation/testids` |
| Detail Save button | `toolkit-detail-save-button` | on `automation/testids` (ELITEA-1929, EliteaUI PR #572) |
| Form view toggle | `toolkit-form-view-toggle` | on-main ✓ |
| Raw Json view toggle / editor | `toolkit-raw-json-view-toggle` / `toolkit-raw-json-editor-content` | on-main ✓ |
| Detail title | `toolkit-detail-title` | on-main ✓ |

No new testid is required for this case.

## Network Behavior
- `POST /tools/prompt_lib/{project}` → 201 (seed).
- `GET /tool/prompt_lib/{project}/{id}` on detail load and after reload.
- `PUT /tool/prompt_lib/{project}/{id}` → 200 on Save.
- The new URL is **never dialled** — nothing in this case triggers `mcp_sync_tools`.

## Known Defects Found During Exploration
None.

## Blocked Steps
None.

## Automation Hints
- `expand_configuration_section()` is required **twice**: once on first load and
  once again after `reload_and_wait()` (the section re-collapses).
- Use `get_raw_json()` (not `get_raw_json_full()`): this toolkit has no
  discovered tools, so the payload is short and not virtualization-truncated.
- The Raw Json `url` is nested under `settings`.
