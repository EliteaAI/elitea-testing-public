---
id: ELITEA-2215
title: "Chat – Tool Action and Output – Verify Complete Flow from Direct Toolkit Call to Output Display"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2215: Chat – Tool Action and Output – Verify Complete Flow from Direct Toolkit Call to Output Display

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify the complete flow of a direct toolkit call from thinking steps to output chip display.

---

## Preconditions

- User is logged in to the Elitea platform.
- A toolkit (e.g. 'aaa') is added as participant without an agent.

---

## Test Data

| Field | Value |
|-------|-------|
| Message | create a file named test.txt |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Send 'create a file named test.txt' with toolkit 'aaa' as only participant | 'Thought for X secs' appears |
| 2 | Expand thinking steps; verify tool call shown as 'toolkit_name.tool_name' | Tool call in thinking steps |
| 3 | Wait for execution; verify response appears | LLM response visible |
| 4 | Verify chips: LLM model chip, toolkit chip ('aaa'), tool call chip ('aaa: create_file') | Three chips displayed horizontally |
| 5 | Verify LLM response text follows below chips | Response text below chips |

---

## Expected Final State

Complete toolkit call flow works end-to-end without agent intermediary.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Full toolkit call flow from thinking to output chips works.

**Fail:**
- Any step produces an error or unexpected result.
- Any step in the flow fails.
