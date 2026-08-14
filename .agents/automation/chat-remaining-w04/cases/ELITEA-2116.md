---
id: ELITEA-2116
title: "Chat – Delete Confirmation Modal UI Validation"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2116: Chat – Delete Confirmation Modal UI Validation

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify the UI elements and behavior of the delete confirmation modal including title, body text, button styling, and dismissal via Escape or outside click.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation exists in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over any conversation, click three-dot icon, click Delete | Modal overlay dims background |
| 2 | Verify modal title text is "Delete conversation?" | Title is correct |
| 3 | Verify modal body text is "Are you sure to delete conversation? It can't be restored." | Body text is correct |
| 4 | Verify Cancel button is on the left as a secondary/outlined button | Cancel button styled correctly |
| 5 | Verify Delete button is on the right as a red/destructive button | Delete button styled correctly |
| 6 | Click outside the modal or press Escape | Modal closes without deleting the conversation |
| 7 | Verify the conversation remains in the list after dismissing via Escape or outside click | Conversation preserved |

---

## Expected Final State

The delete modal has correct UI elements and can be dismissed without triggering deletion.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Modal has correct title, body, button styles; dismissal via Escape/outside click works.

**Fail:**
- Any step produces an error or unexpected result.
- Modal text is wrong, button styles are wrong, or Escape triggers deletion.
