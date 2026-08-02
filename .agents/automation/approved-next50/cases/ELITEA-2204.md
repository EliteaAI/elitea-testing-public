---
id: ELITEA-2204
title: "Chat – Slash Commands – Verify Selecting Toolkit from / Dropdown and Viewing Available Tools"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2204: Chat – Slash Commands – Verify Selecting Toolkit from / Dropdown and Viewing Available Tools

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that selecting a toolkit from the '/' dropdown shows its available tools.

---

## Preconditions

- User is logged in to the Elitea platform.
- Conversation with toolkit 'banana' added as participant.

---

## Test Data

| Field | Value |
|-------|-------|
| Toolkit | banana | Expected tools | index_data, list_collections, search_index, stepback_search_index |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Type '/' and click 'banana' in dropdown | Message field shows '/banana'; tools list 'BANANA AVAILABLE TOOLS' appears |
| 2 | Verify tools: index_data, list_collections, search_index, stepback_search_index | All tools listed |
| 3 | Click 'index_data' from tools list | Message field updates to '/banana/index_data' |

---

## Expected Final State

Selecting toolkit from '/' shows available tools; selecting a tool updates message field.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Toolkit tools shown; selecting updates message field.

**Fail:**
- Any step produces an error or unexpected result.
- Tools not shown or message field not updated.
