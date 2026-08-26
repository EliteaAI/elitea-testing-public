---
id: ELITEA-2164
title: "Chat – Search Cleared by Clicking X Icon Restores Default View"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2164: Chat – Search Cleared by Clicking X Icon Restores Default View

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that clicking the X icon in the search field closes the search and restores the full conversation list.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is on the Chats page with at least one conversation.

---

## Test Data

| Field | Value |
|-------|-------|
| Search query | un |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Click magnifier icon, type 'un', verify filtered results appear | Filtered results shown |
| 2 | Click the X (clear/close) icon to the right of the search input | Search field closes and disappears |
| 3 | Verify the left panel returns to default view with all conversations, folders, and date groups | Full conversation list restored |
| 4 | Verify no search filter is applied | All conversations visible |
| 5 | Verify the magnifier icon is visible again in the CHATS header | Magnifier icon visible |

---

## Expected Final State

Default conversation list view restored after closing search.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Default view restored after closing search.

**Fail:**
- Any step produces an error or unexpected result.
- Search filter remains after closing.
