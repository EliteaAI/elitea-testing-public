---
id: ELITEA-2133
title: "Chat – Folder Creation with Custom Name via CHATS Header Icon"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2133: Chat – Folder Creation with Custom Name via CHATS Header Icon

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that a custom folder name can be entered and saved when creating a folder via the CHATS header icon.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is on the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| Custom folder name | My Test Folder |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to the Chats section and click the folder icon in the CHATS header | New folder entry appears in editable mode |
| 2 | Clear the default name and type 'My Test Folder' | Custom name in input |
| 3 | Click the checkmark icon | Folder created with 'My Test Folder' in the folder list |
| 4 | Click on the folder to expand it | Folder expands showing empty state |

---

## Expected Final State

Folder 'My Test Folder' created and is empty.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Folder created with custom name.

**Fail:**
- Any step produces an error or unexpected result.
- Folder not created or name is wrong.
