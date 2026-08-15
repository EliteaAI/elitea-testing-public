---
id: ELITEA-2134
title: "Chat – Folder Creation Cancel Discards New Folder"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2134: Chat – Folder Creation Cancel Discards New Folder

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking the X icon during folder creation discards the new folder without adding it to the folder list.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is on the Chats section.

---

## Test Data

| Field | Value |
|-------|-------|
| Discarded folder name | Cancelled Folder |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and click the folder icon in the CHATS header | New folder input appears |
| 2 | Type 'Cancelled Folder' | Name in input |
| 3 | Click the X (cancel) icon | Input closes without saving |
| 4 | Verify no folder named 'Cancelled Folder' is added to the list | Folder not created |
| 5 | Verify the folder list remains unchanged | Folder list unchanged |

---

## Expected Final State

No new folder is created after cancelling.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Cancel discards folder creation.

**Fail:**
- Any step produces an error or unexpected result.
- Folder created despite cancelling.
