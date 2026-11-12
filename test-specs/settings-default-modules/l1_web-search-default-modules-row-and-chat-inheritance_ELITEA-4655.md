# Test Case: Web Search Default Modules row (description + independent Chats/Agents toggles) and Chats default propagating to a new chat that really web-searches

- **TMS:** ELITEA-4655 (`settings/default-modules/ELITEA-4655_web-search-default-modules-tooltip-and-chat-inheritance-triggers-search.md`)
- **Status:** ready-for-automation
- **Surface:** `settings-default-modules` (Settings > General > Default Modules; chat Modules panel)
- **Executed:** 2026-11-11 against DEV (`https://dev.elitea.ai/app`, project "Private", user autotest_user_admin), headless Playwright probes, every step run live.
- **Spec home (suggested):** `automation/tests/ui/settings/` (extend `ProjectGeneralSettingsPage`; chat steps reuse `ChatPage`).

## Preconditions
- Web Search available: `GET /api/v2/elitea_core/platform_settings/prompt_lib` -> `tool_spend.web_search.available == true` (DEV: true, toolkit "Tavily Web Search dev Levon"). If false the row is HIDDEN (`requiresWebSearch`) - precondition check, not a product defect.
- **Starting state of the Chats default toggle was OFF**; the test must normalise: read state, set to OFF first if needed (persisted per user/project via `PUT /api/v2/social/module_settings/{project_id}`), and **restore OFF in teardown (finally)**. Persisted state leaks into every later new chat for the account.
- Dismiss the platform announcement dialog (`platform-banner-close` / `BasePage.dismiss_announcement_dialog_if_present`) - it intercepts pointer events (hit live).

## Steps (as executed)
1. Open `/settings/project-general` (`ProjectGeneralSettingsPage.open()` waits on `chat-configuration-section`; wait on `default-modules-section`). Section text starts `DEFAULT MODULES / Module / Chats / Agents`. Note the Web Search row is the **2nd** row (after Image Creation).
2. Web Search row title `Web Search` + description paragraph `Allow the LLM to search the Internet, read web pages, and cite its sources.` (source: `InternalToolsConstants.INTERNAL_TOOLS_LIST` `infoTooltip.text`, rendered as the row paragraph by `DefaultModulesSettings.jsx`).
3. **Tooltip:** in Default Modules the "tooltip" IS the description paragraph - the row has NO `(i)` icon (`[data-info-tooltip]` count in section = 0). The `(i)` InfoTooltip with the same text exists in the chat Modules panel (step 7). Presence assertion = paragraph visible and non-empty. See Clarification below.
4. Row has exactly two `input[role="switch"]` (index 0 = Chats, index 1 = Agents), independently checkable (observed Chats ON / Agents OFF after toggling Chats only; reload confirmed Agents unchanged). Column headers `Chats`, `Agents`.
5. Click the Chats switch (ON). Autosave is on **blur** (`useFormikAutoSaveOnBlur`): click the switch, then click neutral area (`body` at 5,5) -> `PUT /api/v2/social/module_settings/575` 200. `reload` -> Chats switch checked, Agents unchecked. (Wrap with `expect_response(module_settings, PUT/POST/PATCH)` like `enable_midturn_input`.)
6. Create new chat: `sidebar-create-button` (`ChatPage` existing "new conversation" helper ~L3070) -> URL stays `/app/chat`, `chat-new-conversation-greeting` visible.
7. `plus-menu-button` click -> **click** (not hover) `internal-tools-menuitem` (headless hover did not open the flyout on a fresh chat; click did - existing `open_internal_tools_menu` hovers; implementer: verify, fall back to click). Panel shows 11 `modules-toggle-*` switches; `modules-toggle-web_search` is **last in DOM / at bottom (needs scroll in the 1000px viewport)** and `checked == True`; all others False.
8. (scroll) Assert `modules-toggle-web_search` checked via `ChatPage.is_module_toggle_checked("web_search")` (existing, testid-based). Control: with Chats default OFF the same panel has web_search unchecked (and, with it OFF, the earlier new-chat panel had no web_search ON).
9-10. Close panel (click outside), type prompt `search me some todays sport news article` in `chat-message-input`, click `chat-send-button`; wait for answer (`ChatPage` wait_for_response style; DEV answer ~15-45 s incl. 11 s thinking).
11. `chat-answer-tool-chip` (existing `ChatPage.answer_tool_chip`) visible with text `Web Search: web_search` (+ `· 2.6s` duration). `chat-answer-thought-accordion` also present. Assert chip text contains `web_search`.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Default Modules section | 1 | `default-modules-section` | - | testid on DEV (verified) |
| Web Search row title/description | 4 css/ role-less | scope `div:has(> div > :text-is("Web Search"))` inside section (pattern as `MIDTURN_INPUT_SWITCH`) | `settings-default-modules-web-search-row` | ladder - no testid on DEV; unique inside `default-modules-section` (the separate `web-search-section` card also has a "Web Search" title - MUST scope to `default-modules-section`) |
| Web Search Chats switch | 4 css | row-scope + `input[role="switch"]` (the two switches are enumerated as the row's matches; Chats=first, Agents=second - **positional**, see Question) | `settings-default-modules-web-search-chats-switch` / `-agents-switch` | ladder - no testid on DEV |
| Column headers | 2/4 | text `Chats` / `Agents` in section | `settings-default-modules-chats-column-header` | ladder |
| Chat `+` / Modules / toggle | 1 | `plus-menu-button`, `internal-tools-menuitem`, `modules-toggle-web_search` | - | testid on DEV (verified) |
| Tool chip | 1 | `chat-answer-tool-chip` | - | testid on DEV (verified) |
| Autosave | - | response URL contains `module_settings`, PUT, 200 | - | observed |

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | section loads | step 1 | `default-modules-section` visible | asserted |
| Step 2 | row descriptive text | step 2 | description text visible | asserted |
| Step 3 | tooltip present | step 3 | description paragraph present (live: no (i) in settings; (i) in chat panel) | clarification |
| Step 4 | separate Chats/Agents toggles | step 4 | 2 switches, headers, independence | asserted |
| Step 5 | ON + persists | step 5 | autosave 200 + reload checked | asserted |
| Steps 6-8 | new chat shows web_search ON | steps 6-8 | `is_module_toggle_checked("web_search")` | asserted |
| Steps 9-11 | prompt, response, tool-use indicator | steps 9-11 | tool chip text | asserted |
| Axis 2 extra | Agents switch unchanged after Chats toggle | step 5 | `not is_checked()` | grounded: proves "independent" in Pass criteria |

## Known Defects
None.

## Clarifications (note in findings, not a bug)
- Case step 3 says "hover/inspect tooltip": in Default Modules the descriptive paragraph is the tooltip text; no hover icon exists. Presence-only assertion on the paragraph is the honest contract.
- Case step 5 "save": no Save button - blur autosave.
- Step 7 "click +, open Modules": on a new chat the flyout opened on click of the Modules menuitem; plain hover did not (possibly headless mouse-event artefact).

## Known flakiness / risks
- Web-search LLM answer is non-deterministic: assert the chip (tool use), never answer content. Tool needs `web_search` toolkit alive on DEV (Tavily); if `platform_settings...available` false -> precondition failure, not skip-masking: fail loudly.
- Shared account state: toggle persists; always restore in `finally`. Do not run in parallel with other module-defaults specs (e.g. ELITEA-2876 mid-turn uses the same module_settings payload).
- Platform announcement dialog can render late.
