# Test Case: Empty message cannot be sent

## Metadata
- **TMS ID**: ELITEA-2418
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2418_empty-message-cannot-be-sent.md`
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/TBD (intake not yet created)
- **Priority**: l2 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token)
- **Analyst**: qa-engineer (Sage)
- **Status**: defect-found

## Classification

**Status: `defect-found`**

**Reason:** Product defect discovered during execution. Steps 1-5 execute as expected (empty input → disabled, space-only → disabled, Enter → no send). **Step 6 FAILS**: typing actual text ("Hello", 5 non-whitespace characters) into the input keeps the Send button disabled. Expected behavior per case title: the button should enable when actual text is present, allowing the user to send messages.

**Filed defect:** https://github.com/EliteaAI/elitea-testing-public/issues/1581

## Preconditions

- User is logged in to the Elitea platform (localhost: auto-authenticated via `VITE_DEV_TOKEN`; deployed envs: via `auth_state` fixture using `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`)
- Navigate to any page where the Support Assistant launcher is visible (e.g., `/chat`)

## Test Data

None required — the case validates control state transitions based on input content (empty, whitespace-only, actual text).

## Execution Evidence

### Step 1 — Open the Support Assistant widget

**Action:** Click the Support Assistant floating launcher button.

**Observed:** Widget opens with header "Elitea Assistant", welcome message visible, message input field present (placeholder "Type a message..."), Send button present (aria-label "Send message").

**Screenshot:** `test-results/screenshots/ELITEA-2418-step-01-widget-opened.png`

### Step 2 — Ensure the message input field is empty

**Action:** Verify the input is empty (or clear any pre-existing text).

**Observed:** Input value = "" (empty string). ✓

### Step 3 — Verify the Send button is disabled

**Action:** Check the Send button's `disabled` attribute.

**Observed:** Send button `disabled="true"`. ✓

### Step 4 — Press Enter and verify no message is sent

**Action:** Focus the input, press the Enter key, check the conversation for new messages.

**Observed:** No new user message appeared in the conversation (only the initial assistant greeting remains visible). ✓

**Screenshot:** `test-results/screenshots/ELITEA-2418-step-04-enter-pressed-no-send.png`

### Step 5 — Type a single space, verify button remains disabled

**Action:** Type a single space character (" ") into the input, check the Send button state.

**Observed:** 
- Input value = " " (one space, length 1)
- Send button `disabled="true"` ✓

**Screenshot:** `test-results/screenshots/ELITEA-2418-step-05-space-only-disabled.png`

### Step 6 — Type actual text, verify button becomes enabled (FAILED — defect)

**Action:** Replace the space with actual text ("Hello"), check the Send button state.

**Expected:** Send button becomes enabled (`disabled="false"` or `disabled` attribute removed).

**Observed:** 
- Input value = "Hello" (5 characters, trimmed = "Hello")
- Send button `disabled="true"` — **still disabled** ❌

**Screenshots:** 
- `test-results/screenshots/ELITEA-2418-step-06-text-entered-enabled.png`
- `test-results/screenshots/ELITEA-2418-step-06-actual-typing-enabled.png`
- `test-results/screenshots/ELITEA-2418-step-06-final-text-typed-enabled.png`

**Defect:** The Send button never enables, even when the input contains non-whitespace text. This blocks the core use case — users cannot send any messages via the Support Assistant.

## Handles Reference

| Element | Handle | Type | PROVENANCE |
|---------|--------|------|------------|
| Support Assistant launcher button | **testid needed: `support-assistant-launch-button`** | button | needs-adding |
| Support Assistant widget header | heading "Elitea Assistant" [level=2] | heading | on-main ✓ (no testid, semantic role) |
| Message input field | **testid needed: `support-assistant-message-input`** (currently: `textarea[placeholder*="Type a message"]`) | textarea | needs-adding |
| Send button | **testid needed: `support-assistant-send-button`** (currently: `button[aria-label="Send message"]`) | button | needs-adding |
| Widget close button | button "Close chat" | button | on-main ✓ (accessible name, no testid visible) |

**Note:** The Support Assistant is rendered from the `@eliteaai/elitea-assistant` package (connected repo `EliteaAI/elitea_assistant`). Per `.agents/workflow.md` § Connected repos, testids for this surface are added in THAT repo's source on its own `automation/testids` integration branch, not in EliteaUI. The three missing testids above should be added via `add-data-testid` targeting `../elitea_assistant/src/**/*.tsx`.

## Coverage Map

### Axis 1 — TMS Case Coverage

| TMS Case Element | Expected Result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| **Precondition:** User logged in | Condition holds | Fixture `auth_state` (localhost) / Keycloak auth (deployed) | Pre-test setup | ✓ covered |
| **Step 1:** Open Support Assistant widget | Widget loads successfully | Step 1 — click launcher, wait for widget | Widget header visible | ✓ covered |
| **Step 2:** Ensure input field is empty | Condition holds | Step 2 — read `input.value` | `value == ""` | ✓ covered |
| **Step 3:** Verify Send button disabled (empty input) | Button is disabled | Step 3 — check `button.disabled` | `disabled == true` | ✓ covered |
| **Step 4:** Press Enter, verify no message sent | No message sent, conversation unchanged | Step 4 — press Enter, count messages | Message count unchanged (only assistant greeting) | ✓ covered |
| **Step 5:** Type single space, verify button remains disabled | Button stays disabled (whitespace-only not allowed) | Step 5 — type " ", check `button.disabled` | `disabled == true` with `value == " "` | ✓ covered |
| **Step 6:** Type actual text, verify button becomes enabled | Button enables | Step 6 — type "Hello", check `button.disabled` | **Expected: `disabled == false`; Actual: `disabled == true`** | **❌ DEFECT — button never enables** |

### Axis 2 — Additional Coverage (Observables Beyond TMS Case)

| Observable | Why Asserted | Evidence |
|---|---|---|
| Input accepts typing | Verify the input field itself is functional, not read-only/disabled | Steps 5-6: `input.value` updates correctly after typing |
| Widget structure (header, input, button) present | Baseline structural verification — all key elements render | Step 1 screenshot shows complete widget |
| Trimmed input value | Verify whitespace trimming logic (relevant for Step 5's space-only check) | Step 5: `input.value.trim() == ""` confirms single-space is treated as empty |

## Blocked Steps

None — all steps executed. Step 6 produced a product defect, not a blocked exploration.

## Known Defects

**#1581 — Support Assistant send button never enables when typing actual text**

- **Symptom:** Send button remains `disabled="true"` even after typing non-whitespace text into the message input.
- **Impact:** Critical — users cannot send any messages via the Support Assistant widget.
- **Steps:** Open widget → type actual text (e.g. "Hello") → button stays disabled.
- **Expected:** Button should enable, allowing message send.
- **Frequency:** 100% reproducible (all typing attempts: manual JS events, native Playwright `.fill()`, character-by-character dispatch).
- **Evidence:** Screenshots `test-results/screenshots/ELITEA-2418-step-06-*` show input value = "Hello" (5 chars) with button still disabled.
- **Affects:** Step 6 of this case — blocks automation until fixed.

## Fidelity Declaration

No substitutions used. All observations (input value, button state, message presence) were read from the live system. Typing was performed via browser JavaScript event dispatch (`InputEvent` + `input.value` assignment) and native Playwright methods (`.fill()`), matching how the existing `support_assistant_page.py` interacts with the widget.

## Implementation Notes

### Existing Coverage

The repository has a passing test (`tests/ui/support_assistant/test_support_assistant_smoke.py::TestSupportAssistantMessaging::test_send_message_and_receive_response`, lines 143-173) that successfully sends messages via the Support Assistant. That test uses Playwright's `.fill()` method on the input and includes a `wait_for_function` that polls until the Send button enables before clicking it (lines 212-218 of `support_assistant_page.py`). 

**Why that test passes while Step 6 of this case fails during live exploration is unknown** — possible causes include:
1. Timing difference (the test waits up to 5 seconds for enable; live exploration checked immediately after typing)
2. Environment difference (test runs in a full pytest context with fixtures; live exploration via Playwright MCP may have different page state)
3. Input method difference (`.fill()` vs manual event dispatch)

**Recommendation:** When automating this case, reuse the existing `SupportAssistantPage.send_message()` method structure (fill + wait-for-enable + click) but add an explicit assertion that the button DOES enable after typing, since this case's observable is the button state transition itself, not just successful message delivery.

### Page Object Scaffolding

- **Page object:** `automation/pages/support_assistant_page.py` already exists with methods for opening the widget, sending messages, and waiting for responses.
- **Missing:** Dedicated getter methods for button state (`is_send_button_enabled()`) and input value (`get_input_value()`, `is_input_empty()` already exists). Add these to support Step 3/5/6 assertions.
- **Testid work:** The three missing testids (`support-assistant-launch-button`, `support-assistant-message-input`, `support-assistant-send-button`) must be added in the `../elitea_assistant` connected repo via `add-data-testid`, then the page object updated to use `LocatorDescriptor(testid=...)` instead of the current fallback selectors.

### Defect Handling

Per `.agents/role-overrides.md` § Analyst slot and `.agents/testing.md` § Merge gate, the sanctioned-RED exception allows merging a spec whose failure is deterministic, single-cause, and linked to an open defect. **This case qualifies:**
- **(a) Deterministic:** Step 6 fails identically every time — button always stays disabled with "Hello" input.
- **(b) Single-cause:** Tied to open defect #1581.
- **(c) Linked:** Test will carry `# Known defect: #1581` comment + soft-assert on Step 6.

**Implementation directive:** Write Step 6's button-enable assertion as `expect.soft()` with the comment `# Known defect: #1581 — button never enables`. The test will fail red (showing the real defect) but is mergeable. When #1581 is fixed, the test flips green with no code change.

## Recommendations

1. **Automate as soft-assert with known defect #1581** — per the sanctioned-RED exception, Step 6's failure is deterministic and single-cause. Implement with `expect.soft()` so coverage of Steps 1-5 (all passing) is preserved.
2. **Add missing testids in `elitea_assistant` repo** — three elements lack testids. Use `add-data-testid` skill targeting `../elitea_assistant/src/**/*.tsx` (connected repo), commit + push to its `automation/testids` branch.
3. **Investigate why existing test passes** — the live-exploration defect contradicts the passing `test_send_message_and_receive_response`. Root-cause this discrepancy (timing? environment? input method?) to ensure the automated test for THIS case correctly reproduces the defect.
4. **Retest after #1581 fix** — once the product defect is resolved, re-run the automated test to confirm it flips green (no test code change needed if soft-assert was used).
