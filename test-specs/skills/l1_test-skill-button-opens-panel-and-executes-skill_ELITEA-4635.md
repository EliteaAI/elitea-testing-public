# Test Case: Test Skill button in editor opens test panel; send message; verify skill execution steps and response

## Metadata
- **TMS ID**: ELITEA-4635
- **Priority**: l1 (TMS: critical regression)
- **Environment explored**: DEV `https://dev.elitea.ai/app` (`APP_PREFIX=/app` must be set - `automation/.env.test` absent in this sandbox, bare ELITEA_URL gives a 404 page), project Private (575), admin account, 2026-11-11. Scripted python-playwright probes (SkillsListPage/SkillDetailPage transit), 2 full live runs with a per-run API-created skill.
- **Status**: **ready-for-automation** (minor case-text drift, see Clarifications)
- **surface_key**: skill-editor-test-panel
- **Neighbours read**: ELITEA-4634 AFS + `test_own_skill_run_message_exchange.py` (Run from list row; NOT the toolbar button), ELITEA-2442 AFS/spec `test_skill_test_panel_response_actions.py` (already uses `SkillDetailPage.open_test_skill_panel/send_test_message/wait_for_test_response`; asserts only read-aloud/copy), ELITEA-2440/4631. Not already-covered: no merged spec asserts the "Skill: <name>" execution chip/"Thought for" accordion nor the button-click -> panel open as its own observable.

## Clarifications (case-text drift, not defects)
1. Skill is created per-run via API (not pre-existing "lmt-answer-format"): shared-data independence.
2. Input placeholder IS "Type your message..." here (unlike the Run-from-list panel in 4634 where it was empty) - assertable.
3. Send button is the shared `chat-send-button` (arrow icon, no text).
4. "Thought for X secs" is the accordion `chat-answer-thought-accordion` ("Thought for 2 secs"); skill badge is `chat-answer-tool-chip` reading `Skill: <skill-name>`; model chip `chat-answer-model-chip` ("Anthropic Claude Haiku 5.5" on DEV; model varies - assert non-empty only); duration chip `chat-answer-chip-duration` (e.g. "2.2s").
5. Step 13/14 "no error / success indicator": there is no explicit success icon; assert absence of `[role=alert]` and of error text in the panel, and that response is non-empty.
6. Panel is NOT open on page load (`skill-test-panel` visible=True only after click). A second click on the button did not behave as a simple re-click in my probe (timed out - likely the button is covered once the panel is open); do not assert toggle/close via this button.
7. Sender label on user message: avatar, user display name (account-dependent - never asserted), "to", skill name, then text "run".

## Preconditions / Test data (generate-per-test)
- `skill_api.create_skill(name=f"autotest-4635-{ts}", description="4635 probe", instructions="Convert the user text to UPPERCASE and reply with only that.")` -> id. Message "run" per case; expected reply `RUN` (observed `RUN` 3/3-ish: 2 runs). Assert case-insensitive non-empty reply, `RUN` preferred but LLM-nondeterministic: assert response non-empty and (soft) contains "run".
- Teardown (finally): `skill_api.delete_skill(id)`; conversation id from URL `?run=(\d+)` -> `conversation_api.delete_conversation(id)` (verified 204-style success).
- Banners: modal `platform-banner-center` (~5s after load) and corner banner `platform-banner-close` that covers the send button - dismiss both before clicking send (`SkillsListPage.dismiss_announcement_dialog_if_present`; for the corner banner click `platform-banner-close` with ~8s wait, ignore timeout).
- Transit: `SkillsListPage().navigate()` + dismiss + `SkillDetailPage.navigate(id)` (direct detail navigation first-load can show a 404/blank if the list was never visited; visit list first as 4634 does).

## Observed flow (live)
1. Skill editor `/skills/all/{id}`: **[superseded 2026-11-25, see Adjustment]** originally the toolbar had two buttons `edit-skill-with-ai-button` ("Edit with AI") then `skill-test-button` ("Test Skill"). Now: `skill-test-button` (text "Test", aria-label "Test skill") sits in the Instructions header (`skill-instructions-header`); `edit-skill-with-ai-button` is at the right end of the Settings/Files tab bar. Visible+enabled; `skill-test-panel` not visible before click.
2. Click `skill-test-button` -> `skill-test-panel` visible (now a third column "Test" inside `skill-run-pane`; URL gets `?panel=test`). Panel contains `chat-message-input` (placeholder "Type your message..."), `chat-send-button`, `chat-attach-button`, `model-selector-button`, header `skill-run-history-button`, `chat-clear-button`, `skill-test-panel-close`.
3. Fill "run" -> input value "run". Click send. Two `chat-message-item`: user (text "run", author) then AI.
4. Reply ~7s total: AI item contains `chat-answer-thought-accordion` "Thought for 2 secs", `chat-answer-tool-chip` "Skill: <name>", `chat-answer-model-chip`, `chat-answer-chip-duration`; `skill-test-last-response` text `RUN`; action buttons present.
5. URL -> `/skills/all/{id}?run={convId}`. Network non-socket POST: only `conversations/prompt_lib/575` (201). Console errors: none. `[role=alert]` count 0.

## Handles Reference (verified on DEV 2026-11-11)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `skill-test-button` (`SkillDetailPage.test_skill_button`; scoped via `TEST_BUTTON_IN_HEADER` ScopedLocator within `instructions_header`) - text "Test", aria-label "Test skill", lives in the Instructions header | - | testid on DEV ✓ (unchanged; location moved, PR #1575) |
| testid | `skill-instructions-header` (`instructions_header`) - scope for the Test button | - | testid on DEV ✓ |
| testid | `skill-view-settings` / `skill-view-files` (`skill_view_settings_tab`) - tab bar; `edit-skill-with-ai-button` now at its right end | - | testid on DEV ✓ |
| testid | `edit-skill-with-ai-button` | - | testid on DEV ✓ (relocated to tab bar) |
| testid | `skill-test-panel` (`test_panel`) inside `skill-run-pane` | - | testid on DEV ✓ |
| testid | `chat-message-input`, `chat-send-button`, `chat-message-item`, `skill-test-last-response` | - | testid on DEV ✓ (existing in SkillDetailPage/ChatPage) |
| testid | `chat-answer-thought-accordion`, `chat-answer-tool-chip`, `chat-answer-model-chip`, `chat-answer-chip-duration` | - | testid on DEV ✓ (check whether ChatPage/SkillDetailPage already declare; else add class-level testid fields scoped to the AI message) |
| testid | `platform-banner-center`, `platform-banner-close` | - | testid on DEV ✓ |
| attr | placeholder "Type your message..." via `get_attribute("placeholder")` on `chat-message-input` | - | observed |

## Steps (AFS)
1. Create skill via API; open list (dismiss banners) and `SkillDetailPage.navigate(id)`. **Verify** `skill-test-button` within `skill-instructions-header` is visible+enabled, text "Test" (was "Test Skill"); `edit-skill-with-ai-button` present in the Settings/Files tab bar; `skill-test-panel` not visible.
2. Click `skill-test-button`. **Verify** `skill-test-panel` visible AND URL contains `panel=test`.
3. **Verify** `chat-message-input` visible, placeholder "Type your message...", `chat-send-button` visible; `chat-message-item` count 0.
4. Dismiss corner banner; fill "run". **Verify** input value == "run".
5. Click `chat-send-button`. **Verify** first `chat-message-item` contains "run" and the sender label `to <skill name>` (no username asserted - account-independent).
6. Condition-wait reply (`wait_for_test_response`). **Verify** `chat-answer-thought-accordion` visible and text matches `Thought for \d+ secs?`.
7. **Verify** `chat-answer-tool-chip` text == `Skill: {skill_name}` (case 8-9), `chat-answer-model-chip` visible with non-empty text.
8. **Verify** `skill-test-last-response` non-empty (relevant: contains "run" case-insensitive), no `[role=alert]`, no error/failed text in panel, no console errors (steps 11-14).
9. Teardown: delete conversation (from `?run=`) and skill.

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1 Test btn visible (now in Instructions header; Edit with AI moved to tab bar) | | AFS 1 | covered (label/location per TMS PR #348) |
| 2 click opens Test panel (third column) | URL `panel=test` | AFS 2 | covered (position not asserted; URL added) |
| 3 input/placeholder/send icon | | AFS 3 | covered |
| 4-5 type/send | | AFS 4-5 | covered |
| 6 message in thread w/ avatar/name | | AFS 5 | covered (skill name in sender label; username deliberately not asserted) |
| 7 Thought for X secs | | AFS 6 | covered |
| 8-9 Skill badge + tool icon + model | | AFS 7 | covered (model name non-empty only; varies) |
| 10-12 response, relevant | | AFS 8 | covered (relevance = deterministic instruction, contains "run") |
| 13-14 no error / success status | | AFS 8 | **clarification**: no explicit success icon; absence of alerts/errors asserted |
Axis 2 extras: console-error-free; `?run=` URL (grounded: observed, same as 4634).

## Known defects
None.

## Automation Hints
- Extend nothing in page objects beyond declaring the four `chat-answer-*` testid fields (check `ChatPage` first - likely reusable) on `SkillDetailPage`; `test_skill_button`, `open_test_skill_panel`, `send_test_message`, `wait_for_test_response`, `get_last_test_response` exist. `send_test_message` does not dismiss the corner banner - dismiss first.
- Do NOT use `open_test_skill_panel()` for step 2's click assertion if it short-circuits when panel already visible; it is fine here (panel hidden on load) but assert panel hidden beforehand.
- Cleanup via `skill_api` + `conversation_api` fixtures. Markers: `@pytest.mark.tms("ELITEA-4635")` + `@allure.issue` pair; skills/p1/regression. New test in `tests/ui/skills/test_skill_editor_test_button_execution.py`.
- Env note: run with `APP_PREFIX=/app` (and ELITEA_URL) if `.env.test` is missing.

## Adjustment (2026-11-17, card #2954 - account independence)
Step 5 previously asserted the literal `autotest_user_admin` and failed under other accounts (e.g. `autotest_user_2`). Now asserts the first `chat-message-item` contains "run" and matches `to <skill name>` from the sender label; no username is asserted or required. Step 7 unchanged: `chat-answer-tool-chip` == `Skill: <name>` (skill) and `chat-answer-model-chip` visible/non-empty (LLM was called).

## Adjustment (2026-11-25, class A - UI drift)
- **What changed:** the button moved. Old: toolbar with `Edit with AI` then `Test Skill`. New: `Test` button (aria-label "Test skill") in the Instructions (SKILL.md) header; `Edit with AI` at the right end of the Settings/Files tab bar. Clicking Test opens a third column "Test" (`skill-test-panel` in `skill-run-pane`) and the URL gets `?panel=test`; nothing is sent automatically.
- **Why:** intentional product change (EliteaUI PR #1575 / elitea_issues#7573); TMS case updated in EliteaAI/onetest-ai-tm-Elitea#348. Not a defect.
- **Triage:** class A. All testids unchanged (`skill-test-button`, `skill-test-panel`, `edit-skill-with-ai-button`, `skill-instructions-header`, `skill-view-settings`, `skill-view-files`; testid on DEV).
- **Expected-result changes:** Step 1 label "Test Skill" -> "Test" and location (Instructions header); Step 2 adds `panel=test` URL assertion. Steps 3-14 unchanged. No assertion weakened.
- **Code:** `pages/skill_detail_page.py` (new `instructions_header`, `TEST_BUTTON_IN_HEADER` ScopedLocator, `skill_view_settings_tab`; descriptions updated) and spec Steps 1-2.
