# Test Case: Agent "+ Modules" dropdown opens from the Tools row, lists every module once, scrolls to a fully visible last module

- **TMS:** ELITEA-4789 (`agents/modules/ELITEA-4789_modules-dropdown-opens-lists-all-modules-and-scrolls-to-last-module.md`)
- **Status:** ready-for-automation
- **Surface:** `agent-modules-dropdown` (Agent detail > Tools row > "+ Modules")
- **Executed:** 2026-11-23 on DEV (`https://dev.elitea.ai/app`, existing agent 3832 viewMode=owner, 1920x1080), scripted headless Playwright probes, every step run live. Console errors: none.
- **Spec home (suggested):** `automation/tests/ui/agents/`, extend `AgentDetailPage` (fixture `agent_id` creates a fresh editable agent; read-only test, no mutation).

## Preconditions
- Editable agent: use `agent_id` fixture, `AgentDetailPage.navigate(agent_id)`; dismiss `platform-banner-close` if present.
- Viewport 1920x1080. On DEV the menu has 11 rows and overflows (list `scrollHeight 448 > clientHeight 325`). Assert overflow precondition (`scrollHeight > clientHeight`) loudly; do not skip.

## Steps (as executed)
1. Tools row buttons, all `y=124`, DOM/x order: `agent-add-toolkit-button` (Toolkit), `agent-add-mcp-button` (MCP), `agent-add-agent-button` (Agent), `agent-add-pipeline-button` (Pipeline), `agent-add-modules-button` (Modules). Assert order by bounding-box x (or DOM order of `[data-testid^="agent-add-"]` restricted to these 5; `agent-add-skill-button` sits on a separate row below, y=232, exclude).
2. Old grid gone: no text "Show all"/"Show less" (count 0), no "MODULES" header (count 0).
3. Click `agent-add-modules-button` -> `agent-modules-menu` (Paper) appears; `agent-modules-search-input` (placeholder `Search modules...`, aria-label `Search modules`) present and autofocused. Button has `aria-haspopup=menu`, `aria-expanded` toggles.
4. Row (`li[role=menuitemcheckbox]`, testid `agent-module-menu-item-<key>`): module svg icon, name text, `[data-info-tooltip]` (i) icon (1 per row), switch input `agent-canvas-tools-toggle-<key>` (1 per row, tabIndex -1, `aria-checked` on the li).
5. Wheel over the menu (`mouse.move` to menu centre, wheel 15x400): inner `ul` (`[aria-label="Modules"]`, overflow-y auto) `scrollTop == scrollHeight-clientHeight` (123/123); `window.scrollY` stays 0 (page does not scroll).
6. Last row (`code_mode`) at scroll end: `row.bottom (530) <= ul.bottom (534)` and `<= menu.bottom (535)`; `row.top (490)` inside. Assert `last.bottom <= list.bottom + 1` (sub-pixel tolerance).
7. Rows live (11, DOM order): attachments, image_generation, data_analysis, elitea_builder, ask_user, planner, pyodide, swarm, lazy_tools_mode, web_search, code_mode. All present once (all 11 `agent-module-menu-item-*` testids unique; titles unique).
8. Scroll back: `scrollTop 0`, first row top >= search container bottom (assert via bounding boxes).
9. `Escape` -> `agent-modules-menu` count 0 (focus returns to the Modules button).

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| + Modules button | 1 | `agent-add-modules-button` | - | testid on DEV (verified) |
| + Toolkit / MCP / Agent / Pipeline | 1 | `agent-add-toolkit-button` (existing `add_toolkit_button`), `agent-add-mcp-button` (`add_mcp_button`), `agent-add-agent-button` (`add_agent_button`), `agent-add-pipeline-button` (declared in `pipeline_detail_page.py`; declare on `AgentDetailPage`) | - | testid on DEV (verified) |
| Dropdown paper | 1 | `agent-modules-menu` | - | testid on DEV (verified) |
| Search input | 1 | `agent-modules-search-input` | - | testid on DEV (verified) |
| Module rows | 1 | `[data-testid^="agent-module-menu-item-"]` (prefix, enumerate all); per-row `agent-module-menu-item-{}` template | - | testid on DEV (verified) |
| Row switch | 1 | `agent-canvas-tools-toggle-{}` | - | testid on DEV (verified) |
| Scroll container (ul) | 2 | `role=menu`, name `Modules` scoped within `agent-modules-menu` | `agent-modules-menu-list` | ladder - no testid on DEV; unique inside the menu (UL, aria-label "Modules") |
| Row (i) icon | 4 css | `[data-info-tooltip]` scoped within a row | `agent-module-menu-item-info-icon-{}` | ladder - no testid on DEV; 1 per row verified |
| Row icon | - | assert row has an svg before the name (`svg` count 2 = icon + (i)) | - | observed |
| Old grid text | 3 | text `Show all` / `Show less`, `MODULES` absent | - | observed count 0 |

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | order Toolkit, MCP, Agent, Pipeline, Modules | step 1 | x-order of 5 testids | asserted |
| Step 2 | no grid, no Show all/less | step 2 | counts 0 | asserted |
| Step 3 | dropdown with search + list | step 3 | menu + search placeholder visible | asserted |
| Step 4 | icon, name, (i), switch | step 4 | per row (loop all rows) | asserted |
| Step 5 | list scrolls, page does not | step 5 | scrollTop==max, window.scrollY==0 | asserted |
| Step 6 | last row fully visible | step 6 | bounding box vs list/menu bottom | asserted |
| Step 7 | all modules once, reference list | step 7 | uniqueness + count + reference (see Clarification) | asserted |
| Step 8 | first row visible under search | step 8 | bounding boxes | asserted |
| Step 9 | Escape closes | step 9 | menu hidden | asserted |
| Axis 2 | list overflows (precondition for step 5/6) | step 5 | scrollHeight > clientHeight | grounded: otherwise scroll steps are vacuous |

## Known Defects
None.

## Clarifications
- **Reference list**: case says reference = Settings > General > Default Modules. Live that list (`image_generation, web_search, data_analysis, internal_mcp, skill_builder, project_context_builder, ask_user, planner, pyodide, swarm, lazy_tools_mode`) is NOT the agent menu list (the agent menu has `attachments, elitea_builder, code_mode`, lacks `internal_mcp, skill_builder, project_context_builder`). Per the case's own note ("build the reference list from the environment under test") the implementer should NOT compare to Settings. Independent oracle: agent module definitions from the frontend `InternalToolsConstants` are not reachable from the test; use (a) all rows unique by testid and by title, (b) row count equals the count of `agent-canvas-tools-toggle-*` inputs, (c) each of the 11 expected keys above present, as a named required subset (list may grow: assert subset, not equality) , (d) search filter cross-check: typing each row title shows that row (optional). Raise to lead if a stricter oracle is wanted. `web_search`/`code_mode` presence is environment-dependent (platform settings); treat keys beyond the first 9 as optional-subset.
- Case "Search modules..." filtering is client-side on title (`includes`), no network.

## Known flakiness / risks
- Menu animates (Grow): wait on `agent-modules-menu` visible plus short settle before measuring boxes (use expect polling, not sleep).
- Mouse wheel needs the pointer over the menu; use `page.mouse.move` then `mouse.wheel` (or set `scrollTop` is NOT acceptable: step says wheel).
- Platform announcement dialog can intercept clicks.
