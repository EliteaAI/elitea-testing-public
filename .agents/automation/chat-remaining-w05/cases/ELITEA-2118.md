---
id: ELITEA-2118
title: "Chat – Folder Name Edited Inline During Creation with Default Name Saved"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2118: Chat – Folder Name Edited Inline During Creation with Default Name Saved

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking the checkmark without changing the default folder name during creation saves the folder with the default name.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is on the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to the Chats section | Chats section is displayed |
| 2 | Click the folder icon in the CHATS header to create a new folder | New folder entry appears in editable mode with default name e.g. 'New folder' |
| 3 | Do not change the default name | Default name remains in the input |
| 4 | Verify the checkmark icon is active (default name meets 3 char minimum) | Checkmark is active |
| 5 | Click the checkmark icon | Folder is saved with the default name and appears in the folder list |
| 6 | Verify the input field closes and the folder name is displayed as plain text | Folder name shows as plain text |

---

## Expected Final State

Folder is saved with the default name.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Folder saved with default name.

**Fail:**
- Any step produces an error or unexpected result.
- Folder not created or name is blank.
