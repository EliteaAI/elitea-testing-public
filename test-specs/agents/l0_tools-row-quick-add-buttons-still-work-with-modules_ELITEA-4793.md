# Test Case: + Toolkit / + MCP / + Agent / + Pipeline still work next to + Modules; module states unaffected by adding a tool

- **TMS:** ELITEA-4793 (`agents/modules/ELITEA-4793_*.md`, requirement elitea_issues#7380)
- **Status:** ready-for-automation
- **Surface:** `agent-tools-row` (Agent detail, TOOLS row) - see `test-specs/agents/_surface.md`
- **Executed:** 2026-11-23 on DEV (`https://dev.elitea.ai/app`), scripted headless Playwright through repo page objects + `agent_id` / `artifact_toolkit` fixtures (MCP chrome binary absent on host). Every step run live, clean pass, no product defect. NOTE: `APP_PREFIX=/app` was not in the shell env and `.env.test` was absent in this sandbox; I exported `APP_PREFIX=/app` (without it navigation 404s). Not a repo defect.
- **Spec home (suggested):** `automation/tests/ui/agents/test_agent_modules_tools_row.py`; fixtures `agent_id`, `artifact_toolkit` (any existing toolkit; this one is API-created and deleted at teardown).
- **Neighbours checked:** ELITEA-4789 spec (dropdown list/scroll, asserts all five buttons exist, not that they open flows), ELITEA-4790/4791/4792 (module persistence/attachments/save-as-version); `add_toolkit`/`remove_toolkit` page-object methods and `open_agent_picker` (ELITEA-1887). None asserts open/dismiss of the four flows or module-state invariance after a tool add -> NOT coverage.

## Steps (as executed)
Dismiss platform banner first (`dismiss_platform_release_banner_if_present`), `ensure_toolkits_section_visible()`.
1-4. For each of `add_toolkit_button`, `add_mcp_button`, `add_agent_button`, `add_pipeline_button`: click -> a MUI popper (not a dialog) opens, containing `toolkit-search-input`; contents: Toolkit = "Create new" (+ "No toolkits available" on an empty project, otherwise the list), MCP = Create new + MCP list, Agent = project agents, Pipeline = project pipelines. Dismiss: **Escape does NOT close the popper** (still open after Escape, all four); a click outside (`page.mouse.click(5, 5)`) closes it (`toolkit-search-input` count 0).
5. `open_modules_menu()`, record `{key: module_is_on(key)}` (`module_menu_item_keys()`), then click `add_toolkit_button` with the Modules menu open: `agent-modules-menu` becomes hidden AND the toolkit popper opens (click works without `force`; `force=True` is what `add_toolkit` uses and is fine).
6. Select the toolkit in the popper (`add_toolkit(name)`): `agent-toolkit-card` containing the name appears in TOOLS. **Save button stays disabled** (`agent-save-button` and `discard-button` both disabled right after attach): attaching a toolkit persists immediately (PATCH on the tool relation); reload shows the card still present (count 1). See clarification 1.
7. `open_modules_menu()`, read states: dict == step-5 dict (True after attach and after reload).
8. `remove_toolkit(name)` (hover card, delete icon, confirm): card gone; Save still disabled (remove also auto-persists); after reload card count 0.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| + Toolkit / + MCP / + Agent / + Pipeline | 1 | `agent-add-toolkit-button`, `agent-add-mcp-button`, `agent-add-agent-button`, `agent-add-pipeline-button` (page-object fields of same names) | - | testid on DEV (verified) |
| + Modules | 1 | `agent-add-modules-button` (`open_modules_menu`) | - | testid on DEV (verified) |
| Modules menu | 1 | `agent-modules-menu` (`modules_menu`) | - | testid on DEV (verified) |
| Module row switch | 1 | `agent-canvas-tools-toggle-{key}` (`module_is_on`) | - | testid on DEV (verified) |
| Picker popper content | 1 | `toolkit-search-input` (shared by all four pickers), `toolkit-menu-item` rows; popper itself via `components.mui.Popper.wait_for` | - | testid on DEV (verified) |
| Toolkit card | 1 | `agent-toolkit-card` (`toolkit_card`) filtered by name | - | testid on DEV (verified) |
| Save / Discard | 1 | `agent-save-button` / `discard-button` | - | testid on DEV (verified) |

Implementer needs ONE small addition: a "popper is closed" check and a click-outside dismiss. Escape does not work, so dismiss with `page.mouse.click(5, 5)` inside a page-object method (coordinates, not a locator) and assert `toolkit-search-input` count == 0 (declare `toolkit-search-input` at class level if not already; a `[data-testid="toolkit-search-input"]` constant is rung 1). "Dialog opens" in the case = popper visible with `toolkit-search-input`; for MCP/Agent/Pipeline assert the popper lists ≥1 `toolkit-menu-item` or the Create new entry (project data dependent - assert visibility of search input, not list contents).

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | Toolkit dialog opens/closes | step 1 | popper + `toolkit-search-input` visible; after click-outside count 0 | asserted |
| Step 2 | MCP dialog opens/closes | step 2 | same | asserted |
| Step 3 | Agent dialog opens/closes | step 3 | same | asserted |
| Step 4 | Pipeline dialog opens/closes | step 4 | same | asserted |
| Step 5 | Modules menu closes, Toolkit dialog opens | step 5 | `modules_menu` hidden; `toolkit-search-input` visible; states recorded | asserted |
| Step 6 | toolkit card in TOOLS; agent saved | step 6 | card visible; reload -> card still present (persistence proves saved); "click Save" not performed, button disabled (clarification 1) | asserted (adapted) |
| Step 7 | module states == step 5 | step 7 | dict equality | asserted |
| Step 8 | cleanup: card removed | step 8 | card count 0 (+ after reload) | asserted |
| Expected Final State | module states unaffected | step 7 | covered | asserted |
| Axis 2 | persistence after reload of add/remove | steps 6, 8 | grounds "agent is saved" | added (defends clarification 1) |

## Known Defects
None.

## Clarifications (case-text drift, not defects)
1. Case says "click Save" after adding the toolkit; live, adding/removing a tool persists immediately and Save/Discard stay disabled (never enabled by a tool change). Assert the real contract (persisted after reload) and do NOT click a disabled Save. File as case-text clarification; do not mask.
2. "Dialog" is a MUI popper, and "dismiss" = click outside (Escape does not close it). Possible UX note (not filed): Escape not closing the pickers.
3. "Any existing toolkit": the project has toolkits, but use the `artifact_toolkit` fixture for determinism (it needs a bucket; fixture handles it; teardown logs a harmless bucket-delete 404).

## Known flakiness / risks
- Platform banner intercepts clicks: dismiss first. Wait for popper hidden before the next button click, otherwise the click-outside lands on a stale popper.
- Picker list contents depend on project data; assert only the search input.
- Needs `APP_PREFIX=/app` in the environment (see header).
