---
id: ELITEA-2135
title: "Chat – Move Conversation to Existing Folder via Move To Menu"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2135: Chat – Move Conversation to Existing Folder via Move To Menu

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a conversation can be moved to an existing folder via the Move to submenu and a success toast appears.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one folder and one conversation in Today/This Week/Older exist.

---

## Test Data

| Field | Value |
|-------|-------|
| Target folder | New folder6 |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and hover over a conversation in the Today section, click three-dot icon | Context menu appears |
| 2 | Verify context menu has: Delete, Edit, Move to, Export, Playback, Pin on top | Options visible |
| 3 | Hover over the Move to option | Submenu appears: Create folder, Back to the list, existing folders |
| 4 | Click on an existing folder name (e.g. 'New folder6') | Success toast: 'Chat moved to [folder name] folder successfully' |
| 5 | Verify the conversation is no longer in Today/This Week/Older | Conversation removed from date groups |
| 6 | Expand the selected folder and verify the moved conversation is inside | Conversation inside the folder |

---

## Expected Final State

Conversation moved to the selected folder; success toast appeared.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation moved; success toast shown.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation not moved or toast not shown.
