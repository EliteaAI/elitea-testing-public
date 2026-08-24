# Test Case: Remote MCP — Copy Link from Three-Dot Menu

## Metadata
- **TMS ID**: ELITEA-1959
- **Linked Story**: none
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project `399`)
- **User set**: `${TEST_USER}` (localhost: no login — `VITE_DEV_TOKEN` auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-24, batch `mcp-w02` (cluster dispatch with ELITEA-1946)
- **Status**: ready-for-automation
- **Cluster sibling**: ELITEA-1946 (`l2_mcp-detail-three-dot-menu-actions_ELITEA-1946.md`) — same live session, SEPARATE AFS. The cases differ in **steps**: 1946 inventories the menu and exercises Pin-to-top + the list reorder; this case reads the **clipboard's content** and navigates to it in a new tab. Only "click Copy link → toast" overlaps.
- **Filed during analysis**: CLARIFICATION [#1729](https://github.com/EliteaAI/elitea-testing-public/issues/1729) — the case's expected URL format omits a `/{projectId}` path segment the product does emit (see § Known Defects Found).

## Preconditions
- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed: Keycloak as `${TEST_USER}`).
- Project context set (`${ELITEA_PROJECT_ID}`, `399` during exploration).
- **Clipboard permissions granted on the browser context.** `conftest.py:303` grants `clipboard-read` + `clipboard-write` suite-wide; re-grant defensively in the test as the merged precedents do (`test_agent_copy_version_link.py:201`, `test_pipeline_three_dot_menu_actions.py:155`). Without the grant, `navigator.clipboard.readText()` raises `NotAllowedError: Read permission denied` — observed verbatim during this analysis in the un-granted Playwright-MCP context.

## Test Data

### generate-per-test (created in setup, deleted in teardown)
| Alias | Name | Url |
|---|---|---|
| MCP **A** | `autotest_mcp_copylink_{ts}` | `https://mcp.example.com/sse` |

- One disposable Remote MCP is enough — no ordering dependency in this case.
- A **generated, unique name** matters here: the copied URL carries `name={A.name}`, so a unique name makes the clipboard assertion exact rather than "some MCP".
- Name length: `MAX_NAME_LENGTH = 32`, silent truncation. `autotest_mcp_copylink_` is 22 chars → a 10-digit unix `ts` gives 32 exactly. Verify the *stored* name after creation rather than assuming the literal survived.
- Creation path: the UI create flow (`McpFormPage.navigate_to_create()` → `select_remote_mcp_type()` → `fill_name()` → `fill_url()` → `save_and_wait_for_created(project_id)`) — merged, proven in `test_mcp_delete_remote.py`.
- Teardown: `ToolkitAPI.delete_toolkit(A.id)`. (`ToolkitAPI.list_toolkits()` is a known-broken discovery path on this env — never use it to find the MCP.)

### reuse-existing
- `${TEST_USER}` (deployed envs only).

## Test Steps

1. **Setup** — create MCP **A** via the UI create flow.
   - **Verify**: `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` → `201 Created` with a numeric `id`; capture `A.id` and the persisted `A.name`.

2. **(case step 1)** Navigate to `${BASE_URL}/mcps/all` and open **A**'s detail page by clicking its card.
   - **Verify**: URL is `${BASE_URL}/mcps/all/{A.id}?viewMode=owner&name={A.name}`; `toolkit-detail-title` reads `{A.name}`.

3. **(case step 2)** Click the three-dot menu button (`controls-menu-button`).
   - **Verify**: `controls-menu` visible.

4. **(case step 3)** Clear the clipboard (real write of `''`), then click `Copy link` (`copy-link-toolkit-menuitem` — **testid needed**, see § Handles).
   - **Verify**: `toast-message` appears reading exactly **`The link has been copied to the clipboard.`**
   - **Verify**: the menu closes as a side effect (`controls-menu` → count 0) — `DotMenu.jsx`'s `withClose`.
   - Clearing first turns "wait for a non-empty clipboard" into a real condition instead of a sleep — this is `_copy_link_via_menuitem()`'s whole reason for existing.

5. **(case step 4)** Read the clipboard and assert its content.
   - **Verify**, on the copied string:
     - it starts with the app origin (`${BASE_URL}`'s scheme+host);
     - it contains the path segment sequence **`/{PROJECT_ID}/mcps/all/{A.id}`** — note the **project-id segment**, which the case text omits (CLARIFICATION #1729);
     - the query contains `viewMode=owner`;
     - the query contains `name=` with the **URL-encoded `{A.name}`**.
   - *Observed live, verbatim* (MCP `2140`, project `399`):
     `http://localhost:5173/399/mcps/all/2140?viewMode=owner&name=autotest_mcp_run_tool`
   - **Assert the live contract, not the case's Test Data row.** The stale example (`https://dev.elitea.ai/app/mcps/all/208?viewMode=owner&name=Web%20Search`) has no project-id segment; asserting it would be reverse-masking. The shape is produced by `useProjectEntityLink()` (`src/hooks/useProjectEntityLink.js:12-14`) as `origin + getBasename() + details.projectPath + (details.search || '?viewMode=' + viewMode)`, and `usePageDetails().projectPath` carries `PROJECT_ID_URL_PREFIX`. On a deployed env the same link is `https://dev.elitea.ai/app/{projectId}/mcps/all/{id}?viewMode=owner&name=…` — so build the expected value from `${BASE_URL}` + `APP_PREFIX` + `${PROJECT_ID}`, never from a hardcoded host.

6. **(case steps 5–6)** Open a **new tab** on the same authenticated context and navigate to the copied URL; verify the same MCP detail page loads.
   - `new_page = page.context.new_page()` — **not** `browser.new_page()`, which creates an unauthenticated context (the note is already in `test_agent_hub_copy_link_from_modal.py:121-123`). `new_page.goto(copied_url)` is the faithful equivalent of pasting into the address bar.
   - **Verify**: `toolkit-detail-title` on the new tab reads `{A.name}`, and `toolkit-form-name-input` holds `{A.name}`.
   - **Verify**: the new tab's final URL settles at `${BASE_URL}/mcps/all/{A.id}?viewMode=owner&name={A.name}` — i.e. **without** the `/{projectId}` prefix.
   - **The redirect hop is load-bearing, not noise**: the leading `/{projectId}` segment triggers `ProjectSwitcher`, which performs a hard `window.location.replace()` **before** the MCP page mounts. Assert on the settled state (framework auto-waiting on the title/name locator), never on the URL immediately after `goto`. Same hop already documented for ELITEA-1898.
   - *Observed live:* navigated to `…/399/mcps/all/2140?viewMode=owner&name=autotest_mcp_run_tool`; settled at `…/mcps/all/2140?viewMode=owner&name=autotest_mcp_run_tool`, document title `MCP: autotest_mcp_run_tool - project_user_659`, detail title `autotest_mcp_run_tool`, name field `autotest_mcp_run_tool` — resolved within ~300 ms of the poll starting.
   - Close the new tab afterwards (`new_page.close()`), as both merged precedents do.

7. **Teardown** — `ToolkitAPI.delete_toolkit(A.id)`.

8. **Side channel** — assert no browser console **errors** across the run (including on the new tab: attach the listener to `new_page` before `goto`, as `test_agent_copy_version_link.py:303` does).
   - *Observed live:* **0 console errors**, 0 warnings across the whole exploration.

## Expected Results
- `Copy link` copies a fully-qualified URL for the current MCP and confirms with the toast `The link has been copied to the clipboard.`
- The copied URL is `{origin}{APP_PREFIX}/{projectId}/mcps/all/{id}?viewMode=owner&name={encoded name}`.
- Opening that URL in a new tab of the same authenticated context loads the **same** MCP's detail page, after a `ProjectSwitcher` redirect that strips the `/{projectId}` prefix.
- No console errors.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | session authenticated | steps 1–2 | dev-server auto-auth; owner-mode controls render | asserted |
| Precondition: a Remote MCP detail page is open | detail page available | steps 1–2 | *decomposed*: setup creates a uniquely-named disposable MCP (the case's "a Remote MCP" is under-specified; a unique name is what makes step 5's `name=` assertion exact) | asserted |
| Test Data: Expected URL format `https://dev.elitea.ai/app/mcps/all/{id}?viewMode=owner&name={MCP name}` | clipboard matches this shape | step 5 | asserted **as the live contract**, which additionally contains `/{projectId}` | **clarification** — case text is stale, filed as [#1729](https://github.com/EliteaAI/elitea-testing-public/issues/1729); NOT a product defect (reverse-masking guard) |
| 1 Open a Remote MCP detail page | Detail page loads | step 2 | URL + `toolkit-detail-title` | asserted |
| 2 Click three-dot menu | Menu opens | step 3 | `controls-menu` visible | asserted |
| 3 Click "Copy link" | Copy action is triggered | step 4 | `toast-message` exact text + menu closes | asserted |
| 4 Verify clipboard contains the MCP URL | Clipboard contains the correct MCP URL | step 5 | origin + `/{projectId}/mcps/all/{id}` + `viewMode=owner` + encoded `name` | asserted |
| 5 Open a new browser tab and paste the URL | URL is pasted in the address bar | step 6 | `page.context.new_page()` + `goto(copied_url)` — the faithful equivalent of an address-bar paste on the same authenticated session | asserted *(the literal OS-level address-bar paste is not scriptable; the observable the case cares about is the navigation, which IS driven by the real copied string)* |
| 6 Verify the same MCP detail page loads correctly | MCP detail page loads for the correct MCP | step 6 | new tab's `toolkit-detail-title` + name field + settled URL | asserted |
| Expected Final State: copied URL navigates to the same MCP detail page | — | step 6 | same as above | asserted |
| Pass criterion: "All steps complete without errors" | no errors | step 8 | console-error assertion on both tabs | asserted |

### Axis 2 — Beyond the case (each with its grounded reason)

| Extra observable | Why |
|---|---|
| Toast text asserted exactly (`…clipboard.` with the period) | The case only names the toast in ELITEA-1946; here it is the cheap synchronous signal that the copy handler ran, and it is what makes the clipboard poll bounded. |
| The `ProjectSwitcher` redirect strips `/{projectId}` (final URL asserted) | Discovered live. Without asserting the settled URL, a test could pass against a page that never finished switching projects. It also pins the very behaviour that makes the case's "same page loads" true despite the URL shapes differing. |
| Clipboard cleared before the click | Turns the post-click wait into a real condition rather than a sleep — no-`sleep` rule. |
| Console errors on the **new tab** as well as the original | A failed project switch or a 4xx on the deep link would surface only there. |
| 0 console errors | Skill § Execute step 3 — side channels checked even when the surface looks fine. |

## Concrete Handles

| Element | Handle (testid) | Provenance (verified 2026-08-24, `git fetch origin` first) | Notes |
|---|---|---|---|
| Three-dot menu button | `controls-menu-button` | `main` ✓ · `automation/testids` ✓ | already a `McpFormPage` field |
| Menu popup | `controls-menu` | `main` ✓ · `automation/testids` ✓ | unmounts on close |
| `Copy link` menu item | **`copy-link-toolkit-menuitem` — testid needed** | needs-adding | Live testid today is **`Copy link-menuitem`**: `useCopyLinkMenu()` defaults `key: key \|\| label` (`CopyLinkToEntityButton.jsx:44`), leaking the label — *with a space* — into the testid. The hook **already accepts `key`**; the fix is one additive line at `ToolkitsControls.jsx:43` → `useCopyLinkMenu({ key: 'copy-link-toolkit' })`. `grep` over `automation/pages` + `automation/tests` found **0** references to the old string, so nothing breaks. Do not ship a test bound to `Copy link-menuitem`. |
| Toast message | `toast-message` | `main` ✓ · `automation/testids` ✓ | `src/components/Toast.jsx:74`; auto-dismisses within seconds — wait in the same chain as the click |
| Detail page title | `toolkit-detail-title` | `main` ✓ · `automation/testids` ✓ | placeholder text until data lands — poll the text |
| Toolkit Name input | `toolkit-form-name-input` | `main` ✓ · `automation/testids` ✓ | second, independent confirmation the right MCP loaded |
| List card name | `entity-card-name` | `main` ✓ · `automation/testids` ✓ | `McpListPage.open_card_by_name()` already wraps it |

**One `testid needed` row**, and it is an implementer work order (`add-data-testid` on `EliteaAI/EliteaUI` `automation/testids`), not a suggestion. ELITEA-1946 requests the same testid plus two more (`toolkit-actions-export-menuitem`, `pin-toggle-toolkit-menuitem`) — if both cases are built on one branch, add all three in a single commit.

## Automation Hints

- **Reuse `_copy_link_via_menuitem()` verbatim** from `test_pipeline_three_dot_menu_actions.py:44-65` (itself lifted from `test_agent_copy_version_link.py`): clear clipboard → click menuitem → wait for toast → `page.wait_for_function("async () => { const t = await navigator.clipboard.readText(); return t.length > 0; }")` → `page.evaluate("async () => await navigator.clipboard.readText()")`. **Do not call `readText()` directly** — a direct call hung ~30 min on an un-grantable permission prompt during ELITEA-2049's exploration, and this analysis reproduced the underlying `NotAllowedError` in an un-granted context.
- **Reuse the new-tab shape** from `test_agent_hub_copy_link_from_modal.py:121-131` — `page.context.new_page()`, `goto(copied_url, wait_until="load")`, then assert via the page object on `new_page`, and `new_page.close()` in a `finally`.
- **Build expected values from config, never literals**: `settings.app_base_url` (which injects `APP_PREFIX`: empty on localhost, `/app` on deployed) plus `settings.elitea_project_id`. A test hardcoding `dev.elitea.ai` or `399` is wrong on the other environment.
- **Page object:** add `copy_link_menuitem` to `McpFormPage` alongside the existing `delete_menuitem`, plus a `click_copy_link_menu_item()` action. The clipboard read itself stays in the test helper (that is where both merged precedents keep it).
- **Markers:** `pytest.mark.ui`, `pytest.mark.toolkits`, `pytest.mark.mcp`, `pytest.mark.p2`, `pytest.mark.regression`.
- Every step wrapped in `with allure.step("Step N — …")`.

## Fidelity Declaration

**No substitutions.** The clipboard is written by the product's own `navigator.clipboard.writeText()` inside `useCopyLink`; the test only *reads* it (`readText`) and *clears* it beforehand — reading an OS channel the product wrote is observation, not fabrication, and clearing it is test hygiene that touches no product state. The navigation in step 6 is a real `goto` of the string the product produced. No `page.route`, no `route.fulfill`, no injected app state, no replaced client.

## Blocked Steps
None.

## Known Defects Found

**None — no product defect.** One **case-text drift**, filed as a CLARIFICATION, not a bug:

- **[#1729](https://github.com/EliteaAI/elitea-testing-public/issues/1729)** — the case's § Test Data "Expected URL format" (`https://dev.elitea.ai/app/mcps/all/{id}?viewMode=owner&name={MCP name}`) and its step-4 example omit the **`/{projectId}`** path segment the product actually emits. Verified live: the copied string was `http://localhost:5173/399/mcps/all/2140?viewMode=owner&name=autotest_mcp_run_tool`. The shape is by design (`useProjectEntityLink.js:12-14` + `PROJECT_ID_URL_PREFIX`), and the case's own Pass criterion still holds — the URL does load the correct MCP. Automation asserts the live contract (reverse-masking guard: the case text is what is stale, not the product). **Not a duplicate** of #1288 / #1337 / #1218 / #1451 — those are *label* drifts ("Copy link" vs "Share"); the MCP detail menu genuinely renders a literal `Copy link` item, so no label drift exists here. Sibling, cross-linked in the issue body.

## Evidence
- Playwright MCP session, 2026-08-24, `http://localhost:5173`, MCP `2140` (`autotest_mcp_run_tool`), project `399`.
- Copied URL captured by a **real paste** (`Meta+V` into the MCP list's `agent-search-input`), since the analysis context lacked clipboard-read permission: `http://localhost:5173/399/mcps/all/2140?viewMode=owner&name=autotest_mcp_run_tool`.
- New-tab navigation to that exact URL settled at `http://localhost:5173/mcps/all/2140?viewMode=owner&name=autotest_mcp_run_tool`, title `autotest_mcp_run_tool`.
- Toast text confirmed by waiting on the literal string `The link has been copied to the clipboard.`
- Console: 0 errors, 0 warnings.
