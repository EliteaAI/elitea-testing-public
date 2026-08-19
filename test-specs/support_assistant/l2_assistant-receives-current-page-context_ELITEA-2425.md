---
id: ELITEA-2425
title: Assistant receives current page context
priority: 2
status: defect-found
surface: support-assistant
test_type: functional
browsers: [chromium]
---

# ELITEA-2425: Assistant receives current page context

**Objective:** Verify that the Support Assistant receives and correctly reports the current page context when asked about the user's location or the entity being viewed.

**Priority:** P2 (Medium)  
**Surface:** Support Assistant widget  
**Status:** `defect-found` — Support Assistant echoes questions instead of answering them

---

## Defect Found

**Defect**: Support Assistant only echoes the user's question back without providing actual answers about page context.

**Steps to reproduce:**
1. Navigate to any page (e.g., `/agents/all`)
2. Open Support Assistant widget
3. Ask: "What page am I currently on in the application?"
4. Observe response

**Expected:** Assistant responds with the current page/section name (e.g., "You are on the Agents page" or "You are viewing the Agents section").

**Actual:** Assistant only echoes back "Echo: What page am I currently on in the application?" without answering the question.

**Frequency:** Always (reproduced on Agents page, Pipelines page, and Agent detail page)

**Evidence:**
- `test-results/screenshots/ELITEA-2425-step-08-full-response.png` — Agents page response showing echo only
- `test-results/screenshots/ELITEA-2425-step-11-pipelines-response.png` — Pipelines page response showing echo only  
- `test-results/screenshots/ELITEA-2425-step-17-final-response.png` — Agent detail page response showing echo only

**Additional context:** The welcome message claims "I have context about your current screen and settings", but this context is not being utilized in responses.

---

## Secondary Issue

**Issue**: Agent detail page `/agents/all/5` returns 404 error and shows "Page not found" message in main content area.

**Console error:** `Failed to load resource: the server responded with a status of 400 (Bad Request) @ http://localhost:5173/api/v2/elitea_core/public_application/prompt_lib/5:0`

This may be environmental (agent ID 5 doesn't exist in test environment) or a routing issue.

---

## Preconditions

- User is logged in to Elitea platform
- Support Assistant is enabled and accessible

---

## Test Data

No specific test data required. Any existing agents/pipelines can be used.

---

## Test Steps (as specified in TMS case)

| # | Step | Expected Result | Actual Result | Status |
|---|------|-----------------|---------------|--------|
| 1 | Navigate to Agents page (`/agents/all`) | Page loads successfully | ✅ Pass | Pass |
| 2 | Open Support Assistant widget | Widget opens with welcome message | ✅ Pass | Pass |
| 3 | Send: "What page am I currently on in the application?" | Assistant responds with current page context | ❌ Fail — Only echoes question | **FAIL** |
| 4 | Verify assistant responds with reference to Agents section or correct current page path | Response mentions "Agents" or `/agents/all` | ❌ Fail — No actual response | **FAIL** |
| 5 | Navigate to Pipelines page and open widget again | Widget opens on new page | ✅ Pass | Pass |
| 6 | Send same question — verify assistant now reports Pipelines page context | Response mentions "Pipelines" or `/pipelines/all` | ❌ Fail — Only echoes question | **FAIL** |
| 7 | Open specific Agent detail page; send: "What entity am I currently viewing?" — verify assistant reports agent name/type from context payload | Response includes agent name/ID or type | ❌ Fail — Only echoes question; page also returned 404 | **FAIL** |

---

## Coverage Map

### Axis 1: TMS Case Requirements

| Case Element | Expected Result | Covered By | Asserted Where | Disposition |
|---|---|---|---|---|
| Navigate to Agents page | Page loads successfully | Step 1 | Navigation + snapshot | ✅ Covered |
| Open Support Assistant widget | Widget visible with title and input | Step 2 | Widget open check + snapshot | ✅ Covered |
| Send message asking about current page | Message sent and response received | Step 3 | Message sent + wait for response | ✅ Covered |
| Assistant responds with page context reference | Response contains "Agents" or page path | Step 4 | Response text verification | ❌ **DEFECT** — Only echo returned |
| Navigate to Pipelines page | Page loads, widget can be reopened | Step 5 | Navigation + widget reopen | ✅ Covered |
| Send same question on different page | Response updates to reflect new page | Step 6 | Response text verification | ❌ **DEFECT** — Only echo returned |
| Open specific agent detail page | Agent detail page loads | Step 7 (partial) | Navigation attempt | ⚠️ **ISSUE** — 404 error on `/agents/all/5` |
| Ask about specific entity being viewed | Response includes agent name/type | Step 7 (partial) | Response text verification | ❌ **DEFECT** — Only echo returned |

### Axis 2: Additional Coverage

| Observable | Why Asserted | Grounded In |
|---|---|---|
| Welcome message claims "I have context about your current screen" | Verify feature claim is true | TMS case objective + welcome message text |
| Widget persists across page navigation | Ensure context updates don't break widget | Common cross-page behavior expectation |
| Console errors when assistant responds | Catch silent backend failures | Standard error-checking practice |
| 400 error on public_application endpoint | Agent detail page may have routing issue | Console log observation during Step 7 |

---

## Blocked Steps

None — all steps executed, but core functionality (context-aware responses) is defective.

---

## Known Defects Referenced

- **#[TBD]** — Support Assistant only echoes questions instead of answering (to be filed)

---

## Handles Reference

All handles below are from the **Support Assistant widget**, which is a first-party component from the `elitea_assistant` connected repo (`@eliteaai/elitea-assistant`). Per `.agents/testing.md` § Locator policy, connected-first-party repos follow the same testid discipline as EliteaUI — testids are added in the source repo on its `automation/testids` branch.

| Element | Current Handle | PROVENANCE | Notes |
|---|---|---|---|
| Support Assistant launcher button | `button[aria-label="Support Assistant"]` | on-main ✓ (aria-label) | ⚠️ **testid needed:** `support-assistant-launcher-button` — add in `elitea_assistant` repo |
| Widget close button | `button[aria-label="Close chat"]` | on-main ✓ (aria-label) | ⚠️ **testid needed:** `support-assistant-close-button` — add in `elitea_assistant` repo |
| Widget title | `.elitea-assistant-header-title` (fallback in page object) | needs-adding | ⚠️ **testid needed:** `support-assistant-title` |
| Message input field | `input[placeholder*="Type a message"]` | on-main ✓ (placeholder) | ⚠️ **testid needed:** `support-assistant-message-input` |
| Send message button | `button[aria-label*="Send"]` | on-main ✓ (aria-label) | ⚠️ **testid needed:** `support-assistant-send-button` |
| Message container | `.elitea-assistant-messages` (fallback in page object) | needs-adding | ⚠️ **testid needed:** `support-assistant-messages-container` |
| Individual message bubbles | (not yet captured — would need for text extraction) | needs-adding | ⚠️ **testid needed:** `support-assistant-message-user` / `support-assistant-message-assistant` |

**Note:** The Support Assistant page object (`automation/pages/support_assistant_page.py`) currently uses fallback locators exclusively. All testids above should be added to the `elitea_assistant` repo source (not EliteaUI) per `.agents/workflow.md` § Connected repos.

---

## Notes

1. **Core feature is non-functional**: The entire page-context feature cannot be verified because the assistant doesn't process or respond to questions—it only echoes them back.

2. **Backend vs Frontend issue**: The echo behavior suggests either:
   - The AI model/backend is returning echoes instead of answers
   - The context payload is not being sent from the frontend
   - The assistant's prompt/instructions are malformed

3. **All three test scenarios failed identically**: Agents page, Pipelines page, and Agent detail page all produced the same echo-only behavior, indicating a systemic issue rather than a page-specific problem.

4. **Agent detail 404**: The `/agents/all/5` route returned "Page not found" with a 400 error on `/api/v2/elitea_core/public_application/prompt_lib/5`. This may be:
   - Environmental (agent ID 5 doesn't exist in test environment)
   - A routing issue between list and detail views
   - Separate from the context issue

5. **MUI overlay click workaround required**: Clicking the Support Assistant launcher button requires JavaScript evaluation (`el.click()`) due to MUI overlay interception — documented pattern in `.agents/memory/qa-engineer/project_briefing.md`.

6. **Testid migration needed**: The Support Assistant widget (from `elitea_assistant` connected repo) needs testids added. This is tracked tech debt similar to the ~350 raw handles in EliteaUI's `automation/pages/` (issues #25/#42).

---

## Test Artifacts

- **Screenshots**: `test-results/screenshots/ELITEA-2425-step-*.png` (9 screenshots captured)
- **Snapshots**: `test-results/screenshots/ELITEA-2425-step-*.md` (accessibility tree snapshots)
- **Console logs**: Available in `.playwright-mcp/console-*.log`

---

## Classification

**Status:** `defect-found` — Core functionality (context-aware responses) is broken. The Support Assistant cannot provide meaningful answers about the current page or entity being viewed.

**Reason:** The feature under test (receiving and reporting page context) is completely non-functional due to the echo-only behavior. This blocks any meaningful automation of context-aware response verification.

**Next Steps:**
1. File bug for echo-only behavior (strict-per-bug style per `.agents/profile.md`)
2. Investigate whether issue is backend (AI model) or frontend (context payload)
3. After fix, re-analyze this case to verify correct responses on all three tested pages
