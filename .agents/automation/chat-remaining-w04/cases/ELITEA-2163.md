---
id: ELITEA-2163
title: "Chat – Search No Results State"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2163: Chat – Search No Results State

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that searching for a non-existent conversation shows an empty state or 'No conversations found' message.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is on the Chats page.

---

## Test Data

| Field | Value |
|-------|-------|
| Query with no results | xyznotexists |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Navigate to Chats and click the magnifier icon | Search input opens |
| 2 | Type 'xyznotexists' | Left panel shows empty state or 'No conversations found' message |
| 3 | Verify no conversation items are displayed | Results area is empty |
| 4 | Verify no error or crash occurs | Page remains stable |

---

## Expected Final State

No results state shown correctly for non-matching query.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Empty state shown; no error.

**Fail:**
- Any step produces an error or unexpected result.
- Error occurs or existing conversations shown.
