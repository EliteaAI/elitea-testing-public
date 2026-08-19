---
id: ELITEA-2422
title: Widget state preserved after in-app navigation
priority: medium
status: defect-found
source: onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2422_widget-state-preserved-after-in-app-navigation.md
analyst_session: 2026-08-18
---

# ELITEA-2422: Widget state preserved after in-app navigation

**Module:** support-assistant · **Priority:** medium · **Type:** functional  
**Status:** defect-found  
**Blocking defect:** #1581 (duplicate of ELITEA-2418)

---

## Objective

Verify that the Support Assistant widget preserves conversation state when navigating between pages in the Elitea application. Success confirmed when a follow-up message can be sent after navigation and the assistant responds in the same session.

---

## Preconditions

- User is logged in to the Elitea platform at `http://localhost:5173`
- Support Assistant feature is enabled (launcher visible)

---

## Known Defects

### Blocking Defect — Cannot Send Messages

**Issue:** #1581 — "[BUG][ELITEA-2418] Support Assistant send button never enables when typing actual text"

**Status:** OPEN (filed 2026-08-18)

**Impact:** Critical — blocks execution at Step 2. Cannot send any message through the Support Assistant widget because the Send button remains permanently disabled even after typing text.

**Observed behavior:**
- Support Assistant widget opens successfully
- Message input field accepts text (value updates in DOM)
- Send button remains `disabled="true"` regardless of input content
- Neither Enter key nor clicking the disabled button sends the message
- Multiple React event triggers attempted (input, change, keydown) — all fail to enable the button

**Reproduction confirmed:** 100% reproducible on `localhost:5173` (EliteaUI `automation/testids`, DEV backend)

**Evidence:** `automation/test-results/screenshots/ELITEA-2422-defect-send-button-disabled.png`

**This prevents testing:**
- Step 2: Send message
- Step 4-7: All navigation/state-preservation steps (no initial message to verify persistence)

---

## Blocked Steps

| Step | Reason | What was attempted |
|---|---|---|
| 2 | Send button disabled | Typed "Navigation persistence test" — button never enabled. Tried: direct value setting, InputEvent dispatch, character-by-character typing, Enter key press. |
| 3-7 | Depends on Step 2 | Cannot navigate and verify state without an initial message to track |

---

## Execution Log (Partial — Stopped at Step 2)

### Step 1 — Open the Support Assistant widget on the Chat page ✓

**Action:** Navigate to Chat page, click Support Assistant launcher button (bottom-left)

**Observed:**
- Chat page loaded: `http://localhost:5173/chat`
- Support Assistant launcher visible at `[box=20,943,28,28]`
- Clicked launcher via JavaScript (`el.click()`) due to known MUI overlay quirk
- Widget opened successfully at `[box=66,491,460,480]`
- Widget title: "Elitea Assistant"
- Initial greeting message visible: "Hi! I'm your ELITEA Support Assistant..."
- Message input field visible: `textbox "Type a message..."` at `[box=115,924,362,34]`
- Send button visible but disabled: `button "Send message" [disabled]` at `[box=485,927,28,28]`

**Result:** PASS — Target page/section loaded successfully ✓

---

### Step 2 — Send the message "Navigation persistence test" and wait for a response ✗ BLOCKED

**Action:** Type message into Support Assistant input and send

**Attempted:**
1. JavaScript value setting + React event dispatch (input, change)
2. Character-by-character typing with InputEvent for each character
3. Enter key press (KeyboardEvent with key='Enter', keyCode=13)
4. Verified input value in DOM: "Navigation persistence test" (28 characters, non-whitespace)

**Observed:**
- Input field value updated correctly in DOM
- Send button state: `disabled="true"` (never changed)
- No network requests fired
- No error messages in console (0 errors, 1 warning unrelated)

**Result:** FAIL — Cannot complete due to blocking defect #1581

**Root cause:** React state not updating when input value changes. The `disabled` prop on the Send button is controlled by component state that never reflects the input's actual value, regardless of how the value is set.

---

## Steps Not Executed

| # | Step | Reason |
|---|---|---|
| 3 | Navigate to Agents page (widget still open) | Blocked by Step 2 failure |
| 4 | Verify widget still open with conversation intact | Blocked by Step 2 failure |
| 5 | Navigate back to Chat page | Blocked by Step 2 failure |
| 6 | Verify widget shows previous session messages | Blocked by Step 2 failure |
| 7 | Send follow-up message | Blocked by Step 2 failure |

---

## Handles Reference

### Support Assistant Widget Elements

| Element | Handle | Provenance | Type | Notes |
|---|---|---|---|---|
| Support Assistant launcher button | testid needed: `support-assistant-launcher` | needs-adding | button | Currently at `[box=20,943,28,28]`, requires JS click due to MUI overlay |
| Widget container | testid needed: `support-assistant-widget` | needs-adding | dialog/panel | Currently at `[box=66,491,460,480]` |
| Widget title | Contains text "Elitea Assistant" | N/A | heading[level=2] | |
| Close chat button | `aria-label="Close chat"` | live | button | At `[box=83,504,28,28]` |
| New chat button | `aria-label="New chat"` | live | button | At `[box=409,504,28,28]` |
| Message input field | `placeholder="Type a message..."` | live | textbox | At `[box=115,924,362,34]` — testid needed: `support-assistant-message-input` |
| Send button | `aria-label="Send message"` | live | button | At `[box=485,927,28,28]` — testid needed: `support-assistant-send-button` |
| Attach file button | `aria-label="Attach file"` | live | button | At `[box=79,927,28,28]` |

### Navigation Elements

| Element | Handle | Provenance | Type |
|---|---|---|---|
| Sidebar "Agents" button | `button "Agents"` | live | button |
| Sidebar "Chats" button | `button "Chats"` | live | button |

**Note:** All `needs-adding` testids should be added to `elitea_assistant` repo on its `automation/testids` branch (connected repo, consumed by EliteaUI as `@eliteaai/elitea-assistant`).

---

## Network Behavior (Step 1 Only)

No Support Assistant-specific requests fired at Step 1 (widget open). Only normal page-load GETs observed:
- `/support_assistant` config
- `/project_info`
- socket.io polling

**Step 2 network behavior:** Not reached — send blocked by disabled button.

---

## Coverage Map

### Axis 1 — TMS Case Elements vs. Coverage

| TMS Case Element | Expected Result | Covered By | Asserted Where | Disposition |
|---|---|---|---|---|
| Precondition: User logged in | User can access application | Implicit | N/A | covered |
| Step 1: Open widget on Chat page | Widget opens successfully | Execution log Step 1 | Widget container visible, title visible | covered ✓ |
| Step 2: Send message "Navigation persistence test" | Message sent, AI responds | — | — | **blocked** (#1581) |
| Step 3: Navigate to Agents page (keep widget open) | Agents page loads, widget remains | — | — | **blocked** (depends on Step 2) |
| Step 4: Verify widget open with conversation intact | Widget shows previous messages | — | — | **blocked** (depends on Step 2) |
| Step 5: Navigate back to Chat page | Chat page loads | — | — | **blocked** (depends on Step 2) |
| Step 6: Reopen widget if closed, verify messages visible | Previous session restored | — | — | **blocked** (depends on Step 2) |
| Step 7: Send follow-up message | Message sent in same session | — | — | **blocked** (depends on Step 2) |
| Final state: Assistant responds in same session | Response appears, session continuous | — | — | **blocked** (depends on Step 2) |

**Summary:** 1/8 case elements covered (Step 1 only). Remaining 7 blocked by defect #1581.

### Axis 2 — Additional Observables Beyond Case

| Observable | Why Asserted | Grounded In |
|---|---|---|
| Widget has Close/New Chat/Expand buttons | Standard widget controls present | Step 1 snapshot — confirmed visible in widget header |
| Initial greeting message renders | Widget initialized correctly | Step 1 snapshot — "Hi! I'm your ELITEA Support Assistant..." visible |
| Send button starts disabled (empty input) | Correct initial state | Step 1 snapshot — button `[disabled]` when input empty |

---

## Test Data

| Field | Value |
|---|---|
| Test message | "Navigation persistence test" |
| Follow-up message (not reached) | (Any short message to verify session continuity) |
| Navigation route | Chat → Agents → Chat |

---

## Classification Rationale

**Status:** `defect-found`

**Reason:** Real product defect (#1581) prevents execution of Step 2 and all subsequent steps. The Support Assistant send button never enables after typing, making it impossible to send any message through the widget. This is not a test environment issue or a transient failure — it's a deterministic React state bug affecting the core user flow.

**Defect is not a navigation-persistence issue** (this case's subject) but a **message-sending prerequisite**. Without the ability to send an initial message, the case's actual objective (verifying state preservation across navigation) cannot be tested.

**Automation status:** Unblocked once #1581 is fixed. All handles except the blocking send-button behavior are automatable.

---

## Fidelity Declaration

No substitutions performed or required. Execution stopped at the first blocking defect.

---

## Evidence

- Screenshot: `automation/test-results/screenshots/ELITEA-2422-defect-send-button-disabled.png` — shows input field with text, send button still disabled
- Browser console: 0 errors, 1 warning (unrelated)
- Page URL: `http://localhost:5173/chat`
- Widget state: Open, message typed, button disabled

---

## Recommendations

1. **Block automation** until #1581 is resolved
2. **Retest this case** immediately after #1581 fix lands — navigation state preservation is a separate concern that may have its own bugs
3. **Add testids** to Support Assistant widget controls (see Handles Reference) once the widget is functional
4. **Consider** filing the widget's reliance on precise React state updates as a robustness issue — if automated testing via DOM manipulation cannot trigger the send flow, neither can assistive technologies or browser extensions

---

## Related Issues

- #1581 — Blocking defect (Support Assistant send button never enables)
- #1583 — Support Assistant drag-and-drop file attachment not implemented (ELITEA-2420)
- #1584 — Support Assistant selected file not sent with message (ELITEA-2421)

---

**Analyst:** qa-engineer (Sage)  
**Execution date:** 2026-08-18  
**Analysis duration:** ~15 minutes (stopped at blocking defect)
