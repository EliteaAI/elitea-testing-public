---
id: ELITEA-2144
title: "Chat – Drag and Drop Conversation Between Two Folders"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2144: Chat – Drag and Drop Conversation Between Two Folders

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that dragging a conversation from one folder and dropping it onto another folder moves it correctly.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least two folders exist, one containing at least one conversation.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and expand a folder containing a conversation | Conversation visible |
| 2 | Click and hold the conversation to begin dragging | Drag started |
| 3 | Drag toward a different folder; verify it becomes highlighted | Target folder highlighted |
| 4 | Drop the conversation onto the target folder | Conversation removed from source folder |
| 5 | Expand the target folder and verify the conversation is inside | Conversation in target folder |
| 6 | Verify the source folder still exists | Source folder remains |
| 7 | Verify a success toast appears | Toast shown |

---

## Expected Final State

Conversation moved from source to target folder via drag and drop.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation in target folder; source folder remains.

**Fail:**
- Any step produces an error or unexpected result.
- Drag and drop does not work between folders.
