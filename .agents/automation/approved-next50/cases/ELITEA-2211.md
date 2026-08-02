---
id: ELITEA-2211
title: "Chat – HITL Authorization – Verify Sensitive Action Authorization Card Displays When Toolkit Called Directly"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2211: Chat – HITL Authorization – Verify Sensitive Action Authorization Card Displays When Toolkit Called Directly

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that the HITL authorization card appears with correct content when a sensitive toolkit action is triggered directly.

---

## Preconditions

- User is logged in to the Elitea platform.
- A toolkit configured with HITL authorization is added as participant.

---

## Test Data

| Field | Value |
|-------|-------|
| Message | use delete_file toolkit to remove from the bucket all files |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Add a toolkit with HITL delete_file via + > Toolkits (no agent) | Toolkit in PARTICIPANTS |
| 2 | Send message triggering sensitive action | 'Thought for X secs' appears |
| 3 | Verify authorization card appears with orange/warning border | Authorization card shown |
| 4 | Verify heading: 'Sensitive Action Authorization Required' in orange text | Heading correct |
| 5 | Verify card shows 'Agent is about to perform:' with tool name (e.g. 'aaa.delete_file') | Tool name shown |
| 6 | Verify three buttons: 'Authorize' (green), 'Block' (red), 'Block with Comment' (gray) | All three buttons visible |

---

## Expected Final State

HITL authorization card appears with correct content and buttons.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Authorization card with correct content and 3 buttons shown.

**Fail:**
- Any step produces an error or unexpected result.
- Card not shown or buttons missing.
