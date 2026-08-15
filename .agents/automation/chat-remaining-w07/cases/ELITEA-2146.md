---
id: ELITEA-2146
title: "Chat – Folder List is Scrollable When Many Folders Exist"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2146: Chat – Folder List is Scrollable When Many Folders Exist

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that the folder list in the left panel is scrollable when there are more folders than fit in the visible area.

---

## Preconditions

- User is logged in to the Elitea platform.
- A large number of folders exist (more than fit in the visible panel area).

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and verify the folder list contains many folders | Many folders visible |
| 2 | Hover over the folder list area | Scrollbar appears or list is scrollable |
| 3 | Scroll down through the folder list | Additional folders become visible |
| 4 | Verify all folders are accessible via scrolling | No folders hidden or cut off |
| 5 | Scroll back up and verify top folders are still accessible | Top folders visible after scrolling back |

---

## Expected Final State

All folders are accessible via scrolling.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Folder list is scrollable; all folders accessible.

**Fail:**
- Any step produces an error or unexpected result.
- List not scrollable or some folders are inaccessible.
