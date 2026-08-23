# Test Case: Edit Remote MCP — Change Name

## Metadata
- **TMS ID**: ELITEA-1925
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `priority: critical`; case body text says
  "**Priority:** medium" — the same pre-existing internal inconsistency the
  ELITEA-1929 AFS records for this case family; frontmatter is authoritative)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`
  auto-auths the dev server)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- Project context is set; project id read from `${ELITEA_PROJECT_ID}`.
- A Remote MCP exists in the project and is reachable at `/mcps/all/{id}`.

## Test Data

### generate-shared-with-cleanup

The case text names an existing Remote MCP called **"Web Search"** with a rename
to **"Web Search Renamed"**. No such MCP exists in this project, and
`ToolkitAPI.list_all_toolkits()` returns an empty list on this environment
regardless of auth method (documented quirk — see `config.py`'s
`remote_github_mcp_toolkit_id` comment and the ELITEA-1927/1929 AFS files), so
there is no reliable read-only way to rediscover an existing Remote MCP's id at
runtime. Additionally, renaming is inherently destructive to whatever toolkit is
used. Therefore, per Hard Rule 10, the test **seeds its own disposable Remote MCP
via the UI create flow** and deletes it in teardown — the same precedent shipped
for ELITEA-1927 and ELITEA-1929.

| Field | Case value | Automated value | Why |
|---|---|---|---|
| Original Name | `Web Search` | `autotest_mcp_rename_<6hex>` (26 chars) | seeded, collision-free; `MAX_NAME_LENGTH = 32` truncates silently |
| New Name | `Web Search Renamed` | `autotest_renamed_<6hex>` (23 chars) | same suffix, so the pair is traceable to one run |
| Url | (not in case data) | `https://mcp.example.com/sse` | never dialled — this case never clicks Load Tools (digest § Fixtures addendum) |

## Test Steps

Live-executed 2026-08-24 against `http://localhost:5173` on a seeded MCP
(`autotest_mcp_rename_ed7db0`, toolkit id 3024). Observed values below are the
literal probe output.

| # | Action | Expected (case) | Observed live |
|---|---|---|---|
| 1 | Navigate to the MCP detail page (`/mcps/all/{id}`) | Detail page loads with tab showing MCP name | Form view active (`form_view_toggle` `aria-pressed="true"`); detail title = `autotest_mcp_rename_ed7db0` |
| 2 | Verify detail page/tab shows the MCP name | Tab shows the original name | `toolkit-detail-title` text == seeded name; `toolkit-form-name-input` value == seeded name |
| 3 | Click into "Toolkit Name *" and edit | Field becomes editable | Editable; pristine state confirmed: Save **disabled**, Discard **disabled** |
| 4 | Change name to the new name | Field displays updated name | `name_input.input_value()` == `autotest_renamed_ed7db0` |
| 5 | Verify Save and Discard become enabled | Both active | Save `disabled == False`, Discard `disabled == False`. **Both gate on the same `isFormDirtyExcluding` flag** (`ToolkitsTabBarContainer.jsx:102-109,157-160`) — this is a genuine dirty-state assertion, unlike the *create* form's Save (see digest § Save-button gating / #633). |
| 6 | Click Save | Operation completes; confirmation or updated state shown | `PUT /tool/prompt_lib/{project}/{id}` → **200**, body `name` == new name. **No success toast is rendered on this surface** — `toast-message` never appears within 5 s (two probes). The case's "confirmation **or** updated state" is satisfied by the 200 + the updated state asserted in steps 7-9; do not assert a toast. |
| 7 | Verify the header updates | Header shows the new name | Header **does** update to the new name, but **not synchronously with the PUT**: an immediate read right after the PUT resolved still returned the OLD name (probe 1); a read ~5 s later returned the NEW name (probe 2, stable at +2/+5/+10 s and after a full reload). **This is a re-render lag, not a defect** — assert with a retrying web-first assertion (`expect(...).to_have_text(...)`), never a bare `text_content()` read. |
| 8 | Navigate to the MCP list; verify the updated name appears | List shows the new name | `McpListPage.search(new_name)` → `get_card_names()` == `['autotest_renamed_ed7db0']` |
| 9 | Reopen the MCP; verify the name persisted | Detail shows the new name | Opened from the list card: title == new name, `name_input` value == new name |
| 10 | Rename back to the original and save | Name restored | Second `PUT` → 200; after `reload_and_wait()` the name field reads the original name again (header again needs the retrying assertion) |

## Expected Results
- The Toolkit Name field is editable on the detail page; editing it dirties the
  form and enables both Save and Discard.
- Save issues a `PUT .../tool/prompt_lib/{project}/{id}` returning 200 whose body
  carries the new name.
- The new name is reflected in the detail header (eventually-consistent), in the
  MCP list, and after reopening the MCP.
- Renaming back to the original restores the name (this doubles as cleanup of the
  rename; the seeded toolkit itself is deleted in teardown).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: logged in | precondition | framework `auth_state` (localhost `VITE_DEV_TOKEN`) |
| Precondition: existing Remote MCP "Web Search" | precondition (substituted) | seeded via UI create flow — see § Test Data |
| Step 1 — open detail page | asserted | Form view `aria-pressed == "true"` + detail title == seeded name |
| Step 2 — tab shows MCP name | asserted | `toolkit-detail-title` text + `toolkit-form-name-input` value |
| Step 3 — name field editable | asserted | pristine Save/Discard both disabled, then fill succeeds (value read back) |
| Step 4 — field shows updated name | asserted | `name_input.input_value() == new_name` |
| Step 5 — Save + Discard enabled | asserted | `detail_save_button.is_disabled() is False` and `detail_discard_button.is_disabled() is False` |
| Step 6 — Save completes | asserted | PUT 200 response body `id`/`name` (network-level, not a UI poll) |
| Step 7 — header updates | asserted | `expect(detail_title).to_have_text(new_name)` (retrying — see step-7 note) |
| Step 8 — list shows updated name | asserted | `McpListPage.search()` + `get_card_names()` contains new name |
| Step 9 — reopen shows persisted name | asserted | reopened via list card: title + name field both == new name |
| Step 10 — rename back to original | asserted | second PUT 200 + post-reload name field == original name |
| Pass criterion: no errors during the flow | asserted | console-error listener (known #291/#549 filtered/soft, same pattern as the sibling MCP edit specs) |

### Axis 2 — Analyst additions

| Addition | Why grounded |
|---|---|
| Pristine-state assertion (Save/Discard **disabled** before editing) | Step 5 asserts they *become* enabled; without the pristine baseline the assertion proves nothing. The detail-page gate is `!isFormDirtyExcluding`, verified in source. |
| PUT-response assertion (status 200, `name` in body) | Step 6's "operation completes" is otherwise unobservable — there is no toast on this surface (confirmed twice live). |
| Post-reload read in step 10 | The case's step 10 only says "restored"; a reload distinguishes server-side persistence from client state, consistent with the sibling ELITEA-1929 spec. |
| Console-error monitoring | Case Pass criterion "All steps complete without errors". |

## Cleanup
- Step 10 (rename back) is the case's own cleanup of the rename.
- The **seeded toolkit** is deleted in a `finally:` block via
  `ToolkitAPI.delete_toolkit(id)` — identical to ELITEA-1927/1929.

## Concrete Handles (discovered during exploration)

| Element | Handle | Provenance |
|---|---|---|
| Toolkit Name input | `toolkit-form-name-input` | on-main ✓ (pre-existing, used by merged specs) |
| Detail title / header | `toolkit-detail-title` | on-main ✓ |
| Detail Save button | `toolkit-detail-save-button` | on `automation/testids` (added ELITEA-1929, EliteaUI PR #572) |
| Detail Discard button | `toolkit-detail-discard-button` | on `automation/testids` (added ELITEA-1929, EliteaUI PR #572) |
| Form / Raw Json view toggles | `toolkit-form-view-toggle` / `toolkit-raw-json-view-toggle` | on-main ✓ |
| MCP list card name | `entity-card-name` (via `McpListPage.get_card_names`) | on-main ✓ |
| MCP list search | `search-input` / send button (via `McpListPage.search`) | on-main ✓ |
| Toast (NOT used) | `toast-message` | exists app-wide but is **not rendered** by this flow |

No new testid is required for this case — every handle already exists.

## Network Behavior
- `GET /tool/prompt_lib/{project}/{id}` on detail load (awaited by
  `McpFormPage.navigate_to_detail`).
- `PUT /tool/prompt_lib/{project}/{id}` → 200 on each Save (awaited by
  `save_and_wait_for_updated`).
- `POST /tools/prompt_lib/{project}` → 201 for the seed create.
- List search is client-driven over the already-fetched list.

## Known Defects Found During Exploration
None. The header lag in step 7 was investigated across two probes and is a
render-timing characteristic that a retrying assertion covers honestly — it
converges without any user action and survives reload. It is **not** filed as a
defect and is **not** masked: the assertion still requires the header to show the
new name.

## Blocked Steps
None.

## Automation Hints
- Reuse `McpFormPage` end-to-end; no page-object surgery is needed beyond what
  ELITEA-1923/1924 already landed.
- **Never read the header with a bare `text_content()` right after Save** — use
  `expect(form.detail_title).to_have_text(...)`. This is the single trap in this case.
- `MAX_NAME_LENGTH = 32` truncates silently; keep generated names ≤ 32.
- The MCP list is reachable via `McpListPage.navigate()` + `wait_for_page_load()`;
  `search()` then `get_card_names()` is the cheapest list assertion.
