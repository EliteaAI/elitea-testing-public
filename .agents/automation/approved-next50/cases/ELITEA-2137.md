---
id: ELITEA-2137
title: "Chat – Move Conversation to a New Folder via Move To Menu"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2137: Chat – Move Conversation to a New Folder via Move To Menu

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a conversation can be moved to a newly created folder via the Create folder option in the Move to submenu.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation exists in Today/This Week/Older.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a conversation, click three-dot icon, hover over Move to | Submenu appears |
| 2 | Click 'Create folder' | New folder entry appears at top of folder list in editable mode |
| 3 | Verify checkmark and X icons are visible | Both icons visible |
| 4 | Click the checkmark icon to save the default folder name | New folder created; conversation moved into it |
| 5 | Verify a success toast appears confirming the move | Toast shown |
| 6 | Verify the conversation is no longer in its original date group | Removed from date groups |
| 7 | Expand the new folder and verify the conversation is inside | Conversation inside folder |

---

## Expected Final State

Conversation moved to a newly created folder.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation moved to new folder; success toast shown.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation not moved or folder not created.
