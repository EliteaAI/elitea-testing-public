---
id: ELITEA-2117
title: "Chat – Deletion of the Last Remaining Conversation in a Project"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2117: Chat – Deletion of the Last Remaining Conversation in a Project

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that deleting the last conversation in a project empties the left panel, transitions the main panel to the new chat welcome state, and keeps the + Chat button active.

---

## Preconditions

- User is logged in to the Elitea platform.
- Exactly one conversation remains in the Chats section with no other conversations or folders.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and verify exactly one conversation exists in the left panel | One conversation listed; no others |
| 2 | Click on the conversation to open it | Messages are displayed in the main panel; conversation highlighted |
| 3 | Hover over the conversation, click three-dot icon, click Delete | "Delete conversation?" modal appears |
| 4 | Verify modal body reads "Are you sure to delete conversation? It can't be restored." | Body text correct |
| 5 | Click the Delete button | Modal closes without error |
| 6 | Verify the left panel conversation list is empty — no conversations under any date group | Left panel is empty |
| 7 | Verify the main panel transitions to the new chat welcome/empty state with Elitea logo and greeting | Welcome state shown |
| 8 | Verify the message input area is visible and active | Input field is ready |
| 9 | Verify no error banners or toast messages are present | No errors shown |
| 10 | Verify the page URL no longer references the deleted conversation | URL updated |
| 11 | Verify the + Chat button remains available | + Chat button is active |

---

## Expected Final State

After deleting the last conversation, the panel is empty, the welcome state is shown, and a new conversation can be started.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Left panel empties; welcome state shown; + Chat available.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation persists or welcome state is not shown.
