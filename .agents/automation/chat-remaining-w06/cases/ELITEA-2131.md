---
id: ELITEA-2131
title: "Chat – Folder Rename – No Changes Made Checkmark Inactive"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2131: Chat – Folder Rename – No Changes Made Checkmark Inactive

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that the checkmark icon is inactive when no changes are made to the folder name in the edit field.

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
| 1 | Navigate to Chats, hover over a folder, click three-dot icon, click Edit | Folder name is editable with current name pre-filled |
| 2 | Do not make any changes to the folder name | Name is unchanged |
| 3 | Verify the checkmark icon is in a disabled/inactive state | Checkmark is inactive |
| 4 | Attempt to click the checkmark icon | Click has no effect; name unchanged |
| 5 | Click the X icon to close the edit mode | Edit mode closed |
| 6 | Verify the folder name is unchanged in the folder list | Name unchanged |

---

## Expected Final State

Checkmark stays inactive when no changes are made; folder name is unchanged.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Checkmark inactive; no changes applied.

**Fail:**
- Any step produces an error or unexpected result.
- Save triggered without changes.
