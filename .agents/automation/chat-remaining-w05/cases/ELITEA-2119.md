---
id: ELITEA-2119
title: "Chat – Folder Name Edited Inline During Creation with Custom Name"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2119: Chat – Folder Name Edited Inline During Creation with Custom Name

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that typing a custom folder name during creation and clicking the checkmark saves the folder with the custom name.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is on the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| Custom folder name | My Sprint Folder |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to the Chats section and click the folder icon in the CHATS header | New folder entry appears in editable mode |
| 2 | Clear the default name and type 'My Sprint Folder' | Custom name appears in the input |
| 3 | Verify the checkmark icon is active | Checkmark is active |
| 4 | Click the checkmark icon | Folder is saved with 'My Sprint Folder' in the folder list |
| 5 | Verify the input field closes and the folder name is displayed as plain text | Folder visible in panel |

---

## Expected Final State

Folder 'My Sprint Folder' is created and visible in the panel.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Folder created with custom name.

**Fail:**
- Any step produces an error or unexpected result.
- Folder not created or name is wrong.
