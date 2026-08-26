---
id: ELITEA-2120
title: "Chat – Folder Name Edited Inline During Creation – Cancel Discards Folder"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2120: Chat – Folder Name Edited Inline During Creation – Cancel Discards Folder

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking the X (cancel) icon during folder creation discards the new folder and leaves the folder list unchanged.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is on the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| Folder name | Temp Folder |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to the Chats section and click the folder icon in the CHATS header | New folder entry appears in editable mode |
| 2 | Type 'Temp Folder' | Name appears in the input |
| 3 | Click the X (cancel) icon | Input field closes without saving |
| 4 | Verify no folder named 'Temp Folder' appears in the folder list | Folder not created |
| 5 | Verify the folder list remains unchanged from before the creation attempt | Folder list unchanged |

---

## Expected Final State

No folder is created; folder list remains unchanged.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Cancel discards the folder creation.

**Fail:**
- Any step produces an error or unexpected result.
- Folder is created despite cancelling.
