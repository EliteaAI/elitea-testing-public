---
id: ELITEA-2149
title: "Chat – Pin a Conversation via Pin on Top Option"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2149: Chat – Pin a Conversation via Pin on Top Option

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that pinning a conversation moves it to the pinned section above folders with a pin icon.

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
| 1 | Navigate to Chats and hover over a conversation, click three-dot icon, click 'Pin on top' | Conversation moves to pinned section above folders |
| 2 | Verify a pin icon is displayed next to the pinned conversation name | Pin icon visible |
| 3 | Verify the conversation is no longer in its original date group | Removed from date groups |
| 4 | Verify the panel order: pinned folders, pinned conversations, unpinned folders, unpinned conversations | Panel order is correct |

---

## Expected Final State

Conversation pinned and appears above folders with pin icon.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation pinned; panel order correct.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation not pinned or panel order wrong.
