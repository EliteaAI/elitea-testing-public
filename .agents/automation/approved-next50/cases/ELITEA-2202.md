---
id: ELITEA-2202
title: "Chat – Slash Commands – Verify Typing / When No Toolkits or MCPs Are Added Displays Empty Results"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2202: Chat – Slash Commands – Verify Typing / When No Toolkits or MCPs Are Added Displays Empty Results

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that typing '/' in the message input when no toolkits or MCPs are added shows a 'MENTION TOOLKIT OR MCP' dropdown with no results.

---

## Preconditions

- User is logged in to the Elitea platform.
- User has an open conversation with no toolkits or MCPs added.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Create a new conversation with no toolkits or MCPs added | Conversation open; PARTICIPANTS has no TOOLKITS or MCPS |
| 2 | Click into the message input field and type '/' | Dropdown appears with heading 'MENTION TOOLKIT OR MCP' |
| 3 | Verify dropdown shows 'No matching results' or empty list | No toolkits or MCPs listed |
| 4 | Press elsewhere to close dropdown | Dropdown closes |

---

## Expected Final State

'/' with no toolkits/MCPs shows empty dropdown.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Empty dropdown shown for '/' with no participants.

**Fail:**
- Any step produces an error or unexpected result.
- Dropdown shows non-existent items.
