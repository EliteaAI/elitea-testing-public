# Test Case: Remote MCP — Cancel During Creation

## Metadata
- **TMS ID**: ELITEA-1960
- **Linked Story**: none
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project `399`, 20+ MCPs present)
- **User set**: `${TEST_USER}` (localhost: no login — `VITE_DEV_TOKEN` auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-24, batch `mcp-w04` (solo dispatch)
- **Status**: ready-for-automation
- **Surface key**: `mcp-create-form`
- **Filed during analysis**:
  - CLARIFICATION [#1747](https://github.com/EliteaAI/elitea-testing-public/issues/1747) — step 7's "navigation goes back to MCP create page" is **view-level only**: the create form unmounts and the type picker re-renders, but the URL stays `/mcps/create/mcp`.
- **Reverse-masking note**: the divergence above is **case-text imprecision, not a product defect** (`test-case-analysis` § Classify findings). The case's own *expected result* ("user is navigated away from the creation form") holds exactly. This AFS asserts the LIVE contract.
- **New testids required**: **none.** All three cancel-flow handles already exist and are **on `origin/main` ✓**.

## Preconditions
- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed: Keycloak as `${TEST_USER}`).
- Project context set (`${ELITEA_PROJECT_ID}`, `399` during exploration).
- **No MCP named `autotest_cancelled` may pre-exist** — step 8's observable is absence, so a leftover from a prior run would make the assertion lie in the *other* direction. See § Test Data for why a fixed literal is nonetheless the right choice here, plus the guard.
- Nothing is created by this case, so nothing needs teardown (§ Cleanup).

## Test Data

### fixed literals (verbatim from the case's Test Data table — nothing is persisted, so uniqueness is not needed for isolation)
| Field | Value | Notes |
|---|---|---|
| Toolkit Name | `autotest_cancelled` | 18 chars, well under `MAX_NAME_LENGTH = 32` (which **silently truncates** — `_surface.md` § Fixtures addendum). No uuid suffix: the whole point of the case is that this name never reaches the server, and a generated suffix would make step 8's "does NOT appear" assertion trivially true for the wrong reason (a random string is absent from any list). |
| Url | `https://mcp.example.com/sse` | Correct fixture: the URL is only ever **stored in form state**, never dialled — Load Tools is not part of this case (`_surface.md` § Fixtures addendum). |

**Pre-flight guard (recommended, declared):** before step 1, assert via `ToolkitAPI.list_all_toolkits()` that no toolkit named `autotest_cancelled` exists. If one does, the environment is dirty from an aborted earlier run and step 8 would pass/fail for the wrong reason — fail fast with a clear message rather than produce a misleading result. This is cheap (one API call) and makes the fixed-literal choice safe.

### reuse-existing
- Whatever other MCPs the project holds — used only to prove the list actually rendered (a zero-length list would make step 8 vacuous). Never asserted by name.

## Test Steps

> Steps are numbered to match the TMS case.

| # | Action | Case's Expected Result | **OBSERVED LIVE (2026-08-24)** |
|---|---|---|---|
| 1 | `goto /mcps/create`, click the Remote MCP type card | Form page loads | URL becomes `/mcps/create/mcp`; the create form mounts (`toolkit-form-name-input`, `toolkit-field-url-input`, `toolkit-form-save-button`, `toolkit-form-cancel-button` all present). ⚠️ The type card mounts **asynchronously** after `goto` — an immediate DOM read misses `toolkit-type-card-mcp` (observed again this session; `_surface.md` § Fixtures addendum). Rely on framework auto-waiting. |
| 2 | Fill "Toolkit Name *" with `autotest_cancelled` | Field accepts and displays the input | `input_value() == "autotest_cancelled"` |
| 3 | Fill "Url *" with `https://mcp.example.com/sse` | Field accepts and displays the URL | `input_value() == "https://mcp.example.com/sse"`. Baseline captured here: `toolkit-form-cancel-button` is **enabled** (`disabled == False`) and its label is exactly `Cancel`. |
| 4 | Click "Cancel" | Cancel action is triggered | The click does **not** cancel anything by itself — it only opens the confirmation dialog (`DiscardButton`: `onClick={() => setOpenAlert(true)}`). The form is still mounted and still holds both values immediately after. |
| 5 | Verify a warning confirmation dialog appears | Confirmation dialog is displayed | `toolkit-form-cancel-confirm-dialog` present; its `text_content()` is exactly `WarningAre you sure you want to cancel creation of this toolkit?CancelDiscard` — i.e. title + message + **both** button labels concatenated (the testid lands on the MUI `Dialog` **root**, `role="presentation"`). ⇒ **assert with `in`, never `==`** (same shape as `toolkit-detail-discard-confirm-modal`, `_surface.md`). Confirm button label is exactly `Discard`. |
| 6 | Click "Discard" to confirm cancellation | Cancellation is confirmed | Dialog **unmounts** (detached, not hidden) — `to_have_count(0)`. |
| 7 | Verify navigation goes back to MCP create page | User is navigated away from the creation form | **Every create-form handle unmounts** (`toolkit-form-name-input`, `toolkit-form-description-input`, `toolkit-field-url-input`, `toolkit-form-save-button`, `toolkit-form-cancel-button` → all count 0) and the **type picker re-renders**: `mcp-type-picker-heading` text == `Choose the MCP type`, `toolkit-type-card-mcp` visible. ⚠️ **The URL does NOT change** — still `/mcps/create/mcp`. Clarification [#1747](https://github.com/EliteaAI/elitea-testing-public/issues/1747); **do not assert the URL in either direction** (§ Automation Hints). |
| 8 | Verify `autotest_cancelled` does NOT appear in MCP list | MCP is absent from the list | Navigate to `/mcps/all`, search `autotest_cancelled` + Enter → **0 cards**, `empty-state-title` renders ("No MCPs yet"). Server-side oracle: **no `POST` to `/api/v2/elitea_core/tool(s)/prompt_lib/399` fired anywhere in the flow** — the full network log for the whole session contained only GETs (`toolkits`, `project_info`, `permissions`, `internal_mcp_pat_status`). |

## Expected Final State
No MCP named `autotest_cancelled` exists — neither in the UI list nor server-side.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition — logged in, on MCP create page with Remote MCP selected | — | Step 1 (`navigate_to_create()` + `select_remote_mcp_type()`) | form handles present | covered |
| Step 1 — form page loads | Form page loads | Step 1 | `toolkit-form-name-input` + `toolkit-field-url-input` visible, URL `/mcps/create/mcp` | covered |
| Step 2 — name accepted | Field displays the input | Step 2 | `input_value() == "autotest_cancelled"` | covered |
| Step 3 — url accepted | Field displays the URL | Step 3 | `input_value() == "https://mcp.example.com/sse"` | covered |
| Step 4 — Cancel triggered | Cancel action is triggered | Step 4 | dialog appears (that IS the trigger's effect); form still mounted, values intact | covered |
| Step 5 — warning confirmation dialog | Dialog is displayed | Step 5 | dialog visible + exact message text `Are you sure you want to cancel creation of this toolkit?` via `in` | covered |
| Step 6 — click Discard | Cancellation is confirmed | Step 6 | dialog `to_have_count(0)` | covered |
| Step 7 — navigation back to MCP create page | User is navigated away from the creation form | Step 7 | 5 × create-form handle `to_have_count(0)` **and** type-picker heading text | covered (view-level; URL deliberately unasserted — [#1747](https://github.com/EliteaAI/elitea-testing-public/issues/1747)) |
| Step 8 — name absent from MCP list | MCP is absent | Step 8 | filtered list = 0 cards | covered |
| Expected Final State — nothing created | No MCP named `autotest_cancelled` | Step 8 + Axis-2 network/API assertions | see below | covered |
| Pass criterion — "All steps complete without errors" | — | Step 8b | console-error assertion, filtered per § Automation Hints | covered |

### Axis 2 — observables asserted BEYOND the case text
| Extra assertion | Grounded reason |
|---|---|
| Step 3b: `toolkit-form-cancel-button` is **enabled** on the filled form | Cancel is the control under test; proving it was actionable before the click makes step 4's dialog attributable to the click rather than to an already-open state. Cheap, no new handle. |
| Step 4b: form still mounted **and both values still present** immediately after the Cancel click, dialog open | Pins the product's two-step gesture. Without it, a regression that cancelled immediately (skipping the dialog) could still pass steps 5-8 by accident if the dialog rendered afterwards. |
| Step 8b: **no `POST` to the toolkit-create endpoint fired** during the whole flow | The case's Expected Final State is "no MCP is created". A UI-list absence alone does not prove that — a created-then-hidden entity would read the same. Implement with a `page.on("request")` collector (passive observation, **not** interception — § Fidelity Declaration). |
| Step 8c: `ToolkitAPI.list_all_toolkits()` contains no toolkit named `autotest_cancelled` | Independent, non-DOM ground truth for the same claim; also catches a create that succeeded but did not reach the list view. |
| Step 8d: the unfiltered MCP list rendered **> 0** cards before the search | Guards against the vacuous pass where the list failed to load at all and *everything* is "absent". |
| Step 8e: console errors, filtered (see § Automation Hints) | The case's Pass criterion says "All steps complete without errors" — the side channel is where a silent one would show. |

## Concrete Handles

All handles below are **on `origin/main` ✓** (verified 2026-08-24 with a fresh `git fetch origin` in `../EliteaUI`) — this case needs **no new testid** and is deployed-env promotable on the testid axis.

```
toolkit-form-cancel-button               main:YES  testids:YES
toolkit-form-cancel-confirm-dialog       main:YES  testids:YES
toolkit-form-cancel-confirm-button       main:YES  testids:YES
toolkit-form-name-input                  main:YES  testids:YES
```
(All four promoted in EliteaAI/EliteaUI@bf4a13ad, the 400-testid bulk promotion of 2026-08-11.)
`toolkit-field-url-input`, `toolkit-type-card-mcp`, `mcp-type-picker-heading`, `entity-card-name`, `agent-search-input`, `empty-state-title` are **runtime-composed or pre-existing** handles already bound by merged specs — a bare `git grep` of the literal returns nothing for the composed ones (three-level composition, `_surface.md` § Client Secret note); their provenance is the composing file, not the string.

| Element | Testid (testid-only per `.agents/testing.md`) | Provenance | Notes |
|---|---|---|---|
| Remote MCP type card | `toolkit-type-card-mcp` | pre-existing, bound by merged specs | already `McpFormPage.remote_mcp_type_card`; **mounts async after `goto`** |
| Type-picker heading | `mcp-type-picker-heading` | pre-existing, bound by merged specs | already `McpFormPage.type_picker_heading`; text `Choose the MCP type` — the step-7 positive observable |
| Toolkit Name input | `toolkit-form-name-input` | on-main ✓ | already `McpFormPage.name_input` |
| Url input | `toolkit-field-url-input` | pre-existing (generic `toolkit-field-{k}-input`) | already `McpFormPage.url_input`. **Testid sits on the `<input>` itself** — `[data-testid="toolkit-field-url-input"] input` matches nothing |
| Description input | `toolkit-form-description-input` | pre-existing | used only in the step-7 absence assertion |
| Save button | `toolkit-form-save-button` | pre-existing | used only in the step-7 absence assertion; already `McpFormPage.save_button` |
| **Cancel button (create form)** | `toolkit-form-cancel-button` | **on-main ✓** | `CreateToolkitToolTabBar.jsx` → `Button.DiscardButton dataTestId=`. **NEW to the suite** — no page object binds it yet |
| **Cancel-confirm dialog** | `toolkit-form-cancel-confirm-dialog` | **on-main ✓** | same call site, `modalDataTestId=`. Lands on the MUI `Dialog` **root** (`role="presentation"`) → `text_content()` includes title + both button labels ⇒ assert with `in`. **NEW to the suite** |
| **Cancel-confirm "Discard" button** | `toolkit-form-cancel-confirm-button` | **on-main ✓** | same call site, `confirmButtonDataTestId=`. Label `Discard`. **NEW to the suite** |
| MCP list search input | `agent-search-input` | on-main ✓ | already `McpListPage.search_input` (shared `SearchBar`) |
| MCP card name | `entity-card-name` | on-main ✓ | already `McpListPage.mcp_card_name` |
| Zero-result empty state | `empty-state-title` | pre-existing | optional secondary signal for step 8; the count assertion is the primary |

### Page-object work

- **`McpFormPage`** — add three class-level `LocatorDescriptor` fields: `create_cancel_button`, `cancel_confirm_dialog`, `cancel_confirm_button`.
- Add two methods mirroring the already-merged detail-page pair (`click_discard()` / `confirm_discard()`, `mcp_form_page.py:1429-1459`) — same two-step shape, different testids:
  - `click_cancel_creation()` — click `create_cancel_button`, `wait_for(state="visible")` on `cancel_confirm_dialog`.
  - `confirm_cancel_creation()` — click `cancel_confirm_button`, `wait_for(state="detached")` on `cancel_confirm_dialog`.
  - plus `get_cancel_confirm_message()` returning `cancel_confirm_dialog.text_content()`, docstring noting the root-node concatenation.
- **Naming, declared:** the existing detail-page fields are `detail_discard_button` / `discard_confirm_modal` / `discard_confirm_button`. The create-form pair is named `create_cancel_*` / `cancel_confirm_*` to keep the two flows unambiguous in a single class — the product itself names them differently (`Cancel` vs `Discard` trigger, identical `Discard` confirm). Declared per `.agents/role-overrides.md` § declared-improvisation protocol; if the implementer prefers a different prefix, declare the choice in the Run Report.
- **`McpListPage`** needs **nothing new** — `navigate()`, `search()`, `get_card_count()`, `get_card_names()` all exist and were exercised live.

## Automation Hints

- **`McpFormPage.select_remote_mcp_type()` after `navigate_to_create()`** is the proven entry path (`test_mcp_back_navigation.py:98-99`). The type card mounts asynchronously — never a bare immediate `query_selector`.
- **The Url testid is ON the input.** `url_input.fill(...)` works; `[data-testid="toolkit-field-url-input"] input` matches nothing (cost one probe live this session).
- **`McpListPage.search()` needs ≥3 chars and commits on Enter** — typing alone does not filter (`SearchBar.jsx`; `.agents/role-overrides.md` § interaction-discovery ladder, #44). The existing method already presses Enter and waits ~1.5 s for the React re-render.
- **Do NOT `clear_search()` after step 8.** Clicking Clear while the zero-match empty state is showing navigates away to `/mcps/create` — known defect [#1734](https://github.com/EliteaAI/elitea-testing-public/issues/1734) (regression of #585). The test has no reason to clear; just end there.
- **Do NOT assert the URL in step 7** (either value) — see [#1747](https://github.com/EliteaAI/elitea-testing-public/issues/1747). Assert unmount + type-picker heading instead. `to_have_count(0)` (not `not_to_be_visible()`): the create-form nodes are **removed**, not hidden.
- **Console assertion must filter two known, unrelated signatures** — this flow renders the MCP type picker **twice** (entry, and again after the cancel), and the picker deterministically emits a React dev-mode error on every mount:
  - `Each child in a list should have a unique "key" prop` — `CategorySection.jsx:35` via `ToolkitTypeSelector.jsx:36`, tracked as [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656). **Unavoidable here** — unlike ELITEA-1961, this case cannot register the listener after leaving the picker, because returning to it *is* step 7's observable.
  - `socket.io` polling failures to `dev.elitea.ai` (CORS / 502 / 503) — the standing localhost-vs-DEV-backend environment characteristic, not this flow.

  So: collect console errors, **exclude those two signatures by message match with a `# Known defect: #656` comment**, and assert the remainder is empty. That keeps a genuinely new error red without a guaranteed sanctioned-RED. Do **not** drop the assertion entirely (the case's Pass criterion names it) and do **not** assert unfiltered (deterministic RED for an already-tracked, unrelated defect — masking in the other direction).
- **No teardown.** If the pre-flight guard or a failure leaves a real `autotest_cancelled` behind, that is itself the bug this case exists to catch — do not silently delete it in a `finally` block. (A cleanup that deletes it would erase the evidence of the failure.)
- Whole flow runs in a few seconds — no long waits, no WebSocket dependency, no Load Tools.

## Fidelity Declaration

**No substitutions of any kind.** Every observable is produced by the system:
- Both fields are filled through the real inputs; Cancel and Discard are real clicks on the product's own controls.
- The dialog, the unmount, the type-picker re-render and the empty search result are all rendered by the product.
- The "no POST fired" assertion uses a **passive** `page.on("request")` observer — observation, not interception. No `page.route`, no `route.fulfill`, no `page.evaluate`-injected state, no API-seeded precondition standing in for a UI step.
- `ToolkitAPI.list_all_toolkits()` is used only as an **independent read-only oracle** for absence, never to create or shortcut a step.

*Analyst-side note on exploration technique:* live observation used `browser_evaluate` **read-only** DOM probes (presence/value/text reads). No state was injected and no assertion in this AFS derives from an evaluated write.

## Blocked Steps

None. Every case step was executed live, end to end.

## Known Defects Found

No product defect. One clarification:

### CLARIFICATION [#1747](https://github.com/EliteaAI/elitea-testing-public/issues/1747) — cancel returns to the type picker without a URL change

`CreateToolkitToolTabBar.jsx`'s `onCancel` sets `wantToCancel`; its effect calls `onClearEditTool()` + `formik.resetForm()`. At the MCP call site (`CreateToolkit.jsx:141`) `onClearEditTool` is `() => setEditToolDetail(null)` — pure component state. **No `navigate()` exists anywhere in the cancel path**, so the URL cannot change by construction. The case's *expected result* still holds (the user IS away from the creation form); only its step *title* implies a route change. Filed for a human to rule on whether the residual URL/view desync is intended.

Two adjacent observations, recorded but **not** filed:
- The type picker's React "unique key prop" console error is already tracked as [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656) — not re-filed, handled by the console filter above.
- `CreateToolkitToolTabBar.jsx` passes `dataTestId` / `modalDataTestId` / `confirmButtonDataTestId` — prop names the project's own convention would write as `testId` / `<part>TestId` (`.agents/testing.md` § Locator policy). This is **pre-existing product code already on `main`**, not our diff, and the resulting `data-testid` values are correct — noted only so a future `add-data-testid` pass at this call site does not copy the prefix.

## Cleanup

**Nothing to clean up** — the case creates nothing. Explicitly: no `ToolkitAPI.delete_toolkit()` in a `finally` block (see § Automation Hints for why deleting a leaked `autotest_cancelled` would destroy the failure evidence).

## Evidence

Live exploration, 2026-08-24, `http://localhost:5173`, project 399. Observations from scripted read-only DOM probes plus one screenshot for the dialog (the only step whose observable benefits from a visual record).

| Observation | Value |
|---|---|
| After type-card click | URL `/mcps/create/mcp`; form handles present; `toolkit-form-cancel-button` label `Cancel`, `disabled == False` |
| After filling both fields | name `autotest_cancelled`, url `https://mcp.example.com/sse`, `toolkit-form-save-button.disabled == False` |
| After Cancel click | URL unchanged; dialog present, `role="presentation"`; text `WarningAre you sure you want to cancel creation of this toolkit?CancelDiscard`; confirm label `Discard`; **form still mounted** |
| After Discard click | dialog absent; `toolkit-form-name-input` / `-description-input` / `toolkit-field-url-input` / `toolkit-form-save-button` / `toolkit-form-cancel-button` **all absent**; `mcp-type-picker-heading` == `Choose the MCP type`; `toolkit-type-card-mcp` present; **URL still `/mcps/create/mcp`** |
| Network (whole flow, filtered `tool|toolkit|prompt_lib`) | 9 requests, **all GET**, zero POST/PUT |
| `/mcps/all` unfiltered | 20 cards rendered, `autotest_cancelled` absent from names and from `document.body.innerText` |
| `/mcps/all` + search `autotest_cancelled` | **0 cards**, `empty-state-title` rendered |
| Console (session-wide) | only vite-HMR reload failures (dev-server restart), `socket.io` CORS/502/503 to `dev.elitea.ai`, and the #656 type-picker key warning — **none emitted by the Cancel/Discard clicks themselves** |

Screenshot: `test-results/screenshots/ELITEA-1960-step-05-cancel-confirm-dialog.png` (step 5, confirmation dialog).
