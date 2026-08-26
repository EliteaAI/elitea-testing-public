---
id: ELITEA-2143
title: "Chat – Drag and Drop Conversation Highlights Target Folder on Hover"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2143: Chat – Drag and Drop Conversation Highlights Target Folder on Hover

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that when dragging a conversation over folders, each folder highlights as the conversation hovers over it.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation and at least two folders exist.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and begin dragging a conversation from the Today section | Drag started |
| 2 | Drag the conversation over different folders one at a time | Each folder becomes highlighted (dashed border) when dragged over |
| 3 | Move away from a folder and verify its highlight is removed | Highlight removed when moved away |
| 4 | Drop the conversation on a desired folder | Conversation moved into that folder; highlight disappears |

---

## Expected Final State

Folder highlighting works during drag and conversation is moved on drop.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Hover highlighting works; drop moves conversation.

**Fail:**
- Any step produces an error or unexpected result.
- Highlighting not shown or drop does not move conversation.
