---
id: ELITEA-2015
title: "Pipeline HITL Node — Runtime Behavior"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2015: Pipeline HITL Node — Runtime Behavior

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that during pipeline execution, a HITL node correctly pauses execution and displays action buttons (Approve, Edit, Reject), and that each action routes the flow to the configured target node.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline exists with configuration: LLM → HITL → Printer → END, with HITL routes: APPROVE→Printer, REJECT→END.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create pipeline: LLM → HITL → Printer → END with HITL routes configured (APPROVE→Printer, REJECT→END) | Pipeline is saved with the described topology |
| 2 | Execute pipeline with a message | Pipeline starts execution |
| 3 | Verify pipeline pauses at HITL node — chat shows user message content and action buttons (Approve, Edit, Reject) | Execution pauses, user message is displayed, and Approve/Edit/Reject buttons appear |
| 4 | Click "Approve" — verify flow continues to configured APPROVE route node | Flow proceeds to the Printer node |
| 5 | Verify final response appears in chat | Response message is displayed in the chat panel |
| 6 | Execute again, this time click "Reject" — verify flow goes to END (no further processing) | Pipeline ends without producing a Printer output |

---

## Expected Final State

The HITL node correctly pauses execution, presents action buttons, and routes to the appropriate target node based on the user's choice (Approve → Printer response; Reject → pipeline ends).

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- HITL node pauses execution, shows action buttons, and Approve/Reject correctly route to their configured targets.

**Fail:**
- Any step produces an error or unexpected result.
- HITL does not pause, action buttons are missing, or routing does not match configuration.
