---
id: ELITEA-2129
title: "Chat – Folder Rename – Cannot Type or Paste Beyond 50 Characters"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2129: Chat – Folder Rename – Cannot Type or Paste Beyond 50 Characters

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that the folder rename field enforces a 50-character maximum for both typing and paste operations.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one existing folder is present in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| 70-char clipboard | 70 characters string |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a folder, click three-dot icon, click Edit | Folder name is editable |
| 2 | Clear the current name and attempt to type 51+ characters | Only first 64 characters accepted; 65th is not entered |
| 3 | Prepare a 70-character string and paste it using Ctrl+V | Input contains no more than 50 characters after paste |
| 4 | Click the checkmark icon | Folder saved with exactly 50 characters; no error |

---

## Expected Final State

Folder rename field enforces 50-character max for both typing and paste.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- 50-character limit enforced for type and paste.

**Fail:**
- Any step produces an error or unexpected result.
- More than 50 characters accepted.
