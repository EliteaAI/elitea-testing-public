# Test Case: Save As Version keeps module changes on the new version; base version unchanged

- **TMS:** ELITEA-4792 (`agents/modules/ELITEA-4792_save-as-version-keeps-module-changes-base-version-unchanged.md`, requirement elitea_issues#7380)
- **Status:** ready-for-automation
- **Surface:** `agent-modules-dropdown` + version selector (Agent detail)
- **Executed:** 2026-11-23 on DEV (`https://dev.elitea.ai/app`), scripted headless Playwright via the repo's page objects + `agent_id` fixture (MCP chrome binary absent on host). Every step run live; clean pass, no console/product defects.
- **Spec home (suggested):** `automation/tests/ui/agents/test_agent_modules_save_as_version.py`; fixture `agent_id` (fresh agent, deleted at teardown, so no cleanup of versions needed).
- **Neighbours checked:** ELITEA-4790 spec (modules persist after Save/reload; never creates a version) and ELITEA-1888/1889 `test_agent_save_as_version*.py` (version creation, skills preserved; no module assertion) -> NOT coverage. Reuse their page-object methods.

## Steps (as executed) and observations
Dismiss platform banner first (`dismiss_platform_release_banner_if_present`).
1. Navigate `AgentDetailPage.navigate(agent_id)`; `open_modules_menu()`; record every module state (`module_menu_item_keys()` + `module_is_on(key)`), `Escape`, menu hidden. Observed baseline: a fresh agent has `elitea_builder` and `ask_user` ON, other 9 OFF (11 keys: attachments, image_generation, data_analysis, elitea_builder, ask_user, planner, pyodide, swarm, lazy_tools_mode, web_search, code_mode).
2. Open menu, `toggle_module("pyodide")` and `toggle_module("web_search")` (both stay open, no warning dialog). Escape. `save_as_version_button` enabled (and `save_button` enabled).
3. `save_as_version("modules-reg-v2")` (open dialog, type name, confirm; helper waits for convergence). URL becomes `/agents/all/<id>/<new_version_id>?viewMode=owner...`, selector trigger reads `modules-reg-v2`. Save and Discard are DISABLED right after creation (no pending edits).
4. Open Modules on new version: pyodide ON, web_search ON, all other keys equal base (diff == exactly {pyodide, web_search}).
5. `open_version_selector()` + `select_version_by_name("base")`: trigger reads `base`; modules state dict == step-1 record exactly.
6. Switch back via `select_version_by_name("modules-reg-v2")`: state dict == step-4 dict (pyodide, web_search ON).

## Data / choice of modules
Pick two modules dynamically: A = `pyodide`, B = `web_search` (both toggle without a warning dialog, menu stays open; verified). Avoid `code_mode` (warning dialog closes menu) and `attachments` (row centre-click hits the (i) tooltip; use `toggle_module_at_name`). `web_search` is platform-settings dependent: if absent, choose last row not in {code_mode, attachments} and not equal A. Spec must be baseline-relative (`base` snapshot dict from step 1; do not hardcode ON/OFF), and "opposite state" = flip whatever the baseline says for the two keys.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| + Modules button | 1 | `agent-add-modules-button` (`add_modules_button`) | - | testid on DEV (verified) |
| Modules menu | 1 | `agent-modules-menu` (`modules_menu`) | - | testid on DEV (verified) |
| Module row | 1 | `agent-module-menu-item-{key}` (`toggle_module`, `module_menu_item_keys`) | - | testid on DEV (verified) |
| Row switch | 1 | `agent-canvas-tools-toggle-{key}` (`module_is_on`; `checked`) | - | testid on DEV (verified) |
| Save As Version button | 1 | `agent-save-as-version-button` (`save_as_version_button`) | - | testid on DEV (verified) |
| Version dialog name/save | 1 | `agent-version-dialog-name-input` / `agent-version-dialog-save-button` (wrapped by `save_as_version`) | - | testid on DEV (verified) |
| Version selector trigger | 1 | `agent-version-selector-trigger` (`get_version_selector_value`, `open_version_selector`) | - | testid on DEV (verified) |
| Version option | 1 | `version-option-{name}` (`select_version_by_name`) | - | testid on DEV (verified) |
| Save / Discard | 1 | `agent-save-button` / `discard-button` | - | testid on DEV (verified) |

No new locators or page-object methods required; only a small helper in the spec to snapshot `{key: module_is_on(key)}` (open menu, read, Escape, wait menu hidden).

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | base states recorded | step 1 | snapshot dict captured; sanity: 11-ish rows, A and B recorded | asserted (record) |
| Step 2 | two switches change | step 2 | A/B `is_checked` == not baseline | asserted |
| Step 3 | new version `modules-reg-v2` created and opened | step 3 | trigger text == name; URL version segment changed | asserted |
| Step 4 | A,B changed; others match base | step 4 | v2 dict == base with A,B flipped | asserted |
| Step 5 | base shows original states | step 5 | trigger == `base`; dict == base | asserted |
| Step 6 | v2 still shows changes | step 6 | trigger == name; dict == v2 dict | asserted |
| Expected Final State | each version keeps own config | steps 4-6 | covered | asserted |
| Axis 2 | Save/Discard disabled after creating the version (pending edits consumed) | step 3 | not asserted (not in case) | omitted |

## Known Defects
None.

## Clarifications (case-text drift, not defects)
1. Fresh `agent_id` agents start with `elitea_builder` and `ask_user` ON; case's "note every state" handles this, keep baseline-relative.
2. Save As Version works with unsaved module edits without a prior Save (edits ride into the new version; base unchanged) - exactly the case's flow.

## Known flakiness / risks
- Platform banner intercepts clicks: dismiss first. Escape closes menu; wait `modules_menu` hidden before the next action.
- Version switch: use `open_version_selector()` + `select_version_by_name` (waits for data); re-open the menu only after the version converged.
