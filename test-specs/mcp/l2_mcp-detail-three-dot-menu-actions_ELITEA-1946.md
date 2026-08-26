# Test Case: MCP Detail — Three-Dot Menu Actions

## Metadata
- **TMS ID**: ELITEA-1946
- **Linked Story**: none
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project `399`)
- **User set**: `${TEST_USER}` (localhost: no login — `VITE_DEV_TOKEN` auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-24, batch `mcp-w02` (cluster dispatch with ELITEA-1959)
- **Status**: ready-for-automation
- **Cluster sibling**: ELITEA-1959 (`l2_remote-mcp-copy-link-from-three-dot-menu_ELITEA-1959.md`) — analysed in the SAME live session but emitted as a SEPARATE AFS: the two cases differ in **steps**, not just data (this case asserts the menu inventory + Pin-to-top + list reorder; ELITEA-1959 asserts the clipboard URL's *content* and a new-tab navigation to it). Only the "click Copy link → toast" fragment overlaps — share the page-object method, not the spec.

## Preconditions
- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed: Keycloak login as `${TEST_USER}`).
- Project context set (`${ELITEA_PROJECT_ID}`, `399` during exploration).
- **Clipboard permissions granted on the browser context** — `conftest.py:303` already does this suite-wide (`permissions=["clipboard-read", "clipboard-write"]`); no per-test grant is required, but the merged precedents re-grant defensively (`test_pipeline_three_dot_menu_actions.py:155`). Keep that habit.
- **No other MCP in the project is pinned.** Verified live 2026-08-24: all 19 MCPs in project 399 read `aria-label="Pin to top"` (i.e. none pinned) before this run, and the run left them that way (it unpinned in cleanup). Step 8's "at index 0" assertion depends on this; see § Automation Hints for the defensive check.

## Test Data

### generate-per-test (created in setup, deleted in teardown)
Two disposable Remote MCPs are needed, **created in this order**, because the list's default sort is newest-first — pinning an MCP that is *already* at the top proves nothing:

| Alias | Name | Url | Role |
|---|---|---|---|
| MCP **A** | `autotest_mcp_menu_a_{ts}` | `https://mcp.example.com/sse` | the subject: menu is opened on ITS detail page, and IT gets pinned |
| MCP **B** | `autotest_mcp_menu_b_{ts}` | `https://mcp.example.com/sse` | created **after** A so it sorts above A; gives step 8 a real position to move past |

- `https://mcp.example.com/sse` is never dialled (Load Tools is not clicked in this case) — digest § Fixtures (addendum) already sanctions it for store-only cases.
- Name length: `MAX_NAME_LENGTH = 32`, silently truncating — `autotest_mcp_menu_a_` is 20 chars, so a 10-digit unix `ts` suffix fits exactly (30). Use `int(time.time())`, not a uuid4 hex.
- Creation path: the **UI create flow** (`McpFormPage.navigate_to_create()` → `select_remote_mcp_type()` → `fill_name()` → `fill_url()` → `save_and_wait_for_created(project_id)`), the merged, proven path from `test_mcp_delete_remote.py`. *Unverified optimization:* `ToolkitAPI.create_toolkit(name, description, toolkit_type="mcp", settings={...})` exists but its Remote-MCP `settings` shape was NOT verified during this analysis — do not adopt it without a live check.
- Teardown: `ToolkitAPI.delete_toolkit(id)` for both (confirmed-reliable path; note `ToolkitAPI.list_toolkits()` is a known-broken discovery path on this env — never use it to find them). Unpin A **before** deleting it (see § Automation Hints).

### reuse-existing
- `${TEST_USER}` (deployed envs only).

## Test Steps

1. **Setup** — create MCP **A**, then MCP **B**, via the UI create flow.
   - **Verify**: each `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` returns `201 Created` with a numeric `id`.

2. **(case step 1)** Navigate to `${BASE_URL}/mcps/all` and open **MCP A**'s detail page by clicking its card.
   - **Verify**: URL becomes `${BASE_URL}/mcps/all/{A.id}?viewMode=owner&name={A.name}`; `toolkit-detail-title` reads `{A.name}`; `toolkit-form-name-input` holds `{A.name}`.
   - *Observed live:* `http://localhost:5173/mcps/all/2140?viewMode=owner&name=autotest_mcp_run_tool`, title `autotest_mcp_run_tool`.

3. **(case step 2)** Click the three-dot menu button (`controls-menu-button`, top-right next to Save/Discard).
   - **Verify**: `controls-menu` becomes visible.

4. **(case step 3)** Verify the menu's five items and their states.
   - **Verify**, in this DOM order:

     | # | Label | Handle | State |
     |---|---|---|---|
     | 1 | `Export` | `toolkit-actions-export-menuitem` (added during implementation) | `aria-disabled="true"` |
     | 2 | `Fork` | `toolkit-actions-fork-menuitem` | `aria-disabled="true"` |
     | 3 | `Copy link` | `copy-link-toolkit-menuitem` (added during implementation) | enabled (`aria-disabled` absent) |
     | 4 | `Pin to top` | `pin-toggle-toolkit-menuitem` (added during implementation) | enabled |
     | 5 | `Delete` | `toolkit-actions-delete-menuitem` | enabled |

   - *Observed live, verbatim:* `[{Export, testid: null, aria-disabled: "true"}, {Fork, toolkit-actions-fork-menuitem, "true"}, {Copy link, "Copy link-menuitem", null}, {Pin to top, testid: null, null}, {Delete, toolkit-actions-delete-menuitem, null}]`.
   - Assert **disabled-ness via `aria-disabled`**, not via `is_enabled()`: MUI renders disabled `MenuItem`s as `<li aria-disabled="true" class="… Mui-disabled">`, which Playwright's `is_enabled()` does not read as disabled on a non-form element. Merged precedent: `test_pipeline_three_dot_menu_actions.py:122`.

5. **(case step 4)** Click `Copy link`.
   - **Verify**: the toast (`toast-message`) appears with the exact text **`The link has been copied to the clipboard.`** (note the trailing period — the case text omits it; assert with the period, or a `"copied to the clipboard" in text.lower()` substring as the pipeline precedent does).
   - **Verify**: the menu closes as a side effect of the item click (`controls-menu` count → 0) — `DotMenu.jsx`'s `withClose` fires on every item click. Confirmed live.
     - **Amended during implementation (2026-08-24):** the unmount runs behind MUI's close TRANSITION, so a `count()` read fired in the click's own tick still sees `1` (observed: the first run failed exactly here). Wait on the condition first — `McpFormPage.wait_for_controls_menu_closed()` (`controls_menu.wait_for(state="detached")`) — then assert `count() == 0`. Framework wait, not a sleep. The analyst's live read was correct but taken a turn later.
   - **Timing, load-bearing**: the toast auto-dismisses within a few seconds. Wait for it *in the same synchronous chain* as the click (`toast_message.wait_for(state="visible")`), exactly like `McpFormPage.wait_for_sync_error_toast()`. A DOM read a couple of turns later finds nothing — it did during this analysis, twice.
   - Clipboard *content* is NOT asserted here — that is ELITEA-1959's subject.

6. **(case step 5)** Re-open the menu (`controls-menu-button`) and press `Escape`.
   - **Verify**: `controls-menu` is **removed from the DOM** → `to_have_count(0)` (not `not_to_be_visible()`). Confirmed live: `{menuPresent: false, menuVisible: false}`.
   - **Re-opening first is mandatory, not cosmetic**: step 5's click already closed the menu, so pressing Escape against an already-closed menu would pass even if Escape-to-close regressed. Same fix ELITEA-2049 took in review round 1.

7. **(case step 6)** Re-open the menu and click `Pin to top`.
   - **Verify**: `POST /api/v2/social/pin/prompt_lib/${PROJECT_ID}/toolkit/{A.id}` returns **`201 Created`**. Observed live verbatim.
   - **Verify**: re-opening the menu now shows the item labelled **`Unpin from top`** (the same `pin-toggle-toolkit-menuitem` element; label comes from `usePinMenu`'s `isPinned ? 'Unpin from top' : 'Pin to top'`). Confirmed live.

8. **(case step 7)** Navigate to `${BASE_URL}/mcps/all` and verify MCP A is at the top of the list.
   - **Verify**: `entity-card-name` collection index of `{A.name}` is **0**, and is **lower than** the index of `{B.name}` (which was above A before the pin).
   - **Verify**: A's list-row pin button `mcp-pin-toggle-button-{A.id}` now carries `aria-label="Unpin from top"`.
   - *Observed live:* top-4 after pinning = `[{autotest_mcp_run_tool, "Unpin from top"}, {autotest_conn_tools_a1, "Pin to top"}, {autotest_mcp_test_mcp_node_fresh, …}, {test, …}]` — the pinned MCP jumped from index 3 to index 0, no reload needed beyond the navigation.

9. **Teardown** — re-open A's detail page, open the menu, click `Unpin from top`, then delete **A** and **B** via `ToolkitAPI.delete_toolkit()`.
   - **Verify** (cheap, worth asserting): the unpin fires `DELETE /api/v2/social/pin/prompt_lib/${PROJECT_ID}/toolkit/{A.id}` → **`204 No Content`**. Observed live.

10. **Side channel** — assert no browser console **errors** across the case's own flow (steps 2-9).
    - **Amended during implementation (2026-08-24):** the console listener is registered AFTER setup, not at test start. The `/mcps/create` type-picker used to seed the disposable MCPs emits a React dev-mode `Each child in a list should have a unique "key" prop` warning from `CategorySection.jsx` on every mount — **already tracked as [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656)** ("[MINOR][ELITEA-1868] Toolkit type-picker: React 'unique key prop' console warning in CategorySection list"), and on a page this CASE never visits (the case starts at "Open any Remote MCP detail page"). Scoping the listener to the case's own flow keeps the side channel about the surface under test rather than about our scaffolding; the known defect stays filed and unmasked. Not filed again — occurrence commented on #656.
    - *Observed live:* **0 console errors**, 0 warnings across the full ELITEA-1946 + ELITEA-1959 exploration (8 console messages total, all `info`/`debug`).

## Expected Results
- The MCP detail three-dot menu opens showing exactly five items — `Export` (disabled), `Fork` (disabled), `Copy link`, `Pin to top`, `Delete` — matching the case text verbatim. **No case-text drift on this case.**
- `Copy link` copies the link and surfaces the toast `The link has been copied to the clipboard.`, closing the menu.
- `Escape` closes the menu (element unmounts).
- `Pin to top` pins the MCP (`POST …/social/pin/… → 201`), flips its own menu label to `Unpin from top`, and moves the MCP to index 0 of `/mcps/all`.
- No console errors.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | session is authenticated | step 1–2 | dev-server auto-auth; detail page renders owner-mode controls | asserted |
| Precondition: a Remote MCP detail page is open | detail page available | steps 1–2 | *decomposed*: setup creates two disposable MCPs (the case's "any" is under-specified and would make step 7 non-deterministic), then opens A via a real list-card click | asserted |
| 1 Open any Remote MCP detail page | Detail page loads | step 2 | URL + `toolkit-detail-title` + `toolkit-form-name-input` | asserted |
| 2 Click the three-dot menu button | Menu opens | step 3 | `controls-menu` visible | asserted |
| 3 Menu shows Export (disabled), Fork (disabled), Copy link, Pin to top, Delete | All items visible with correct states | step 4 | per-item testid + `aria-disabled` table | asserted |
| 4 Click "Copy link" → toast "The link has been copied to the clipboard" | Copy confirmation toast is shown | step 5 | `toast-message` exact text (product adds a trailing `.`) | asserted |
| 5 Close menu (click outside or press Escape) | Menu closes | step 6 | `controls-menu` `to_have_count(0)` after Escape, on a **re-opened** menu | asserted *(the case's "click outside" alternative is not exercised — Escape is the deterministic half; noted, not dropped)* |
| 6 Reopen menu and click "Pin to top" — MCP gets pinned | MCP is pinned | step 7 | `POST …/social/pin/… → 201` + menu label flips to `Unpin from top` | asserted |
| 7 Navigate to list — MCP appears at top | MCP is at the top of the list | step 8 | `entity-card-name` index 0 + index(A) < index(B) + row `aria-label="Unpin from top"` | asserted |
| Expected Final State: MCP pinned and at top | — | step 8 | same as above | asserted *(teardown then unpins + deletes — a shared-project hygiene requirement, not a case-text conflict)* |
| Pass criterion: "All steps complete without errors" | no errors | step 10 | console-error assertion | asserted |

### Axis 2 — Beyond the case (each with its grounded reason)

| Extra observable | Why |
|---|---|
| `POST/DELETE /social/pin/prompt_lib/{project}/toolkit/{id}` status codes (201 / 204) | The case's "MCP is pinned" is otherwise only observable as list order, which is also affected by sort/pagination. The API status is the system's own, independent confirmation — same pattern as the merged `test_pipeline_dashboard_pin_to_top.py` and `test_credential_pin_unpin.py`. |
| Menu closes on the `Copy link` click itself | Discovered live; it is the reason step 6 must re-open the menu before Escape. Asserting it pins the behaviour that makes step 6 meaningful. |
| Menu item label flips to `Unpin from top` | Gives step 7 an assertion that does not depend on navigating away, and guards the `usePinMenu` label contract. |
| `index(A) < index(B)` in addition to `index(A) == 0` | `index == 0` is the case's literal expectation but is fragile to a stray pinned MCP left by another run; the relative assertion is the robust half. Both are asserted, not one instead of the other. |
| 0 console errors | Skill § Execute step 3 — side channels are checked even when the surface looks fine. |

## Concrete Handles

| Element | Handle (testid) | Provenance (verified 2026-08-24, `git fetch origin` first) | Notes |
|---|---|---|---|
| Three-dot menu button (detail page) | `controls-menu-button` | `main` ✓ · `automation/testids` ✓ | shared `ControlsDropdown`; already a `McpFormPage` field |
| Menu popup | `controls-menu` | `main` ✓ · `automation/testids` ✓ | already a `McpFormPage` field; **unmounts** when closed |
| `Fork` menu item | `toolkit-actions-fork-menuitem` | `main` ✓ · `automation/testids` ✓ | composed at runtime — `ForkEntityButton.jsx:26` sets key `toolkit-actions-fork`, `DotMenu.jsx:58` appends `-menuitem`. Grep the **key**, not the full string. |
| `Delete` menu item | `toolkit-actions-delete-menuitem` | `main` ✓ · `automation/testids` ✓ | same composition (`DeleteToolkitButton.jsx:72`); already a `McpFormPage` field |
| `Export` menu item | `toolkit-actions-export-menuitem` | **ADDED during implementation** — EliteaAI/EliteaUI@2c4107b4 on `automation/testids` (not yet on `main`) | `useExportToolkitMenu()` (`src/pages/Toolkits/ExportToolkitButton.jsx:38-40`) builds its menuItem with **no `key` at all**, so `DotMenu.jsx:422`'s `testId: item.key` is `undefined` and no `data-testid` renders. Fix: add an **optional** `key` param (same shape `usePinMenu` already uses) and pass `key: 'toolkit-actions-export'` from `ToolkitsControls.jsx:51`. Additive, zero functional impact. |
| `Copy link` menu item | `copy-link-toolkit-menuitem` | **ADDED during implementation** — EliteaAI/EliteaUI@2c4107b4 on `automation/testids` (not yet on `main`) | Live testid today is **`Copy link-menuitem`** — `useCopyLinkMenu()` defaults `key: key \|\| label` (`CopyLinkToEntityButton.jsx:44`), so the label leaks into the testid *with a space*. That violates `{section}-{element}-{type}` and is not a name any coverage tool should index. `useCopyLinkMenu` **already accepts `key`** — the fix is one line at `ToolkitsControls.jsx:43`: `useCopyLinkMenu({ key: 'copy-link-toolkit' })`. Verified no automation code references the old `Copy link-menuitem` string (`grep` over `automation/pages` + `automation/tests` — 0 hits), so the rename breaks nothing. |
| `Pin to top` / `Unpin from top` menu item | `pin-toggle-toolkit-menuitem` | **ADDED during implementation** — EliteaAI/EliteaUI@2c4107b4 on `automation/testids` (not yet on `main`) | `usePinMenu()` already supports an optional `key` (added for ELITEA-2049); `ToolkitsControls.jsx:45-49` is the one caller that doesn't pass one. Pass `key: 'pin-toggle-toolkit'`, mirroring the credentials surface's existing `pin-toggle-credential-menuitem`. **The testid is a STABLE IDENTITY; the pinned/unpinned state is read from the item's TEXT**, never from a second state-flavoured testid (`.agents/testing.md` § Locator policy). |
| Toast message | `toast-message` | `main` ✓ · `automation/testids` ✓ | `src/components/Toast.jsx:74`; already `McpFormPage.sync_error_toast_message` — reuse or add a neutrally-named alias field |
| Detail page title | `toolkit-detail-title` | `main` ✓ · `automation/testids` ✓ | shows an "Edit Toolkit" placeholder until data lands — poll the text |
| Toolkit Name input | `toolkit-form-name-input` | `main` ✓ · `automation/testids` ✓ | |
| List card | `entity-card` | `main` ✓ · `automation/testids` ✓ | |
| List card name | `entity-card-name` | `main` ✓ · `automation/testids` ✓ | `McpListPage.get_card_names()` already wraps it |
| List-row pin toggle (dynamic) | `mcp-pin-toggle-button-{id}` | `main` ✓ · `automation/testids` ✓ | `PinButton.jsx:98` — `${getPinTestIdSlug(entityType)}-pin-toggle-button-${entityId}`. Dynamic testid ⇒ UPPER_CASE class-constant template per `.agents/testing.md`, e.g. `MCP_PIN_TOGGLE_BUTTON = '[data-testid="mcp-pin-toggle-button-{}"]'`. State is read from its `aria-label` (`Pin to top` / `Unpin from top`). |

**No non-testid handle is required by this case.** The three `testid needed` rows were implementer work orders and are **DONE** — all three landed in EliteaAI/EliteaUI@2c4107b4 on `automation/testids` (one additive commit naming each menu item's `key` at the `ToolkitsControls.jsx` call site; the shared hooks are untouched, so no other caller changes). Still awaiting a human cherry-pick to `main`.

## Automation Hints

- **Page object:** extend `McpFormPage` (it already owns `controls_menu_button`, `controls_menu`, `delete_menuitem`, `open_controls_menu()`, `get_controls_menu_text()`). Add `export_menuitem`, `copy_link_menuitem`, `pin_toggle_menuitem` fields plus `get_pin_toggle_menu_label()` / `click_pin_toggle_menu_item()` — **mirror `CredentialDetailPage:272-293` verbatim**, including its `expect_response("/social/pin/prompt_lib/")` wrapper; the two surfaces share the widget.
- **Clipboard:** not read in this case. If a future extension does, copy `_copy_link_via_menuitem()` from `test_pipeline_three_dot_menu_actions.py:44-65` — a direct `navigator.clipboard.readText()` call hung ~30 min on an un-grantable permission prompt during ELITEA-2049's exploration; the `page.wait_for_function` polling form is the sanctioned shape.
- **Pin timing is asymmetric** (documented on both merged pin tests, and consistent with what this analysis saw): pinning re-sorts the grid immediately, **unpinning does not** — the just-unpinned entity stays at the top until a fresh navigate/re-fetch, even though its label flips back instantly. This case never asserts post-unpin order (unpin is teardown only), so it is not exposed — do not add such an assertion without a re-navigation.
- **Defensive pre-check for the "no other MCP is pinned" precondition:** before step 8's `index == 0` assertion, the setup may read `/mcps/all` once and assert that no `mcp-pin-toggle-button-*` carries `aria-label="Unpin from top"`. If one does, that is a leftover from an aborted run — unpin it (or fall back to asserting only `index(A) < index(B)` and record the deviation in the Run Report). Do **not** weaken the assertion silently.
- **Do not reuse `test_mcp_delete_remote.py`'s history caveat here.** That step-ordering constraint exists only because `DeleteToolkitButton`'s confirm handler calls `navigate(-1)`. Copy link and Pin to top have no such dependency — confirmed live by driving both from a directly-navigated detail page.
- **Markers:** `pytest.mark.ui`, `pytest.mark.toolkits`, `pytest.mark.mcp`, `pytest.mark.p2`, `pytest.mark.regression`.
- Every step wrapped in `with allure.step("Step N — …")`.

## Fidelity Declaration

**No substitutions.** Every asserted value is produced by the system: the menu items and their `aria-disabled` state are read from the live DOM, the toast text from the live toast, the pin/unpin outcomes from the real `POST`/`DELETE` responses and the real re-sorted list. No `page.route`, no `route.fulfill`, no injected state. The only `page.evaluate` in the *analysis* was read-only DOM/network inspection; the implemented test needs none.

## Blocked Steps
None.

## Known Defects Found
None. The product matched the case text on every step of this case, including the exact five-item menu inventory and both disabled states.

*(Related, and belonging to the sibling case, not this one: the copied-URL shape drift filed as CLARIFICATION [#1729](https://github.com/EliteaAI/elitea-testing-public/issues/1729) — see `l2_remote-mcp-copy-link-from-three-dot-menu_ELITEA-1959.md`.)*

## Evidence
- Playwright MCP session, 2026-08-24, `http://localhost:5173`, MCP `2140` (`autotest_mcp_run_tool`), project `399`.
- Menu inventory (before pin) and after pin — both captured verbatim in § Test Steps 4 and 7.
- Network: `POST /api/v2/social/pin/prompt_lib/399/toolkit/2140 → 201 Created`; `DELETE …/toolkit/2140 → 204 No Content`.
- Console: 0 errors, 0 warnings.
