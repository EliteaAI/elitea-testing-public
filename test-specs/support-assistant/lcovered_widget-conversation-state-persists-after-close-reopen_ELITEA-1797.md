# Test Case: Widget conversation state persists after close and reopen

## Metadata
- **TMS ID**: ELITEA-1797
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/ (to be linked during intake)
- **Priority**: l2 (high priority → P1 marker)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token)
- **Analyst**: qa-engineer (Sage)
- **Status**: already-covered

## Covering Spec

**File**: `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`  
**Test**: `TestSupportAssistantLauncher.test_widget_state_persists_after_close_reopen` (lines 89-127)  
**Merged to**: `automation/base` (initial commit — pre-pipeline)

## Behavioural Equivalence Argument

The covering test `test_widget_state_persists_after_close_reopen` executes the exact observable sequence ELITEA-1797 specifies:

| ELITEA-1797 Step | Covering Test Step | Evidence |
|---|---|---|
| 1. Navigate to Chat page | L94-96: `chat_page.navigate_to_chat()` | Navigates to `/chat` |
| 2. Open Support Assistant widget | L98: `support_page.open_widget(timeout=WIDGET_TIMEOUT)` | Opens widget, waits for title visible |
| 3. Record initial assistant message count | L100-103: `support_page.start_new_chat()` + `initial_count = support_page.get_assistant_message_count()` | Captures baseline count |
| 4. Send test message | L105-107: `support_page.send_message("Test message for state persistence")` | Exact message text from TMS case |
| 5. Wait for AI response | L108: `support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)` | Waits up to 60s for assistant response |
| 6. Assert message count increased | L109-112: `count_after_send = support_page.get_assistant_message_count()` + `assert count_after_send > initial_count` | Verifies at least one new assistant message |
| 7. Close widget | L114-115: `support_page.close_widget(timeout=WIDGET_TIMEOUT)` | Closes widget, waits for title hidden |
| 8. Reopen widget | L117-120: `support_page.open_widget(timeout=WIDGET_TIMEOUT)` + `support_page.wait_for_widget_ready()` + `page.wait_for_timeout(2000)` | Reopens widget and waits for messages to load |
| 9. Assert messages persist | L122-126: `count_after_reopen = support_page.get_assistant_message_count()` + `assert count_after_reopen >= count_after_send` | Verifies conversation state retained after close/reopen |

**Observable match**: The case asserts "assistant response messages that were present before closing the widget are still visible when reopened" (TMS L56-58). The test asserts the exact same: message count after reopen ≥ count after sending (L123-126), which directly proves the assistant messages persisted.

**Method coverage**:
- Message count: `SupportAssistantPage.get_assistant_message_count()` (L328-350) — counts `.elitea-assistant-message-wrapper--assistant` elements, the stable container for all assistant messages including those still streaming
- Widget state: `open_widget()` / `close_widget()` (L161-191) — JS-click launcher workaround for MUI overlay interception, waits for title visible/hidden
- Response wait: `wait_for_response()` (L223-302) — progressive timeout strategy resets on each status change ("sending" → "thinking" → "receiving text"), handles slow AI responses

## Preconditions
- User is authenticated (on localhost satisfied automatically by `VITE_DEV_TOKEN`; `page` fixture pre-loads `auth_state` on other environments)
- Support Assistant feature is enabled — confirmed live: launcher renders unconditionally on `/chat`

## Test Data
### reuse-existing
- `${BASE_URL}` = `http://localhost:5173` (or project's configured `APP_PREFIX`-aware base URL)
- Page under test: `/chat`
- Test message: `"Test message for state persistence"` (exact text from TMS case, also used in covering test L106)

## Expected Results
- Assistant response messages present before closing the widget are still visible when the widget is reopened (conversation not reset by widget toggle)
- Message count after reopen ≥ message count after sending

## Coverage Map

**Axis 1 — Case coverage** (ELITEA-1797 steps 1-10, mapped to covering test):

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to `/chat` | Page loads successfully | L94-96 | `chat_page.navigate_to_chat()` | already-covered |
| 2 Open Support Assistant widget | Widget panel opens; title visible | L98 | `support_page.open_widget(timeout=WIDGET_TIMEOUT)` — waits for `widget_title` visible (L176) | already-covered |
| 3 Record initial assistant message count | Baseline count captured | L100-103 | `support_page.start_new_chat()` + `initial_count = support_page.get_assistant_message_count()` | already-covered |
| 4 Send message | Message submitted; Send button clicked | L105-107 | `support_page.send_message("Test message for state persistence")` | already-covered |
| 5 Wait for AI response | At least one new "Copy to clipboard" button appears | L108 | `support_page.wait_for_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)` — progressive timeout, waits for completion signal | already-covered |
| 6 Assert new assistant message appeared | `get_assistant_message_count()` > initial count | L109-112 | `count_after_send = support_page.get_assistant_message_count()` + `assert count_after_send > initial_count` | already-covered |
| 7 Close widget | Widget panel dismissed; title hidden | L114-115 | `support_page.close_widget(timeout=WIDGET_TIMEOUT)` — waits for `widget_title` hidden (L190) | already-covered |
| 8 Reopen widget | Widget panel reopens; title visible | L117-120 | `support_page.open_widget()` + `support_page.wait_for_widget_ready()` + 2s settle | already-covered |
| 9 Wait for widget ready | Widget ready; messages rendered | L119-120 | `support_page.wait_for_widget_ready(timeout=WIDGET_TIMEOUT)` + `page.wait_for_timeout(2000)` — title + input visible, 2s for messages to load | already-covered |
| 10 Assert message count persists | `get_assistant_message_count()` ≥ count after sending | L122-126 | `count_after_reopen = support_page.get_assistant_message_count()` + `assert count_after_reopen >= count_after_send` | already-covered |

**Axis 2 — Analyst additions**: None. The covering test already asserts every observable the TMS case specifies; no additional verification was required during this exploration.

## Cleanup
None required — covering test performs same cleanup pattern (no explicit cleanup shown in the test excerpt, consistent with ephemeral widget state that resets on page navigation).

## Concrete Handles (from covering test + page object)

| Element | Live Handle (from page object) | Notes |
|---|---|---|
| Launcher button | JS-evaluate click on `button.elitea-assistant-button, button[aria-label="Support Assistant"]` (L170-173) | MUI overlay intercepts native `.click()` — workaround confirmed working |
| Widget title (open indicator) | `.elitea-assistant-header-title` (L74-77) | Visibility indicates widget open/closed state |
| Message input | `textbox[placeholder*="Type a message"]` or `getByPlaceholder("Type a message...")` (L204-206) | Fallback chain in `send_message()` |
| Send button | `button[aria-label="Send message"]` (L211) | Waits for `!btn.disabled` before clicking (L212-218) |
| Assistant message wrappers | `.elitea-assistant-message-wrapper--assistant` (L340) | Stable container for counting assistant messages, present even during streaming |
| Close button | `LocatorDescriptor` fallback `button[aria-label="Close chat"], button:has-text("Close chat")` (L50-52) | Native click works (no overlay workaround needed) |

**Testid status** (checked against live DOM, 2026-08-18): None of the Support Assistant elements have `data-testid` attributes — page object relies entirely on fallback selectors (aria-label, placeholder, CSS classes). This diverges from `.claude/rules/page-objects.md` testid-only mandate but is pre-existing framework-conformance debt flagged in ELITEA-1796 AFS (L207-213), not blocking this coverage determination.

## Network Behavior
- Open/close widget: pure client-side UI state toggle, no network calls
- Send message + wait for response: WebSocket connection to DEV backend, AI response arrives ~2-30s after send (handled by `wait_for_response()` progressive timeout strategy)

## Known Defects Found During Exploration
None. The covering test already runs green and the TMS case's Test Data table (L30-35) cites selectors (`textbox[placeholder*="Type a message"]`, `button[aria-label="Copy to clipboard"]`) that match the page object's actual implementation, so no case-text drift is present.

## Blocked Steps
None.

## Traceability Notes

**Covering test's own TMS link**: The test at L88 carries `@allure.issue` pointing to **ELITEA-0643** (`conversation-is-retained-when-the-support-assistant-panel-is-closed-an.md`), a legacy onetest case from the `elitea-platform/elitea-chat-bot/` folder. ELITEA-0643 and ELITEA-1797 are **behaviorally identical** — both assert that conversation state persists across widget close/reopen cycles — so the same test correctly covers both.

**Why this is `already-covered` rather than `extend-existing`**: The test proves the exact same observable ELITEA-1797 asks for (message persistence after widget toggle), and the test already exists on `automation/base` (part of the initial commit, pre-pipeline). Adding a second `@allure.issue` decorator for ELITEA-1797 would document the traceability link but would not change the test's behavior or add any new verification — the functional coverage is complete. Per `test-case-analysis` § Classify findings, `already-covered` applies when "the observable this case asserts is already proven by another spec on file" — satisfied here.

**TMS back-write correction** (orchestrator, post-analysis): ELITEA-1797's frontmatter (checked via the case read above) declares:
- `execution_type: manual`
- `status: draft`
- `automation_test_id:` (empty)

Once this `already-covered` determination is accepted, back-write:
- `execution_type: automated`
- `status: ready`
- `automation_test_id: tests.ui.support_assistant.test_support_assistant_smoke.TestSupportAssistantLauncher.test_widget_state_persists_after_close_reopen` (Form C per `.agents/test-automation.yaml` § backwrite_on_done)

## Automation Hints

**No code change required.** The covering test exists, runs green, and proves the observable. The implementer's action for this AFS is **null** — ELITEA-1797 traceability is satisfied by the existing test's coverage of ELITEA-0643 (behaviorally identical cases).

**Optional traceability enhancement** (not required for coverage): If the project wants explicit ELITEA-1797 linkage in Allure reports, the implementer could append a second `@allure.issue` decorator to the test (same pattern as ELITEA-1796's gap-assertion requirement in the `lextend_launcher-visible-widget-opens-and-closes_ELITEA-1796.md` AFS). However, this is a **documentation-only change** — it does not add any new verification, so classifying as `extend-existing` would misrepresent the work (the functional coverage is already complete). Recommendation: leave as `already-covered` and document the ELITEA-0643 ↔ ELITEA-1797 behavioral equivalence in the TMS case's notes field if traceability needs to be explicit.
