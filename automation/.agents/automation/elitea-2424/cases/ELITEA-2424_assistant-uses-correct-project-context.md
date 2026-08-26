---
id: ELITEA-2424
title: "Assistant uses correct project context"
priority: medium
type: functional
module: support-assistant
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:support-assistant]
requirements: []
---

# ELITEA-2424: Assistant uses correct project context

**Module:** support-assistant · **Priority:** medium · **Type:** functional

**Objective:** Verify that Assistant uses correct project context. Success is confirmed when navigate to a different project and repeat steps 3–5 — verify the assistant correctly reflects the new project context.

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
| 1 | Navigate to a project other than the Support Assistant's own deployment project (e.g., any user project visible in the project selector) | Target page/section loads successfully. |
| 2 | Note the current project name shown in the Settings | Action completes without error and produces the expected UI state. |
| 3 | Open the Support Assistant widget | Target page/section loads successfully. |
| 4 | Send the message: "What project am I currently working in? What is the project name and project ID?" | Action completes without error and produces the expected UI state. |
| 5 | Verify the assistant responds with the correct project name and project ID that matches the project the user is currently browsing — NOT the internal Support Assistant deployment project | Condition holds as described. |
| 6 | Navigate to a different project and repeat steps 3–5 — verify the assistant correctly reflects the new project context | Target page/section loads successfully. |

---

## Expected Final State

Navigate to a different project and repeat steps 3–5 — verify the assistant correctly reflects the new project context.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Assistant uses correct project context.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.
