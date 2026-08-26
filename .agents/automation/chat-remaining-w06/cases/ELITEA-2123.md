---
id: ELITEA-2123
title: "Chat – Folder Rename – Validation Tooltip Displayed for Invalid Input"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2123: Chat – Folder Rename – Validation Tooltip Displayed for Invalid Input

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that entering unsupported special characters in the folder rename field shows the correct validation tooltip and disables the checkmark.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one existing folder is present in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| Invalid folder name | Folder$$%% |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a folder, click three-dot icon, click Edit | Folder name is editable |
| 2 | Clear the current name and type 'Folder$$%%' | Input contains invalid characters |
| 3 | Verify a tooltip appears with validation message: "The folder name should be 3 to 64 characters long. It can include letters (a-z, A-Z), numbers (0-9), underscores (_), brackets ([]), parentheses (()), dots (.), hyphen(-), and spaces. Please note that the first character should not be a space." | Tooltip shows correct validation message |
| 4 | Verify the checkmark icon is inactive | Checkmark disabled |
| 5 | Attempt to click the checkmark icon | Click has no effect |
| 6 | Verify the folder name remains unchanged | Name unchanged |

---

## Expected Final State

Validation tooltip shown for invalid characters; checkmark disabled.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Tooltip shows correct message; checkmark disabled.

**Fail:**
- Any step produces an error or unexpected result.
- Tooltip not shown or checkmark active for invalid input.
