# Test Case: Agent module switches persist after Save + reload (ON modules on top); Discard restores saved states

- **TMS:** ELITEA-4790 (`agents/modules/ELITEA-4790_*.md`, requirement elitea_issues#7380)
- **Status:** ready-for-automation
- **Surface:** `agent-modules-dropdown` (Agent detail > Tools row > "+ Modules")
- **Executed:** 2026-11-23 on DEV (`https://dev.elitea.ai/app`, existing agent 3832 viewMode=owner, 1920x1080), scripted headless Playwright probes (MCP chrome binary missing on this host, substituted with repo-venv Playwright + dev storage state), every step run live; several probe runs, final state cleaned (all OFF).
- **Spec home (suggested):** `automation/tests/ui/agents/test_agent_modules_dropdown.py` (same file as ELITEA-4789; page object `AgentDetailPage`, already has `add_modules_button`, `modules_menu`, `MODULES_MENU_ITEM`, `MODULES_MENU_TOGGLE_ANY`, `open_modules_menu`). Fixture `agent_id` creates a fresh editable agent (all modules OFF by construction, so no precondition cleanup; Step 9 cleanup still worth running or skip since the fixture deletes the agent).
- Neighbour checked: ELITEA-4789 spec (merged) only opens/scrolls the dropdown, never toggles or saves -> NOT coverage (new observables).

## Steps (as executed) and observations
Helper: dismiss `platform-banner-close` if present first (it intercepts clicks).
1. Open agent, click `agent-add-modules-button`: `agent-modules-menu` visible, all 11 `agent-canvas-tools-toggle-<key>` inputs unchecked, `agent-save-button` disabled, `discard-button` disabled. (OBSERVED: save+discard `disabled=true`.)
2. Toggle Module A ON (see Data below): input checked, menu STAYS open (`agent-modules-menu` count 1), `agent-save-button` and `discard-button` enabled.
3. Scroll the list (wheel over menu) and toggle Module B ON: checked, menu stays open (when B needs no warning).
4. `Escape` (menu count 0), click `agent-save-button`: both Save and Discard become disabled again (`expect.to_be_disabled`, poll; ~1-3s).
5. `page.reload()` (dismiss banner), open Modules: ON modules are the FIRST rows in DOM order (observed `pyodide, code_mode` first, then the OFF ones in original relative order: attachments, image_generation, ...). Assert: first N row keys == the set of ON modules, and every row after has switch unchecked; Save/Discard disabled on load.
6. Toggle Module A OFF (menu stays open), Escape: Save + Discard enabled. Note: the list does NOT re-sort while open (A stays in place until reload).
7. Click `discard-button`: a confirm dialog `discard-confirm-modal` appears (CASE TEXT OMITS IT); click `discard-confirm-button`. Save and Discard disabled again.
8. Open Modules: Module A and B ON, still at top (observed `pyodide:1, code_mode:1, attachments:0 ...`).
9. Cleanup: toggle A and B OFF, Escape, Save -> reload shows all OFF. (Turning code_mode OFF shows no warning.)

## Data / Module choice (IMPORTANT, case drift)
- Module A = `pyodide` (middle of list). Module B: case says "the last module". On DEV the last row is `code_mode`, and switching it ON opens a **warning dialog** (`role=dialog`, title "Warning", buttons Cancel + `agent-code-mode-warning-confirm` "Enable") and CLOSES the dropdown (menu count 0) until confirmed; enabling = click `agent-code-mode-warning-confirm`, ON state applied, Save enabled. So "dropdown stays open after Module B ON" is false for code_mode by design (CodeModeWarningModal.jsx, `requiresCodeModeWarning`). Instructions for implementer: pick Module B = the last row whose toggle needs no warning (observed `web_search`, second to last; menu stays open, Save enables, persists). `web_search`/`code_mode` presence is environment-dependent: select B dynamically = last row key not equal `code_mode`; assert it needs scrolling only if list overflows (do not assert). Optionally a separate variant with code_mode + confirm click (persists the same: reload shows `pyodide, code_mode` on top).
- `lazy_tools_mode`, `planner`, `swarm`, `attachments` were NOT individually probed for side dialogs; only pyodide, web_search, code_mode, planner(partial). Stick to pyodide + web_search.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| + Modules button | 1 | `agent-add-modules-button` (existing `add_modules_button`) | - | testid on DEV (verified) |
| Dropdown | 1 | `agent-modules-menu` (existing `modules_menu`) | - | testid on DEV (verified) |
| Module row | 1 | `agent-module-menu-item-{key}` (existing `MODULES_MENU_ITEM`); click row to toggle (a `li role=menuitemcheckbox`) | - | testid on DEV (verified); real row click toggles |
| Row switch | 1 | `agent-canvas-tools-toggle-{key}` input (state: `checked`) | - | testid on DEV (verified); tabIndex -1 |
| Save | 1 | `agent-save-button` (existing `save_button` in `AgentFormPage`) | - | testid on DEV (verified); enabled/disabled via `disabled` |
| Discard | 1 | `discard-button` (existing `discard_button`) | - | testid on DEV (verified) |
| Discard confirm modal / button | 1 | `discard-confirm-modal` / `discard-confirm-button` (existing in `AgentFormPage` ~line 196) | - | testid on DEV (verified) |
| Code Mode warning confirm | 1 | `agent-code-mode-warning` (modal), `agent-code-mode-warning-confirm` | - | testid on DEV (verified; only for code_mode variant) |
| Platform banner close | 1 | `platform-banner-close` (existing dismiss helper) | - | testid on DEV |

Row order read: DOM order of `[data-testid^="agent-module-menu-item-"]` (existing `module_menu_item_keys()`); row ON state: `agent-canvas-tools-toggle-{key}` `is_checked()` (aria-checked is on the li, input.checked also correct). New page-object methods needed: `toggle_module(key)`, `module_is_on(key)`, `module_on_keys()`; no new locators required.

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | all OFF, Save/Discard disabled | step 1 | switches unchecked, both disabled | asserted |
| Step 2 | A ON, menu open, Save/Discard active | step 2 | checked, menu count 1, both enabled | asserted |
| Step 3 | B ON, menu stays open | step 3 | checked, menu visible | asserted (B = last non-warning module; see Data) |
| Step 4 | saved; Save/Discard disabled | step 4 | disabled after save | asserted |
| Step 5 | A,B ON on top after reload | step 5 | first-N rows == ON set, rest unchecked | asserted |
| Step 6 | A OFF; Save/Discard active | step 6 | both enabled | asserted |
| Step 7 | Discard -> disabled | step 7 | confirm dialog clicked, both disabled | asserted (confirm step added, clarification) |
| Step 8 | A,B still ON on top | step 8 | same as step 5 | asserted |
| Step 9 | cleanup all OFF | step 9 | save + reload all unchecked | asserted (or fixture deletes agent) |
| Axis 2 | A stays in place when toggled while open (no live re-sort) | step 6 | not asserted (non-contract) | omitted |

## Known Defects
None.

## Clarifications (case-text drift, not defects)
1. Discard shows a confirm dialog (`discard-confirm-modal` -> `discard-confirm-button`), absent from case step 7.
2. Switching `code_mode` ON opens a warning dialog and closes the dropdown; "last module" in step 3 must be a non-warning module (use web_search) or the Enable confirm must be clicked.
3. Step 4 "Save and Discard become disabled" holds after Save, with a ~1-3s delay; use polling expects.
4. Saved ON-first ordering is applied only on reload/reopen after reload; also observed after Discard + reopen (state restored, ON on top).

## Known flakiness / risks
- Platform announcement dialog (`platform-banner-center`) intercepts clicks: dismiss first.
- Menu closes on `Escape`; focus/animation: poll with expect, no sleeps.
- Do not click the switch input with force; click the row (`agent-module-menu-item-{key}`) as a user does.
- web_search availability is environment/settings dependent: choose B dynamically, fail loudly if no non-code_mode last-module candidate beyond A.

## Amendment (implementer, ELITEA-4790)
Live run: a fresh `agent_id` agent starts with `elitea_builder` and `ask_user` already ON (not "all OFF"). Spec is baseline-relative: Module A/B must be OFF initially; ON-on-top and cleanup assert `baseline | {A,B}` / `baseline`. Module B = last row not in baseline and not code_mode.
