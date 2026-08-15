---
id: ELITEA-2121
title: "Chat – Folder Rename via Edit Option in Context Menu"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2121: Chat – Folder Rename via Edit Option in Context Menu

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a folder can be renamed via the three-dot context menu Edit option and the new name is saved correctly.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one existing folder is present in the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| New folder name | New folder_edited |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to the Chats section and hover over any existing folder | Three-dot icon appears |
| 2 | Click the three-dot icon and verify context menu: Delete, Edit, Export, Pin or Unpin | Context menu visible |
| 3 | Click the Edit option | Folder name becomes editable with checkmark and X icons |
| 4 | Clear the current name and type 'New folder_edited' | New name appears in the input |
| 5 | Click the checkmark icon | Folder renamed; new name displayed in folder list |
| 6 | Verify no error message is shown | Rename applied successfully |

---

## Expected Final State

Folder is renamed to 'New folder_edited'.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Folder renamed correctly via context menu.

**Fail:**
- Any step produces an error or unexpected result.
- Rename fails or name is not updated.
