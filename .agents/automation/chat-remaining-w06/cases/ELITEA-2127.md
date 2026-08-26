---
id: ELITEA-2127
title: "Chat – Folder Rename – First Character Cannot Be a Space"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2127: Chat – Folder Rename – First Character Cannot Be a Space

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a space cannot be used as the first character in the folder rename field.

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
| 2 | Clear the current name and press the Space key as the first character | Space not accepted as first character or checkmark stays inactive |
| 3 | Verify the tooltip validation message appears | Tooltip shows validation message |
| 4 | Verify the save cannot be triggered while name starts with a space | Checkmark inactive |

---

## Expected Final State

Leading space rejected; checkmark remains inactive.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Leading space rejected.

**Fail:**
- Any step produces an error or unexpected result.
- Leading space accepted or checkmark becomes active.
