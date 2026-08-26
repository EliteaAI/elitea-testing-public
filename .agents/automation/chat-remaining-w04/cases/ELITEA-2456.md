---
id: ELITEA-2456
title: "Chat – Conversation deletion with cancel and confirm flow"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2456: Chat – Conversation deletion with cancel and confirm flow

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that Chat – Conversation deletion with cancel and confirm flow. Success is confirmed when verify the main chat panel does not display the deleted conversation content.

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
| 1 | Navigate to the Chats section and hover over any conversation in the left panel | Target page/section loads successfully. |
| 2 | Verify the three-dot icon appears on the right side of the conversation row | Condition holds as described. |
| 3 | Click the three-dot icon and verify a context menu appears with options: Delete, Edit, Move to, Export, Playback, Pin on top | Control responds; expected next state is shown. |
| 4 | Click Delete | Control responds; expected next state is shown. |
| 5 | Verify a confirmation modal appears with title "Delete conversation?" and body text "Are you sure to delete conversation? It can't be restored." | Condition holds as described. |
| 6 | Verify the modal contains Cancel (secondary) and Delete (red/primary) buttons | Condition holds as described. |
| 7 | Click Cancel and verify the modal closes and the conversation remains in the list unchanged | Control responds; expected next state is shown. |
| 8 | Hover over the same conversation, open the context menu and click Delete again | Action completes without error and produces the expected UI state. |
| 9 | Verify the confirmation modal appears again | Condition holds as described. |
| 10 | Click Delete | Control responds; expected next state is shown. |
| 11 | Verify the modal closes and the deleted conversation is no longer present in the left panel | Condition holds as described. |
| 12 | Verify no error message is shown and the next conversation is highlighted as selected | Condition holds as described. |
| 13 | Verify the main chat panel does not display the deleted conversation content | Condition holds as described. |

---

## Expected Final State

Verify the main chat panel does not display the deleted conversation content.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Chat – Conversation deletion with cancel and confirm flow.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.
