---
id: ELITEA-2421
title: "Send message with attached file"
priority: medium
type: functional
module: support-assistant
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:support-assistant]
requirements: []
---

# ELITEA-2421: Send message with attached file

**Module:** support-assistant · **Priority:** medium · **Type:** functional

**Objective:** Verify that Send message with attached file. Success is confirmed when verify the assistant returns a response that references or processes the file content.

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
| 1 | Open the Support Assistant widget | Target page/section loads successfully. |
| 2 | Click the Attach file button and select a small text file via the file picker | Control responds; expected next state is shown. |
| 3 | Verify a file preview or attachment chip appears in the input area before sending | Condition holds as described. |
| 4 | Type "Summarize the content of this file" in the input field | Field accepts the input and displays the entered value. |
| 5 | Click Send (or press Enter) | Control responds; expected next state is shown. |
| 6 | Verify the message is sent with the attachment indicator visible in the chat | Condition holds as described. |
| 7 | Verify the assistant returns a response that references or processes the file content | Condition holds as described. |

---

## Expected Final State

Verify the assistant returns a response that references or processes the file content.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Send message with attached file.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.
