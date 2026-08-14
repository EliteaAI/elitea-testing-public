---
id: ELITEA-2115
title: "Chat – Conversation Deletion – Conversation Inside a Folder"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2115: Chat – Conversation Deletion – Conversation Inside a Folder

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that deleting a conversation inside a folder removes it from the folder while the folder itself is preserved.

---

## Preconditions

- User is logged in to the Elitea platform.
- A folder with at least one conversation exists in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and expand a folder that contains at least one conversation | Conversations inside the folder are visible |
| 2 | Hover over a conversation inside the folder and click the three-dot icon | Context menu appears with Delete option |
| 3 | Click Delete | "Delete conversation?" confirmation modal appears |
| 4 | Click the Delete button | Conversation is removed from the folder |
| 5 | Verify the folder still exists in the left panel | Folder is not deleted |
| 6 | Verify if the folder was the last conversation, the folder now appears empty or reflects updated count | Folder shows empty state or updated count |

---

## Expected Final State

The conversation is deleted from the folder; the folder itself remains in the panel.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation deleted from folder; folder remains.

**Fail:**
- Any step produces an error or unexpected result.
- Folder is also deleted or conversation persists.
