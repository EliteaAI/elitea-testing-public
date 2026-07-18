# Test Case: Delete Remote MCP

## Metadata
- **TMS ID**: ELITEA-1947
- **Linked Story**: none
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths the dev server, confirmed "Elitea is connected" in the sidebar after page load)
- **Analyst**: qa-engineer (agent), session 2026-07-18
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (on localhost this is automatic via `VITE_DEV_TOKEN`; on deployed envs, standard Keycloak login via `${TEST_USER}`).
- Project context is set (sidebar shows `Project: <name>`; project id read from `${ELITEA_PROJECT_ID}`).
- No precondition data needs seeding — this is a self-contained create-then-delete flow.

## Test Data

### generate-per-test (created in test setup via the UI, deleted by the test's own steps — this case's subject under test IS the delete flow, so no separate teardown deletion is needed on the happy path)
- Toolkit Name: `autotest_mcp_to_delete` — matches case Test Data exactly. Uniqueness against a name collision from a prior failed/aborted run was **not verified live** (out of scope for this case, same caveat as ELITEA-1922's AFS) — if the implementer's suite runs this case repeatedly without the delete succeeding (e.g. a run that fails between create and delete), a stale MCP with this exact name may already exist. Recommend a defensive pre-check/cleanup in test setup (list-search for the name, delete via `ToolkitAPI.delete_toolkit()` if found) rather than assuming the name is always free.
- URL: `https://mcp.example.com/sse`

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.

## Test Steps

1. Navigate to `${BASE_URL}/mcps/create` (via the sidebar's `sidebar-create-button` quick-create, or direct navigation), select the Remote MCP type card, fill Toolkit Name = `autotest_mcp_to_delete` and Url = `https://mcp.example.com/sse`, click Save.
   - **Verify**: `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` returns `201 Created`; page navigates to `${BASE_URL}/mcps/all/{id}?name=autotest_mcp_to_delete`.
2. Navigate to the MCP list (`${BASE_URL}/mcps/all`, e.g. via the sidebar "MCPs" nav item) and verify the created MCP appears.
   - **Verify**: `autotest_mcp_to_delete` is present among the `entity-card-name` collection.
3. Click the MCP's card from the list to open its detail page.
   - **Verify**: URL becomes `${BASE_URL}/mcps/all/{id}?...&name=autotest_mcp_to_delete`; Toolkit Name field shows `autotest_mcp_to_delete`.
4. Click the three-dot actions menu button (`controls-menu-button`).
   - **Verify**: menu opens (`controls-menu`) showing `Export` (disabled), `Fork` (disabled), `Copy link`, `Pin to top`, `Delete`.
5. Click the "Delete" menu item.
   - **Verify**: the confirmation dialog opens (delete action is triggered).
6. Verify the confirmation dialog's content.
   - **Verify**: dialog title = "Delete confirmation"; body text = `Are you sure to delete the autotest_mcp_to_delete? Enter the name to complete the action.`; a Name text field is present; the dialog's "Delete" button is **disabled** until the typed name matches exactly (type-to-confirm safety gate — case text doesn't mention this mechanic explicitly, see Coverage Map Axis 2).
7. Type `autotest_mcp_to_delete` into the Name field, then click the dialog's "Delete" button.
   - **Verify**: typing the exact name enables the "Delete" button; clicking it fires `DELETE /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}` → `204 No Content`.
8. Verify redirect to the MCP list page.
   - **Verify**: URL becomes `${BASE_URL}/mcps/all` (no id segment). **Automation-critical caveat**: this redirect is implemented as a browser-history "go back" (see § Known Defects Found / Automation Hints) — it only lands on the list page reliably when the detail page was opened by navigating there FROM the list (step 3's path), matching this AFS's step ordering. Do not shortcut steps 2–3 by asserting against the create flow's own post-save detail-page redirect (see below).
9. Verify `autotest_mcp_to_delete` no longer appears in the MCP list.
   - **Verify**: `entity-card-name` collection on `/mcps/all` does not contain `autotest_mcp_to_delete`.
10. Reload the page and verify the deletion persisted.
    - **Verify**: after a full page reload of `/mcps/all`, `entity-card-name` collection still does not contain `autotest_mcp_to_delete`.

## Expected Results
- The MCP "autotest_mcp_to_delete" is created, then permanently deleted via the three-dot menu → Delete → type-to-confirm dialog.
- `DELETE /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}` returns `204 No Content`.
- User lands back on the MCP list page (`/mcps/all`) after confirming deletion, **provided the detail page was reached via the list** (see step 8 caveat).
- The MCP is absent from the list immediately after deletion and remains absent after a full page reload (deletion is persisted server-side, not just a client-side optimistic removal).
- No new console errors are introduced by the delete flow itself (the three pre-existing dev-mode warnings from the create form's `ToolkitTypeSelector`/`ToolBaseProperty`/MUI Tabs components fire on page load regardless of this case's actions — see Known Defects Found).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in | dev-server auto-auths via `VITE_DEV_TOKEN` | step 1 | sidebar "Elitea is connected" state observed before any action | asserted |
| 1 Create a Remote MCP named "autotest_mcp_to_delete" with URL "https://mcp.example.com/sse" | MCP is created successfully | step 1 | step 1: `201 Created` + navigation to detail page | asserted |
| 2 Verify it appears in MCP list | MCP appears in the list | step 2 | step 2: `entity-card-name` collection contains the name | asserted |
| 3 Open MCP detail page | Detail page loads | step 3 | step 3: URL + Toolkit Name field | asserted |
| 4 Click three-dot menu button | Menu opens | step 4 | step 4: `controls-menu` visible with expected items | asserted |
| 5 Click "Delete" menu item | Delete action is triggered | step 5 | step 5: confirmation dialog opens | asserted |
| 6 Verify confirmation dialog appears | Confirmation dialog is displayed | step 6 | step 6: dialog title + body text + Name field | asserted |
| 7 Confirm deletion | Deletion is confirmed | step 7 | step 7: `204 No Content` on the DELETE request | asserted *(decomposed: case step 7 folds "type name" + "click Delete" into one; this AFS keeps them as one step since the case's own step 6/7 split doesn't separate them either)* |
| 8 Verify redirect to MCP list page | User is redirected to the MCP list | step 8 | step 8: URL becomes `/mcps/all` | asserted — **with the automation-critical caveat above; see Known Defects Found for the investigation that ruled this NOT a product defect** |
| 9 Verify "autotest_mcp_to_delete" no longer appears in list | MCP is absent from the list | step 9 | step 9: `entity-card-name` collection | asserted |
| 10 Reload page — verify deletion persisted | MCP is still absent after reload | step 10 | step 10: `entity-card-name` collection after `page.reload()` | asserted |
| Expected Final State: MCP permanently removed, absent after reload | — | steps 7–10 | steps 7–10 | asserted |
| Pass/Fail Criteria: all steps complete without errors; MCP deleted and absent after reload | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- `step 6`/`step 7` assert the type-to-confirm safety gate (Delete button starts disabled, only enables once the typed name exactly matches the entity name) — *added: the case text says "Confirm deletion" but doesn't call out that this is a guarded, type-to-confirm action rather than a single click; worth asserting since a regression that removes or weakens this gate (e.g. Delete becomes clickable without a matching name) would be a real safety regression the case's literal wording wouldn't catch.*
- `step 8` documents the `navigate(-1)` browser-history-back redirect mechanism as a caveat, not a defect — *added: during exploration, deleting immediately from the create-flow's own post-save detail page (skipping an explicit visit to the list first) redirected to `/mcps/create` instead of `/mcps/all`. Re-running with the case's own literal step order (create → visit list → open from list → delete) redirected correctly to `/mcps/all`. This is `window.history.length`-dependent `navigate(-1)` behavior (`DeleteToolkitButton.jsx`), not a defect — see Known Defects Found for the full investigation and why it was NOT filed.*
- No console-error assertion added beyond noting the pre-existing warnings — same reasoning as ELITEA-1922's AFS (issue #291 already tracks them; they're unrelated to this case's actions and fire on page load regardless).

## Cleanup

1. This case's own steps ARE the cleanup — the MCP created in step 1 is deleted by steps 5–7, and both id `1474` and `1475` (the two MCPs created during this exploration session, see below) were confirmed deleted via `204 No Content` + list-absence + persisted-absence-after-reload. **No leftover MCP entities remain from this analysis session.**
2. If a test run fails between step 1 (create) and step 7 (confirm delete), a stale `autotest_mcp_to_delete` MCP could be left behind for the next run — see Test Data § generate-per-test for the recommended defensive pre-check. As a fallback, `ToolkitAPI.delete_toolkit(toolkit_id)` (`automation/api/client.py`, confirmed present, calls `DELETE {ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`) is available for API-level teardown.

## Concrete Handles (discovered during exploration)

All testids below were verified live against `http://localhost:5173` (`EliteaAI/EliteaUI` @ `automation/testids`) on 2026-07-18. Provenance verified fresh via `cd ../EliteaUI && git fetch origin` immediately before writing this table, then `git grep`/`git show` against `origin/main` vs `automation/testids` for the JSX file that renders each testid (not a literal-string grep alone — several of these testids are runtime template literals, e.g. `` `toolkit-type-card-${itemKey}` ``, which a plain string grep misses).

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Sidebar quick-create MCP button | `[data-testid="sidebar-create-button"]` | on-main ✓ | `CreateEntityButton.jsx` |
| Remote MCP type-selector card | `[data-testid="toolkit-type-card-mcp"]` | on-automation/testids only (awaiting human promotion to main) | `CategoryItemCard.jsx`, `` data-testid={`toolkit-type-card-${itemKey}`} ``; already used by `mcp_form_page.py::remote_mcp_type_card` |
| Toolkit Name input | `[data-testid="toolkit-form-name-input"]` | on-automation/testids only | `NameDescriptionInput.jsx`; already used by `mcp_form_page.py::name_input` |
| Url input | `[data-testid="toolkit-field-url-input"]` | on-automation/testids only | already used by `mcp_form_page.py::url_input` |
| Save button (create form) | `[data-testid="toolkit-form-save-button"]` | on-automation/testids only | already used by `mcp_form_page.py::save_button` |
| MCP list card name (collection) | `[data-testid="entity-card-name"]` | on-main ✓ | `Card.jsx`; already used by `mcp_list_page.py::mcp_card_name` |
| MCP list card container (collection) | `[data-testid="entity-card"]` | on-main ✓ | `Card.jsx`; already used by `mcp_list_page.py::mcp_card` |
| Three-dot actions menu button | `[data-testid="controls-menu-button"]` | on-main ✓ | `ControlsDropdown.jsx` → `DotMenu.jsx`, default `id="controls"` prop — SAME generic testid already used by `CredentialDetailPage.controls_menu_button`; `ToolkitsControls.jsx` (Toolkit **and** MCP detail pages both render via this same component) calls `<Controls.ControlsDropdown menuItems={items} />` with no `id` override, so this testid is shared across Toolkits, MCP, and Credentials detail pages — confirmed live on the MCP detail page in this session |
| Three-dot actions menu (popup) | `[data-testid="controls-menu"]` | on-main ✓ | same component/mechanism as above |
| "Delete" menu item | **testid needed: `toolkit-actions-delete-menuitem`** | gap confirmed on BOTH `origin/main` and `automation/testids` | `DeleteToolkitButton.jsx`'s `useDeleteToolkitMenu()` builds `menuItem = { label: 'Delete', icon, confirmText, alarm, disabled, entityName, onConfirm }` with **no `key`** — `DotMenu.jsx`'s `BasicMenuItem`/`ActionWithDialog` only renders `data-testid={testId ? `${testId}-menuitem` : undefined}` where `testId: item.key`, so today this `<li role="menuitem">Delete</li>` has **no `data-testid` at all** (confirmed live: `null`). Fix is a one-line `key: 'toolkit-actions-delete'` addition to the `menuItem` object (mirrors the sibling `Fork` item's `key: FORK_MENU_ITEM_KEY_BY_ENTITY[entity_name] ?? 'entity-actions-fork'` in `ForkEntityButton.jsx`, which already yields `toolkit-actions-fork-menuitem` — confirmed live). Naming `toolkit-actions-delete-menuitem` matches that sibling's `{section}-{element}-{type}` shape. **Do not confuse with Credentials' `delete-credentials-menuitem`** — Credentials writes its OWN inline menu item in `CredentialsControls.jsx` (not via this shared hook), so its Delete item already has a testid; Toolkits/MCP do not share that fix. |
| Confirmation dialog container | **testid needed: `delete-confirm-dialog`** | gap confirmed on BOTH `origin/main` and `automation/testids` | `Modal.DeleteEntityModal` (`src/[fsd]/shared/ui/modal/DeleteEntityModal.jsx`) renders via `Modal.BaseModal`, which DOES support a `data-testid` prop on its underlying `<Dialog>` — but `DeleteEntityModal` never passes one. This is a SHARED component with ~15 call sites (Skills, Agents, Credentials, Pipelines, Artifacts, Users, this MCP flow, …) — per locator policy a shared component gets a GENERIC testid, not a feature-scoped one. `delete-confirm-dialog` follows the same generic-naming family as the ALREADY-EXISTING `delete-confirm-name-input` (see below), so add it the same way: hardcoded directly in `DeleteEntityModal.jsx`'s own `<Modal.BaseModal data-testid="delete-confirm-dialog" ...>` call (not a caller-supplied prop — this component's content is already fixed/generic, matching the existing `delete-confirm-name-input` precedent). Confirmed live: `document.querySelector('[role="dialog"]')` returns MULTIPLE dialogs on this page (3 hidden "MCP Authorization" OAuth dialogs plus the real Delete-confirmation one) — a role-based selector is not just against locator policy here, it is also genuinely ambiguous; a testid is the ONLY reliable way to target this dialog. |
| Confirmation dialog "Delete" button | **testid needed: `delete-confirm-button`** | gap confirmed on BOTH `origin/main` and `automation/testids` | `DeleteEntityModal.jsx` renders its OWN `actionsNode` (bypassing `BaseModal`'s built-in `confirmButtonTestId`/`cancelButtonTestId` props entirely) using `<Button.OneClickButton title={confirmButtonText} ... onClick={onConfirm} />`. **Two-part fix needed**: (1) `OneClickButton.jsx` (`src/[fsd]/shared/ui/button/OneClickButton.jsx`) destructures only `{ disabled, disableRipple, color, onClick, title }` and does NOT forward extra props (including `data-testid`) to the underlying `BaseBtn` — it needs a `'data-testid': testId` (or similar) prop added and passed through; (2) `DeleteEntityModal.jsx`'s `actionsNode` needs to pass that prop with the generic value `delete-confirm-button`. (By contrast, `Button.BaseBtn`, used for the dialog's Cancel button, DOES already spread `...restProps` onto the MUI `Button` — so if a Cancel testid is ever needed, only `DeleteEntityModal.jsx` itself needs a one-line change, not `BaseBtn.jsx`. Cancel is NOT touched by this case's happy path, so no testid is requested for it here — see § Automation Hints re: scope.) |
| Confirmation dialog Name (type-to-confirm) input | `[data-testid="delete-confirm-name-input"]` | on-main ✓ | `DeleteEntityModal.jsx` — **this testid resolves to the MUI `TextField`'s outer `MuiFormControl-root` wrapper `<div>`, NOT the real `<input>`** (the actual `<input name="name" id="name">` is nested inside). Confirmed live this is still usable for fill purposes: clicking the wrapper focuses the inner input (browser default click-delegation), and Playwright's `press_sequentially()`/`type()` on the wrapper locator successfully typed into the focused input (verified: `input.value === 'autotest_mcp_to_delete'` after). **Do NOT use `.input_value()` on this locator** (it will throw — the locator isn't an `<input>`/`<textarea>`/`<select>` element); if a future case needs to read back the typed value, request a dedicated `-field` testid on the real `<input>`, mirroring the `toolkit-field-client_secret-input` vs `-input-field` split pattern already used elsewhere in this codebase (ELITEA-1922 AFS). Not needed for THIS case since we only fill, never read back. |

## Network Behavior
- `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` — fires on create-form Save click; `201 Created` on success; response body's `id` is the new toolkit id (observed `1474` then `1475` across two exploration passes).
- `GET /api/v2/elitea_core/toolkits/prompt_lib/${PROJECT_ID}?mcp=true` — fires on `/mcps/all` list-page load; this is what populates the `entity-card-name` collection for steps 2 and 9.
- `DELETE /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}` — fires on the confirmation dialog's Delete button click; `204 No Content` on success (confirmed both exploration passes: id `1474` and id `1475`). Wait for this response before asserting the step 8 redirect, not a fixed timeout.
- A `GET /api/v2/elitea_core/toolkits/prompt_lib/${PROJECT_ID}?mcp=true` refetch also fires immediately after the successful DELETE (list re-fetch, confirmed in network log) — this is what step 9's list-absence assertion should wait on rather than a fixed timeout.

## Known Defects Found During Exploration

**None found in the MCP delete flow itself.** The DELETE API call, list-absence, and reload-persistence all behaved correctly (`204 No Content`, absent from list, still absent after `page.reload()`).

**One apparent anomaly was investigated and ruled NOT a defect** (documented here per the reverse-masking / pristine-repro-gate discipline, so it isn't silently dropped nor mis-filed):

- During the FIRST exploration pass, deleting the MCP immediately from the create-flow's own post-save detail page (i.e. create → stay on `/mcps/all/{id}` → delete, skipping an explicit visit to the list in between) redirected to `/mcps/create` (the type-picker) instead of `/mcps/all` (the list) after confirming deletion. This looked like it could satisfy the case's step 8 failure condition ("Confirmation dialog is missing" / wrong redirect target).
- Root-caused via source inspection: `DeleteToolkitButton.jsx`'s `useDeleteToolkit()` navigates via `window.history.length > 1 ? navigate(-1) : navigate(MCPsWithTab)` — i.e. "go back one browser-history entry" rather than a fixed route. In the first pass, the immediately-prior history entry was the create flow's own type-picker page (`/mcps/create`), not the list.
- **Re-ran clean, following the case's OWN literal step order** (create → navigate to list via sidebar "MCPs" → click into the card from the list → three-dot menu → Delete → confirm) with a fresh second MCP (id `1475`). This time the redirect correctly landed on `/mcps/all`. Screenshot evidence: `test-results/screenshots/ELITEA-1947-step7b-confirm-dialog-realistic-path.png` (dialog state) and `test-results/screenshots/ELITEA-1947-step9-list-after-delete-absent.png` (post-redirect list state, URL `/mcps/all`).
- **Verdict: NOT a product defect for this case.** The case's own step sequence (create → verify in list → open FROM the list → delete) is exactly the path that makes `navigate(-1)` land on the list. The first pass's misleading result was an artifact of my own shortcut (skipping steps 2–3's actual navigation), not a reproducible product bug. No issue filed — filing it would have been a false positive.
- **This is still an automation-critical fact**, captured in step 8's caveat and Axis 2: an automated test for this case MUST follow the same step order (open the detail page via a list-card click, not via staying on the create flow's own redirect) or it will flakily/incorrectly observe the wrong redirect target and could misreport a defect that isn't real.

Three pre-existing, unrelated console warnings fire on every load of `/mcps/create` (create-form load) regardless of this case's actions — already tracked as `EliteaAI/elitea-testing-public#291` (filed during ELITEA-1922 analysis): (1) missing `key` prop in `CategorySection`/`GroupedCategory`; (2) invalid `<p>`-in-`<p>` DOM nesting from `InfoTooltip`; a third `MUI: The value provided to the Tabs component is invalid` warning was also observed at `/mcps/create` in this session (same load-time trigger, not tied to any of this case's 10 steps) — not filed separately since it's the same "fires on page load, unrelated to the action under test" pattern already covered by #291's disposition; flagging here in case #291 needs its scope widened, not as a new defect.

## Blocked Steps

None. All 10 case steps were executed to completion against the live local environment, twice (once to discover the history-redirect nuance, once clean per the case's own step order).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`).
- Page objects: `automation/pages/mcp_form_page.py` (create form fields + save — all reusable as-is: `navigate_to_create()`, `select_remote_mcp_type()`, `fill_name()`, `fill_url()`, `save_and_wait_for_created()`) and `automation/pages/mcp_list_page.py` (`navigate()`, `get_card_names()` — reusable as-is). **Neither page object currently has methods for**: opening a card by name from the list (mirror `CredentialDetailPage.open_credential_by_name()` — click the `entity-card`/`entity-card-name` collection filtered by text, same pattern), the three-dot controls menu (mirror `CredentialDetailPage.controls_menu_button` / `open_controls_menu()` — same testid, same mechanism), or the delete-confirm dialog. All of this is new page-object work for the implementer, most of it a straight port of the existing `CredentialDetailPage` pattern rather than novel exploration.
- Wait strategy: wait for the `DELETE .../tool/prompt_lib/{project}/{id}` response (`204`) before asserting the step 8 redirect; wait for the post-delete `GET .../toolkits/prompt_lib/{project}?mcp=true` refetch (or `wait_for_network()`) before asserting step 9's list-absence, not a fixed timeout.
- The confirm dialog is NOT the only `[role="dialog"]` on the page at delete time (3 hidden MCP-OAuth-authorization dialogs are also present in the DOM) — this is exactly why the `delete-confirm-dialog`/`delete-confirm-button` testids (see Concrete Handles) are required rather than falling back to a role-based dialog selector; a `getByRole('dialog')` would be ambiguous even setting locator policy aside.
- **Step-order caveat is load-bearing for correctness, not just style**: implement steps 2–3 as real navigations (list → click card) rather than reusing the create flow's own post-save detail-page reference, or step 8's redirect-to-list assertion will be flaky/wrong (see Known Defects Found).
- `delete-confirm-name-input` resolves to the TextField wrapper, not the real `<input>` — click + `press_sequentially()`/`type()` on it works for filling (verified live), but never call `.input_value()` on it.
