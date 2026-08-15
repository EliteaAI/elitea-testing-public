---
id: ELITEA-2124
title: "Chat – Folder Rename – Check Icon Inactive When Name is Empty"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2124: Chat – Folder Rename – Check Icon Inactive When Name is Empty

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that clearing the folder name field to empty disables the checkmark icon.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one existing folder is present in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a folder, click three-dot icon, click Edit | Folder name is editable |
| 2 | Clear the entire content of the input field | Field is empty |
| 3 | Verify the checkmark icon is in a disabled/inactive state | Checkmark inactive |
| 4 | Attempt to click the checkmark icon | Click has no effect; save not triggered |

---

## Expected Final State

Empty name disables the checkmark; save cannot be triggered.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Checkmark inactive when field is empty.

**Fail:**
- Any step produces an error or unexpected result.
- Save triggered with empty field.
