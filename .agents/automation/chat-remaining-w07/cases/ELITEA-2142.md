---
id: ELITEA-2142
title: "Chat – Drag and Drop Conversation to a Folder"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2142: Chat – Drag and Drop Conversation to a Folder

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that dragging a conversation from a date group and dropping it onto a folder moves the conversation into the folder.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation in Today/This Week/Older and at least one folder exist.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and verify a conversation is visible in a date group and a folder exists | Both visible |
| 2 | Click and hold (drag) the conversation from the date group section | Drag started |
| 3 | Drag the conversation toward a folder in the left panel | Target folder becomes visually highlighted |
| 4 | Drop the conversation onto the highlighted folder | Conversation removed from original date group |
| 5 | Verify the folder contains the dropped conversation when expanded | Conversation inside folder |
| 6 | Verify a success toast confirms the move | Toast shown |

---

## Expected Final State

Conversation dragged into folder successfully.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Drag and drop moves conversation to folder.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation not moved or drag-and-drop does not work.
