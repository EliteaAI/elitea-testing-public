---
id: ELITEA-2457
title: "Chat – Create folder with custom name"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2457: Chat – Create folder with custom name

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that Chat – Create folder with custom name. Success is confirmed when expand the folder and verify it is empty with no conversations inside.

---

## Preconditions

- User is logged in to the Elitea platform.


---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Chats section and click the folder icon in the CHATS header | Target page/section loads successfully. |
| 2 | Verify the new folder input field appears with a default name | Condition holds as described. |
| 3 | Clear the default name and type a custom name (e.g. "My Test Folder") | Action completes without error and produces the expected UI state. |
| 4 | Click the checkmark icon | Control responds; expected next state is shown. |
| 5 | Verify the folder is created with the name "My Test Folder" in the folder list | Condition holds as described. |
| 6 | Expand the folder and verify it is empty with no conversations inside | Action completes without error and produces the expected UI state. |

---

## Expected Final State

Expand the folder and verify it is empty with no conversations inside.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Chat – Create folder with custom name.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.
