---
id: ELITEA-2423
title: "History loads correctly after page refresh"
priority: medium
type: functional
module: support-assistant
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:support-assistant]
requirements: []
---

# ELITEA-2423: History loads correctly after page refresh

**Module:** support-assistant · **Priority:** medium · **Type:** functional

**Objective:** Verify that History loads correctly after page refresh. Success is confirmed when repeat: send another message, refresh again — verify history still loads without errors.

---

## Preconditions

- User is logged in to the Elitea platform.


---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open the Support Assistant widget and send any message, wait for the response | Target page/section loads successfully. |
| 2 | Refresh the browser page (F5) | Action completes without error and produces the expected UI state. |
| 3 | After the page reloads, open the Support Assistant widget | Action completes without error and produces the expected UI state. |
| 4 | Open the History panel — verify the GET /api/v2/support_assistant/conversations/ request returns HTTP 200 (not 500) | Target page/section loads successfully. |
| 5 | Verify the previous session is listed in history and can be opened | Condition holds as described. |
| 6 | Repeat: send another message, refresh again — verify history still loads without errors | Action completes without error and produces the expected UI state. |

---

## Expected Final State

Repeat: send another message, refresh again — verify history still loads without errors.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: History loads correctly after page refresh.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.
