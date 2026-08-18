---
id: ELITEA-2423
title: History loads correctly after page refresh
priority: medium
status: defect-found
source: onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2423_history-loads-correctly-after-page-refresh.md
analyst_session: 2026-08-18
---

# ELITEA-2423: History loads correctly after page refresh

**Module:** support-assistant · **Priority:** medium · **Type:** functional  
**Status:** defect-found  
**Blocking defect:** #1581 (duplicate of ELITEA-2418)

---

## Objective

Verify that the Support Assistant History panel loads correctly after page refresh, including after repeat message-send + refresh cycles. Success confirmed when history loads without errors (HTTP 200 on GET /api/v2/support_assistant/conversations/) and previous sessions can be opened.

---

## Preconditions

- User is logged in to the Elitea platform at `http://localhost:5173`
- Support Assistant feature is enabled (launcher visible)

---

## Known Defects

### Blocking Defect — Cannot Send Messages

**Issue:** #1581 — "[BUG][ELITEA-2418] Support Assistant send button never enables when typing actual text"

**Status:** OPEN (filed 2026-08-18, confirmed again 2026-08-18 during ELITEA-2423 analysis)

**Impact:** Critical — blocks execution at Step 1. Cannot send any message through the Support Assistant widget because the Send button remains permanently disabled even after typing text.

**Observed behavior:**
- Support Assistant widget opens successfully
- Message textarea accepts text (value updates in DOM: "Test message for history", 24 characters)
- Send button remains `disabled="true"` regardless of input content
- Multiple React event triggers attempted (input, change, InputEvent) — all fail to enable the button
- Neither Enter key nor clicking the disabled button sends the message

**Reproduction confirmed:** 100% reproducible on `localhost:5173` (EliteaUI `automation/testids`, DEV backend)

**Evidence:** `automation/test-results/screenshots/ELITEA-2423-step-01-send-button-state.png`

**This prevents testing:**
- Step 1: Send message and wait for response
- Step 2-6: All refresh + history verification steps (no conversation created, so no history to load)

---

## Blocked Steps

| Step | Reason | What was attempted |
|---|---|---|
| 1 | Send button disabled | Typed "Test message for history" (24 chars) via JS — button never enabled. Events dispatched: `input`, `change`, `InputEvent`. Value confirmed in DOM. |
| 2-6 | Depends on Step 1 | Cannot refresh and verify history loading without an initial message to create a conversation |

---

## Execution Log (Partial — Stopped at Step 1)

### Step 0 — Open Support Assistant widget ✓

**Action:** Navigate to Chat page, click Support Assistant launcher button

**Observed:**
- Chat page loaded: `http://localhost:5173/chat`
- Support Assistant launcher visible (bottom-right corner area)
- Clicked launcher via JavaScript (`el.click()`) due to known MUI overlay quirk
- Widget opened successfully
- Widget title: "Elitea Assistant" (heading level 2)
- Initial greeting message visible: "Hi! I'm your ELITEA Support Assistant..."
- Message textarea visible: `textbox "Type a message..."` (active, ref=f2e297)
- Send button visible but disabled: `button "Send message" [disabled]` (ref=f2e298)
- **Chat history button: DISABLED** (ref=f2e277) — expected when no conversation exists yet
- Close chat button, New chat button, Attach file button, Expand chat button all present

**Result:** PASS — Widget opened successfully ✓

---

### Step 1 — Send message and wait for response ✗ BLOCKED

**Action:** Type "Test message for history" into Support Assistant textarea and send

**Attempted:**
1. Located textarea via `document.querySelectorAll('textarea')` with placeholder "Type a message..."
2. Set value programmatically: `textarea.value = 'Test message for history'`
3. Dispatched React-compatible events:
   - `Event('input', { bubbles: true })`
   - `Event('change', { bubbles: true })`
   - `InputEvent('input', { bubbles: true, inputType: 'insertText' })`
4. Verified value in DOM

**Observed:**
- Textarea value: "Test message for history" (length: 24, trimmed: "Test message for history")
- **Send button state: `disabled=true` (never changed)**
- Send button exists: true (ref=f2e298, aria-label="Send message")
- No network requests fired
- No error messages in console (0 errors, 1 warning unrelated)
- Accessibility snapshot shows: `textbox "Type a message..." [active]: Test message for history` — value IS in DOM
- Accessibility snapshot shows: `button "Send message" [disabled]` — button remains disabled

**Result:** FAIL — Cannot complete due to blocking defect #1581

**Root cause:** React state not updating when textarea value changes programmatically. The `disabled` prop on the Send button is controlled by component state that never reflects the textarea's actual value, regardless of how the value is set or which events are dispatched.

---

## Steps Not Executed

| # | Step | Reason |
|---|---|---|
| 2 | Refresh the browser page (F5) | Blocked by Step 1 failure — no conversation to persist |
| 3 | After page reload, open Support Assistant widget | Blocked by Step 1 failure |
| 4 | Open History panel, verify GET /api/v2/support_assistant/conversations/ returns HTTP 200 | Blocked by Step 1 failure — no history to load |
| 5 | Verify previous session is listed and can be opened | Blocked by Step 1 failure |
| 6 | Repeat: send another message, refresh again, verify history loads | Blocked by Step 1 failure |

---

## Handles Reference

### Support Assistant Widget Elements

| Element | Handle | Provenance | Type | Notes |
|---|---|---|---|---|
| Support Assistant launcher button | testid needed: `support-assistant-launcher` | needs-adding | button | Requires JS click due to MUI overlay |
| Widget container | testid needed: `support-assistant-widget` | needs-adding | dialog/panel | |
| Widget title | Contains text "Elitea Assistant" | N/A | heading[level=2] | |
| Close chat button | `aria-label="Close chat"` | live | button | ref=f2e266 |
| New chat button | `aria-label="New chat"` | live | button | ref=f2e272 |
| **Chat history button** | `aria-label` pattern TBD | live | button | **ref=f2e277, DISABLED when no conversations exist** |
| Expand chat button | `aria-label="Expand chat"` | live | button | ref=f2e281 |
| Message textarea | `placeholder="Type a message..."` | live | textbox | ref=f2e297 — testid needed: `support-assistant-message-input` |
| Send button | `aria-label="Send message"` | live | button | ref=f2e298 — testid needed: `support-assistant-send-button` |
| Attach file button | `aria-label="Attach file"` | live | button | ref=f2e294 |

**Key observation:** Chat history button is DISABLED when the widget first opens (no conversation exists yet). This is expected behavior and not a defect — the button should enable only after at least one message is sent and a conversation is created.

**Note:** All `needs-adding` testids should be added to `elitea_assistant` repo on its `automation/testids` branch (connected repo, consumed by EliteaUI as `@eliteaai/elitea-assistant`).

---

## Network Behavior (Widget Open Only)

No Support Assistant conversation-related requests fired during Steps 0-1 (widget open + attempted message send):
- No POST to `/support_assistant/conversations/` (message never sent due to disabled button)
- No GET to `/support_assistant/conversations/` (History panel never opened — button was disabled)

Expected network flow (if Step 1 were unblocked):
1. POST `/api/v2/support_assistant/conversations/` → create conversation
2. WebSocket connection for AI response streaming
3. GET `/api/v2/support_assistant/conversations/` → load history (Step 4)

---

## Coverage Map

### Axis 1 — TMS Case Elements

| Case Element | Expected Result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| **Precondition:** User logged in | N/A (setup) | Auth fixture | N/A | ✓ satisfied |
| **Precondition:** Support Assistant feature enabled | Launcher visible | Step 0 | Widget opens | ✓ satisfied |
| **Step 1:** Open widget and send message, wait for response | Message sent, AI responds | Step 0-1 attempt | — | ✗ BLOCKED (#1581) |
| **Step 2:** Refresh browser page (F5) | Page reloads without error | — | — | ○ not executed |
| **Step 3:** After reload, open Support Assistant widget | Widget opens | — | — | ○ not executed |
| **Step 4:** Open History panel, verify GET returns HTTP 200 | API returns 200, not 500 | — | Network monitor | ○ not executed |
| **Step 5:** Verify previous session listed and openable | History shows conversation, clickable | — | — | ○ not executed |
| **Step 6:** Repeat: send message, refresh, verify history loads | No errors on repeat cycle | — | — | ○ not executed |
| **Pass criteria:** History loads correctly after refresh | Verified across multiple refresh cycles | — | — | ○ not executed |

### Axis 2 — Beyond-Case Observations

| Observable | Why asserted | Provenance |
|---|---|---|
| Chat history button disabled when no conversations exist | Correct UX — button should only enable after first conversation created | Discovered during Step 0, ref=f2e277 |

---

## Classification

**Status:** `defect-found`

**Reason:** Identical blocking defect to ELITEA-2422 (#1581). Cannot send any messages via the Support Assistant, which is a prerequisite for creating conversation history to test. The defect prevents testing the entire History-after-refresh flow.

---

## Fidelity Declaration

None — case execution blocked before any fidelity decisions were required.

---

## Next Steps

1. **Wait for #1581 fix** — defect must be resolved before this case can be automated
2. **Reanalyze after fix** — re-execute full case flow once messages can be sent
3. **Expected post-fix analysis findings:**
   - Capture network flow: POST conversation, GET conversations
   - Verify HTTP 200 vs 500 distinction
   - Test persistence across multiple refresh cycles
   - Verify history panel UI behavior (empty vs populated states)
   - Add testids for History-panel-specific elements (not yet visible in current blocked state)
