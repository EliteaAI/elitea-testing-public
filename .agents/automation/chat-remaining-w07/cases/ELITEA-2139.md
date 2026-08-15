---
id: ELITEA-2139
title: "Chat – Move Conversation Back to the List via Move To Menu"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2139: Chat – Move Conversation Back to the List via Move To Menu

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a conversation inside a folder can be moved back to the general list via the 'Back to the list' option in the Move to submenu.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation is inside a folder.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and expand a folder with at least one conversation | Folder expanded; conversation visible |
| 2 | Hover over the conversation and click the three-dot icon, hover over Move to | Submenu appears |
| 3 | Click 'Back to the list' | Conversation removed from folder |
| 4 | Verify the conversation now appears in the Today date group | Conversation in Today |
| 5 | Verify a success toast appears confirming the move | Toast shown |
| 6 | Verify the folder still exists even if now empty | Folder remains |

---

## Expected Final State

Conversation moved out of folder and appears in Today.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation moved to Today; folder remains.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation remains in folder or disappears.
