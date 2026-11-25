# Test Case: Add chat starters up to the admin limit; counter and disabled add button

## Metadata
- **TMS ID**: ELITEA-4863 (case file: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/configurable-chat-starters-limit/ELITEA-4863_add-chat-starters-up-to-the-admin-limit-and-verify-the-counter.md`)
- **Priority**: high (l1)
- **Environment Explored**: DEV `https://dev.elitea.ai/app`, headless Chromium via repo Python Playwright (MCP Chrome absent on this host; substitution noted), storage state from `dev_storage_state.py`
- **Status**: `ready-for-automation`
- **Case snapshot**: missing from `.agents/automation/elitea-4863-chat-starters-limit/cases/`; read from TMS sibling clone instead.
- **Neighbours checked**: `AgentFormPage` already declares `conversation_starters_section`, `conversation_starter_add_button`, `conversation_starter_inputs`, `add_conversation_starter()`; `ApiClient.get_platform_settings()` reads the prompt_lib settings. No spec asserts the n/M counter or the at-limit state (grep `starters added` / `limit of chat starters` in automation/ -> none). Not already-covered.

## Live observations (all 10 steps executed)
- Step 1/2: with the user's browser-session cookies, `GET /api/v2/admin/plugin_config_values/administration/guardrails` -> 200, `values.max_conversation_starters`; `GET /api/v2/elitea_core/platform_settings/prompt_lib` -> 200, `conversation_starters_max`. On DEV M = 6 and both agree. The Bearer `ELITEA_API_TOKEN` was 401 on both endpoints via requests (not investigated further) - implement with the page's `context.request` (cookie auth), which works. Test must read M, never hardcode 6.
- Step 3: Agents list -> `agents-add-button` opens a menu (`agents-add-new` = "New Agent") -> `/agents/create?viewMode=owner` (or navigate directly). The platform announcement dialog (`platform-banner-close`) can intercept clicks; dismiss it first (BasePage helper).
- Step 4: counter `0/6 starters added.`, add button enabled. Section is already expanded (no click needed).
- Steps 5-7: each add click adds a textarea; **the add button is disabled while the last starter field is empty**, so type text into field n before the next click (case order already does this). Counter read `1/6 ... 6/6 starters added.` after each; add enabled for 1..5, disabled at 6.
- Step 8: button is wrapped by `<div aria-label="You have reached the limit of chat starters">`; hovering the wrapper shows `[role="tooltip"]` with that text.
- Step 9: clicking the disabled button times out (not clickable); field count stays 6, counter `6/6`.
- Step 10: the create form has a `Cancel` button (no testid; role=button name "Cancel"; `discard-button` is NOT present on create) -> dialog "Are you sure you want to discard changes?" with `Cancel`/`Discard` buttons (no testids) -> lands on `/agents/all`; no agent with the name exists.
- Console / network: no errors seen in the probe.

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| 1 | `agents-add-button` / `agents-add-new` | - | testid on DEV ✓ |
| 1 | `agent-name-input`, `agent-description-input` | - | testid on DEV ✓ (name verified; description used in case Notes, present on form) |
| 1 | `agent-conversation-starters-section` | - | testid on DEV ✓ |
| 1 | `agent-conversation-starters-limit-counter` (text `n/M starters added.`) | - | testid on DEV ✓ (new vs. existing page object - needs declaring) |
| 1 | `agent-conversation-starter-add` (disabled attr for at-limit) | - | testid on DEV ✓ (existing field) |
| 1 | `agent-conversation-starter-input` (enumerate, count == n) | - | testid on DEV ✓ (existing field) |
| 3/4 | at-limit tooltip wrapper `[aria-label="You have reached the limit of chat starters"]` (hover) | `agent-conversation-starter-add-tooltip-wrapper` | ladder - no testid on DEV; attribute css unique on the form |
| 2 | tooltip text: `role=tooltip` | - | MUI tooltip, text exact |
| 2 | Cancel button `role=button name="Cancel"` on create form | `agent-cancel-button` | ladder - no testid on DEV (existing `cancel_button` field has a testid not served; verify/fix) |
| 2 | confirm dialog `role=dialog` + button `Discard` | `agent-discard-confirm-button` | ladder - no testid on DEV; scope to dialog. (Existing `discard_confirm_*` fields are for the edit-page tab bar, not this create dialog.) |

## Steps for implementation
Pure UI + two API reads; no agent is saved, so no cleanup beyond Discard. Assertions: M in 1..10 and equal across both APIs; counter text after each add; add disabled exactly at M (enabled before); tooltip text; no new field after forced attempt (use `to_be_disabled`, then assert count unchanged); post-discard, agents list contains no agent with the name (UI list search or API list).

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| Step 1 | M whole number 1..10 | admin API read | covered |
| Step 2 | editor limit == M | prompt_lib API read | covered |
| Step 3-4 | form, counter 0/M, add enabled | UI | covered |
| Steps 5-7 | counter n/M each, add enabled until M | loop 1..M | covered |
| Step 8 | at-limit tooltip | hover wrapper | covered |
| Step 9 | disabled, no new field | disabled assertion + count | covered |
| Step 10 | Discard creates nothing | Cancel -> Discard -> list check | covered |
Axis 2: none beyond the case.
## Known Defects
None. Note: case text says "Discard"; on the create form the control is `Cancel`, then a confirm `Discard` (clarification only, behaviour equals intent).
