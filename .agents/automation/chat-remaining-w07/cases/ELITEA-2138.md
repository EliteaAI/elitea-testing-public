---
id: ELITEA-2138
title: "Chat – Move Conversation to a New Folder with Custom Name via Move To Menu"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2138: Chat – Move Conversation to a New Folder with Custom Name via Move To Menu

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a conversation can be moved to a new folder with a custom name entered during creation.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation exists.

---

## Test Data

| Field | Value |
|-------|-------|
| Custom folder name | Sprint Chats |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a conversation, click three-dot icon, hover over Move to, click Create folder | New folder input appears |
| 2 | Clear the default name and type 'Sprint Chats', click checkmark | Folder 'Sprint Chats' created; conversation moved |
| 3 | Verify a success toast appears confirming the move | Toast shown |
| 4 | Verify the conversation is no longer in its original date group | Removed from date groups |
| 5 | Expand 'Sprint Chats' and verify the conversation is listed inside | Conversation inside folder |

---

## Expected Final State

Conversation moved to 'Sprint Chats' folder.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation in 'Sprint Chats'; success toast shown.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation not moved or folder name wrong.
