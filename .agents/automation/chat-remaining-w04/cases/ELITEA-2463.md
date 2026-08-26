---
id: ELITEA-2463
title: "Chat – Search input opens, filters results dynamically, conversation is interactable"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2463: Chat – Search input opens, filters results dynamically, conversation is interactable

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that Chat – Search input opens, filters results dynamically, conversation is interactable. Success is confirmed when verify the search input field remains visible in the left panel while the conversation is open.

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
| 1 | Navigate to the Chats section and verify the CHATS header displays a magnifier (search) icon | Target page/section loads successfully. |
| 2 | Click the magnifier icon | Control responds; expected next state is shown. |
| 3 | Verify the left panel switches to a search input field, the input is focused, and an X icon appears on the right | Condition holds as described. |
| 4 | Type a partial search query (e.g. "un") | Field accepts the input and displays the entered value. |
| 5 | Verify the left panel displays filtered conversations/folders whose names contain the typed characters | Condition holds as described. |
| 6 | Verify results are grouped by pinned and date sections | Condition holds as described. |
| 7 | Verify non-matching conversations are not displayed | Condition holds as described. |
| 8 | Type the exact full name of a known conversation (e.g. "unique") | Field accepts the input and displays the entered value. |
| 9 | Verify only the matching conversation is shown under its correct date group | Condition holds as described. |
| 10 | Click on the matching conversation and verify it opens in the main panel with full message history | Control responds; expected next state is shown. |
| 11 | Verify the URL in the browser updates to reflect the selected conversation | Condition holds as described. |
| 12 | Verify the search input field remains visible in the left panel while the conversation is open | Condition holds as described. |

---

## Expected Final State

Verify the search input field remains visible in the left panel while the conversation is open.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Chat – Search input opens, filters results dynamically, conversation is interactable.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.
