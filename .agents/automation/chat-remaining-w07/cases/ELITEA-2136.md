---
id: ELITEA-2136
title: "Chat – Move Conversation to Existing Folder – Conversation Removed from Date Group"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2136: Chat – Move Conversation to Existing Folder – Conversation Removed from Date Group

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that after moving a conversation to a folder, it is removed from all date groups (Today, This Week, Older) and exists only in the target folder.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least one conversation in Today and at least one folder exist.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Note the conversation name and its date group (e.g. Today) | Conversation noted |
| 2 | Hover over the conversation, click three-dot icon, hover over Move to, select a folder | Success toast appears |
| 3 | Verify the Today section no longer contains the moved conversation | Removed from Today |
| 4 | Verify the This Week and Older sections also do not contain it | Removed from all date groups |
| 5 | Verify the conversation appears exclusively in the selected folder | Conversation only in folder |

---

## Expected Final State

Conversation exists only in the target folder; removed from all date groups.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Conversation appears only in the target folder.

**Fail:**
- Any step produces an error or unexpected result.
- Conversation remains in date groups or appears in multiple places.
