---
id: ELITEA-2148
title: "Chat – Folder Displays Conversation Count or Empty State"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2148: Chat – Folder Displays Conversation Count or Empty State

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that folders show their contents when expanded and display an 'empty' state when they have no conversations.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one folder with conversations and one empty folder exist.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and click on a folder with conversations to expand it | Conversations are listed below the folder name |
| 2 | Click the folder again to collapse it | Folder collapses; conversations hidden |
| 3 | Click on a folder with no conversations | Folder shows 'No conversations added' text when expanded |

---

## Expected Final State

Folders expand/collapse correctly and show empty state when empty.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Folders show correct content and empty state.

**Fail:**
- Any step produces an error or unexpected result.
- Folders do not expand/collapse or empty state is not shown.
