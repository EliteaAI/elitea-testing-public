---
id: ELITEA-2147
title: "Chat – Move To Submenu Folder List is Scrollable When Many Folders Exist"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2147: Chat – Move To Submenu Folder List is Scrollable When Many Folders Exist

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that the folder list inside the Move to submenu is scrollable when many folders exist.

---

## Preconditions

- User is logged in to the Elitea platform.
- Many folders exist in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats, hover over a conversation, click three-dot icon, hover over Move to | Submenu appears with Create folder, Back to the list, folder list |
| 2 | Verify when many folders exist the folder list in the submenu is scrollable | Folder list is scrollable |
| 3 | Scroll down through the submenu folder list | All folders are accessible |
| 4 | Select any folder from the scrollable list | Conversation moved; success toast appears |

---

## Expected Final State

Submenu folder list is scrollable; all folders accessible.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Submenu folder list is scrollable.

**Fail:**
- Any step produces an error or unexpected result.
- List not scrollable or some folders are inaccessible.
