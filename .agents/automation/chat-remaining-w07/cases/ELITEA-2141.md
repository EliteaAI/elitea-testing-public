---
id: ELITEA-2141
title: "Chat – Move Conversation Between Two Folders via Move To Menu"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2141: Chat – Move Conversation Between Two Folders via Move To Menu

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a conversation can be moved from one folder to another folder via the Move to submenu.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least two folders exist, one containing at least one conversation.

---

## Test Data

| Field | Value |
|-------|-------|
| Source folder | New folder_edited | Target folder | New folder5 |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and expand a folder containing a conversation | Conversation visible |
| 2 | Hover over the conversation, click three-dot icon, hover over Move to | Submenu shows all available folders |
| 3 | Select a different folder from the submenu (e.g. 'New folder5') | Success toast: 'Chat moved to New folder5 folder successfully' |
| 4 | Verify the conversation is no longer listed under the source folder | Removed from source folder |
| 5 | Expand 'New folder5' and verify the conversation is inside | Conversation in target folder |

---

## Expected Final State

Conversation moved from source folder to target folder.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation in target folder; removed from source.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation remains in source or disappears.
