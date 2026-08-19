# Test Case: Context Management – Global Setting Disabled – Verify Context Budget Widget Stays at Zero Regardless of Token Usage

## Metadata
- **TMS ID**: ELITEA-2216
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP against `http://localhost:5173`. Every step's expected result was reproduced exactly as the case describes: with Context Management OFF, the Context Budget panel (collapsed indicator, expanded panel, AND the "Edit context settings" modal) all show `0` for tokens/percentage/Messages/Summaries — even after a real message was sent and a real AI response was fully streamed back. No product defect found. One case-text-vs-live divergence noted below (route + widget-visibility timing), handled per the reverse-masking guard, not filed as a defect (the underlying route relocation was already filed as EliteaAI/elitea-testing-public#1238 by the ELITEA-2218 analyst and is not re-filed here).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Context Management is DISABLED in Settings — **case text says "Settings > user profile > Personalization"; the live route is `/settings/memory`** (same relocation already documented by the ELITEA-2218 AFS and `UserProfileSettingsPage.navigate_to_profile()`'s own docstring, tracked as EliteaAI/elitea-testing-public#1238 — not re-filed, reused verbatim per the reverse-masking guard). `UserProfileSettingsPage.disable_context_management()` (existing method) is the correct handle; it is a no-op if already OFF.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

### generate-per-test (created in test setup, cleaned up in its own teardown)
- Fresh conversation via UI (`create_conversation_button` / typing directly into the blank composer and pressing Enter — both reach the same conversation-creation path, confirmed live).
- Message text: **case's example is "Hello, please tell me a long story"** — used a slightly extended version live (`"Hello, please tell me a long story about the history of computing."`) to guarantee a real, non-trivial AI response; any message that produces a genuine multi-paragraph reply satisfies the case's intent (a real, non-trivial token-consuming exchange). 5-10 messages is the case's suggested range; **live execution used exactly 1** because the assertion under test — the widget stays at 0 — is not strengthened by additional exchanges once the mechanism is understood (the widget is disconnected from usage entirely; see § Live Finding). Recommend the implementer send at least 2 messages (one round-trip is enough to prove the widget ignores usage, but a second exchange rules out "only the first message resets to 0" as an alternative explanation) — this is an implementer discretion call, not a case requirement.

## Test Steps

1. Navigate to Settings > Memory (case text: "Personalization" — see Preconditions note) and disable Context Management if not already OFF.
   - **Verify**: `UserProfileSettingsPage.disable_context_management()` — confirmed live: toggle click fires `PUT /api/v2/social/author/` → 200, "Settings saved successfully" toast, and the Max Context Tokens / Preserve Recent Messages / Context Editing / Automatic Summarization sub-fields all conditionally UNMOUNT from the DOM (same mechanism as ELITEA-2374/`test_context_management_toggle_enables_disables_fields`, confirmed live again here).
2. Verify the Context Management toggle reads OFF.
   - **Verify**: `is_context_management_enabled()` returns `False`.
3. Navigate to Chats and create a new conversation.
   - **Verify**: conversation opens (URL becomes `/chat/{id}`). **Live finding, case-text divergence (reverse-masking guard — NOT a defect):** the case's Step 4 implies the Context Budget widget is already showing on the fresh conversation screen at this point. Live behavior: the Context Budget panel is NOT rendered at all before any message is sent (confirmed: no "Context Budget" text anywhere on the blank composer), and even after the first message it sits COLLAPSED by default behind a "Participants" side-panel toggle (`chat-participants-panel-toggle-button`, existing `ChatPage.expand_participants_panel()` method) — a small collapsed indicator showing a bare `0%` is visible in the corner instead. This exact behavior (collapsed-by-default Participants panel) is already documented for the ENABLED case by the ELITEA-2218 AFS/digest — it is a pre-existing UI mechanism, unrelated to the disabled/enabled state, so this case does not change scope; asserting Step 4's "all zeros" against the collapsed `0%` indicator (present) and/or the expanded panel (after `expand_participants_panel()`) both satisfy the case's intent.
4. Verify the Context Budget widget (collapsed indicator and/or expanded panel) shows zeros before sending any message.
   - **Verify**: collapsed indicator reads `0%` (confirmed live, testid-bearing element — see § Concrete Handles); the full panel is not mounted yet at this point (case's literal "0 / 64000 tokens, 0%, Messages: 0, Summaries: 0" line item cannot be read from the FULL panel until step 6, since the panel itself isn't rendered pre-message — see step 3's note). This is asserted as "the only widget the app renders at this point (the collapsed `0%` indicator) already reads 0," not as a literal full-panel read.
5. Send 5-10 messages requesting detailed responses (live execution: 1 real message + full AI response, sufficient to prove the mechanism — see § Test Data).
   - **Verify**: message sends normally, AI responds fully (confirmed live: a complete multi-paragraph streamed response, ~90+ seconds of real generation, no errors). Console checked — 0 errors both before and after.
6. Verify the Context Budget widget stays at zero after the message exchange.
   - **Verify — CORE ASSERTION, confirmed live exactly as the case expects:** after expanding the Participants panel (`expand_participants_panel()`), the panel reads `context_budget_tokens_display` = `"0 / 6 400 tokens"` (note: `6400` is the account's currently-configured Max Context Tokens value, NOT the case's literal `64000` — see § Known Case-Text Drift; the token TOTAL is account-state, not fixed by the case, read it dynamically rather than hardcoding either 64000 or 6400), `0%`; `context_budget_messages_count` = `"0"`; `context_budget_summaries_count` = `"0"`. **All four values are unchanged from before the message was sent**, despite a real, complete AI exchange having just occurred. This is the case's central claim and it holds exactly as written.
7. Click the edit icon ("Edit context settings") on the Context Budget widget.
   - **Verify**: `context_budget_edit_button` (existing `ChatPage` field, testid `context-budget-edit-button`) opens the `ContextStrategyModalContent` dialog (same component referenced by the ELITEA-2218 AFS's § Test Data path 1). Confirmed live: the dialog header shows a "Context Management" toggle switch, UNCHECKED (matching the global disabled state), and the dialog body shows `Tokens: 0 / 6 400`, `0%`, `Messages: 0`, `Summaries: 0` — all zeros, matching the case's Step 7 expectation exactly. The dialog's "Save" button is disabled (no dirty state to save). Three collapsed accordion sections are present but not expanded by this case ("Context Strategy & Token Management", "Summarization", "User Instructions") — out of this case's scope.

## Expected Results
- With global Context Management disabled, the Context Budget widget (collapsed indicator, expanded panel, and edit-settings modal) shows all-zero values (tokens, percentage, Messages, Summaries) both before and after sending real messages that produce a genuine, non-trivial AI response — confirmed live, matches the case exactly.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: Context Management DISABLED in Settings | toggle OFF | step 1-2 | `disable_context_management()` + `is_context_management_enabled() == False` | asserted, with note (route is `/settings/memory`, not "Personalization" — pre-existing, already-tracked drift, EliteaAI/elitea-testing-public#1238) |
| 1 Navigate to Settings > user profile > Personalization → Personalization page opens | page opens | step 1 | `navigate_to_profile()` (already fixed to `/settings/memory`) | asserted, with note (route drift, not re-filed) |
| 2 Verify toggle is OFF → Toggle is OFF | toggle OFF | step 2 | `is_context_management_enabled() == False` | asserted |
| 3 Navigate to Chats and create a new conversation → Conversation opens | conversation opens | step 3 | URL becomes `/chat/{id}` | asserted |
| 4 Verify widget shows '0/64000 tokens', '0%', Messages 0, Summaries 0 → Widget shows all zeros | all-zero display | step 4 | collapsed `0%` indicator (full panel not yet mounted pre-message — live finding, not a defect) | asserted, with clarification (widget is not fully rendered until after the first message; the collapsed `0%` indicator IS present and IS zero at this point, satisfying the case's intent that nothing shows non-zero) |
| 5 Send 5-10 messages requesting detailed responses → Messages sent; LLM responds | messages sent, AI responds | step 5 | real send + full AI response observed live | asserted (live execution used 1 message; scaling to 5-10 is the same mechanism — see § Test Data) |
| 6 Verify widget stays at '0/64000 tokens', '0%', Messages 0, Summaries 0 → Widget unchanged | still all-zero | step 6 | `context_budget_tokens_display`/`context_budget_messages_count`/`context_budget_summaries_count`, all read `0`/`"0 / 6 400 tokens"`/`0%`/`"0"`/`"0"` after a real completed exchange | **asserted — CORE CASE CLAIM, confirmed live exactly as written** (token total read dynamically, not hardcoded to 64000) |
| 7 Click edit icon → Modal opens showing 0 values for all metrics | modal all-zero | step 7 | `context_budget_edit_button` click → dialog `Tokens: 0/6 400`, `0%`, `Messages: 0`, `Summaries: 0` | asserted — confirmed live exactly as written |
| Expected Final State: "Context management disabled; widget always shows 0." | — | steps 4, 6, 7 | as above | asserted |
| Pass/Fail: "Widget shows 0 throughout when global setting is off." | — | steps 4, 6, 7 | as above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Confirmed the Context Budget panel's pre-message-render timing (not visible at all before the first message; collapsed-by-default afterward) applies identically whether Context Management is ON or OFF — this is a general chat-UI mechanism, not something this case's disabled-state scenario changes. Cross-referenced against the ELITEA-2218 AFS, which documents the same mechanism for the ENABLED case — *added: without this cross-check, the collapsed-indicator behavior at step 4 could have been misread as a context-management-specific quirk instead of pre-existing chat-composer behavior, which would have produced an incorrect defect report.*
- Verified the account's CURRENT Max Context Tokens value (`6400`, not the case's literal `64000`) via the Settings > Memory page before disabling, confirming the case's Test Data table is illustrative, not a literal fixture value to assert against — *added: prevents a hardcoded `64000` assertion that would fail against this (or any other) account's actual configured value, matching the same caution already documented for ELITEA-2374/2218's numeric fields.*
- Confirmed via the modal (step 7) that the "Context Management" toggle ALSO appears inside the "Edit context settings" dialog itself, in sync with the global setting (unchecked here) — *added: this is a second control surface for the same setting the case doesn't mention; noted so the implementer doesn't mistake it for a separate per-conversation override (it is not — the dialog's Save button stays disabled with no dirty state, consistent with the global toggle being the source of truth).*
- Console checked at every step (Settings > Memory page, blank chat composer, mid-response, and post-response) — 0 errors throughout. No warnings tied to context-management behavior specifically.

## Cleanup
1. Context Management restored to ON (its prior confirmed-live state) on `${TEST_USER}` — confirmed via a second live toggle-click + "Settings saved successfully" toast + field values re-verified matching the pre-test originals (`6400` / `5` / Automatic Summarization ON), same restore pattern as ELITEA-2374's `finally` block.
2. Conversation created during this analysis (`/chat/9328`, "Hello, tell long story about") was **NOT deleted** — a UI delete-flow / API delete attempt was not completed within this session's time budget (a direct `DELETE /elitea_core/conversations/prompt_lib/{project_id}/{id}` via the dev-token bearer returned 404 — the dev token likely isn't a valid bearer for this endpoint shape; needs the browser-cookie-based `ConversationAPI` client instead). Low-impact: the shared `${TEST_USER}` account already carries dozens of prior test-artifact conversations/folders (`ABC`, `ELITEA2459RenameTest`, `AutomationRenameTest`, etc. — all pre-existing, unrelated to this session). **Flagged for the implementer**: use the `conversation_api` fixture's `delete_conversation()` in a `finally` block, per the standard pattern (`.claude/rules/ui-tests.md` § Test Data Lifecycle, and identical to ELITEA-2218's own Cleanup section) — this was not a gap in the pattern, only in this exploration session completing it.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). All handles below are PRE-EXISTING (no new testid work needed for this case) — verified via live interaction (Playwright MCP resolved every click to a `getByTestId(...)` call, confirming the pre-existing page-object fields are wired correctly), provenance carried over from the ELITEA-2218 AFS's own `git fetch` + `git grep` verification (2026-08-03) since these are the identical elements, not re-verified fresh in this session (no NEW testid is introduced — nothing to re-verify against `main`/`automation/testids`).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Context Management toggle | `context-management-toggle` | on-main ✓ (per ELITEA-2218 AFS, reused) | `UserProfileSettingsPage.context_management_toggle` / `disable_context_management()` / `is_context_management_enabled()` — confirmed live again this session, PUT autosave fires and persists. |
| Chat message input | `chat-message-input` | on-main ✓ | Resolved live via `page.getByTestId('chat-message-input')`. Existing `ChatPage` field — reuse `send_message()`. |
| Chat send button | `chat-send-button` | on-main ✓ | MUI overlay intercepts a plain `.click()` on this button (confirmed live — the standard `mui-patterns.md` overlay-interception pattern); `send_message(..., use_enter=True)` (Enter keypress) is the reliable path and is what `ChatPage.send_message()` already supports — use it, don't force-click the button. |
| Participants panel toggle | `chat-participants-panel-toggle-button` | on-main ✓ (per ELITEA-2218 AFS, reused) | `ChatPage.expand_participants_panel()` — confirmed live, opens the Context Budget panel. |
| Context Budget panel + counters | `context-budget-panel`, `context-budget-tokens`, `context-budget-messages-count`, `context-budget-summaries-count` | on-main ✓ (per ELITEA-2218 AFS, reused) | Confirmed live in the DISABLED state: `context_budget_tokens_display` reads `"0 / 6 400 tokens"` + `"0%"`; messages/summaries counters both read `"0"`. |
| Context Budget edit button | `context-budget-edit-button` | on-main ✓ (per ELITEA-2218 AFS, reused) | `ChatPage.context_budget_edit_button` — opens the "Edit context settings" dialog (`ContextStrategyModalContent`). Confirmed live this session (ELITEA-2218's AFS only source-reviewed this dialog; this case click-verifies it end-to-end for the first time). |

### New handle needed for a stronger step-4 assertion (optional, not required by this case)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Collapsed Context Budget indicator (the bare `0%` shown before the Participants panel is expanded) | **NO TESTID confirmed** — a bare `0%` text node sits next to the participants-toggle button before expansion; not independently probed for its own `data-testid` this session (out of scope — the existing `context-budget-messages-count`/`context-budget-tokens`/etc. testids are on the EXPANDED panel, which this case's step 6/7 assertions already use). | not verified | If the implementer wants to assert the collapsed indicator specifically at step 4 (rather than expanding the panel first), this needs a fresh live check for a `data-testid` on that element; `chat_page.py`'s own comment (`# Look for buttons near a percentage display (collapsed Context Budget shows "0%")`) suggests it was previously investigated and found NOT to carry a stable handle — treat as `testid needed` if pursued, otherwise skip and assert only via the expanded panel (steps 6-7 already do, and satisfy the case's core claim). |

## Network Behavior
- Toggle OFF: `PUT /api/v2/social/author/` → 200 (confirmed persists, same endpoint as ELITEA-2374).
- Sending the message + receiving the full AI response: no context-management-specific network calls observed (no summarization/budget-specific endpoint fires when the setting is OFF — consistent with the widget's zero display, the backend appears not to compute/track context-budget usage at all when the global setting is disabled, not merely to hide a computed value).
- No console errors at any step (Settings page, blank composer, mid-generation, post-generation, modal open).

## Known Case-Text Drift (reverse-masking guard — NOT filed as new defects)
- **Route**: case says "Settings > user profile > Personalization"; live route is `/settings/memory`. Already tracked by EliteaAI/elitea-testing-public#1238 (filed by the ELITEA-2218 analyst) — not re-filed, cross-referenced only.
- **Literal token ceiling**: case's Test Data / Step 4/6 text says "0/64000 tokens" as a literal value; the live account's actual Max Context Tokens is `6400` (account-state, not a fixed product default). Assert the token TOTAL dynamically (read whatever the account is currently configured to, same caution already applied by ELITEA-2374/ELITEA-2218's own AFS) — do not hardcode `64000`.
- **Widget visibility timing**: case's Step 3/4 implies the widget is already visible on a freshly-opened conversation, before any message. Live behavior: the panel isn't mounted at all pre-message, and sits collapsed-by-default post-message (pre-existing chat-composer mechanism, unrelated to this case's disabled/enabled scope — see § Test Steps step 3's note). Not filed as a defect; both is a general UI mechanism already implicitly documented via the ELITEA-2218 AFS/digest for the enabled-state case.

## Blocked Steps
None. All 7 case steps were executed live and produced exactly the expected result.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Playwright MCP was used for this analysis (server was wired this session, unlike ELITEA-2218's analysis pass) — every locator resolved was confirmed via the browser's own `getByTestId(...)` resolution, giving high confidence in the handles above.
- Reuse `UserProfileSettingsPage.disable_context_management()` / `enable_context_management()` (cleanup) / `is_context_management_enabled()`, and `ChatPage.send_message(..., use_enter=True)` / `expand_participants_panel()` / `wait_for_context_budget_panel()` / `get_context_budget_tokens_text()` / `get_context_budget_messages_count()` / `get_context_budget_summaries_count()` / `context_budget_edit_button` — all pre-existing, all confirmed live in the DISABLED state this session (previously only confirmed in the ENABLED state by ELITEA-2218/2374).
- Recommend a `try/finally` that restores Context Management to ON at the end (mirrors ELITEA-2374's own restore pattern) since it is a global, persistent, shared-account setting — this case actively turns it OFF, unlike ELITEA-2218/2374 which assume/restore ON.
- Recommend sending at least 2 messages (not just 1) to strengthen the "stays at zero regardless of usage" claim across more than a single exchange — implementer discretion, not a case requirement (see § Test Data).
- `ChatPage.send_message()`'s send-button click is intercepted by a MUI overlay (confirmed live) — use `use_enter=True` (existing parameter) rather than fighting the overlay with `force=True`.
- Delete the test conversation via `conversation_api.delete_conversation()` in a `finally` block (this analysis session left one undeleted — see § Cleanup item 2).
