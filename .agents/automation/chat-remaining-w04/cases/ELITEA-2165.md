---
id: ELITEA-2165
title: "Chat – Search Input Cleared by Deleting Text Updates Results Dynamically"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2165: Chat – Search Input Cleared by Deleting Text Updates Results Dynamically

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that deleting characters from the search field dynamically updates the results list.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is on the Chats page.

---

## Test Data

| Field | Value |
|-------|-------|
| Full query | unique |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Click magnifier icon and type 'unique'; verify filtered results shown | Filtered results shown |
| 2 | Delete characters one by one from the input | Results update dynamically showing more matches with each deletion |
| 3 | Delete all characters | All conversations shown or appropriate empty search state |

---

## Expected Final State

Results update dynamically as characters are deleted.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Dynamic results update on each character deletion.

**Fail:**
- Any step produces an error or unexpected result.
- Results do not update dynamically.
