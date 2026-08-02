---
id: ELITEA-2079
title: "Chat – Pipeline Flow Editor – Add LLM Node, Verify YAML, Save Pipeline, and Add to Conversation"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2079: Chat – Pipeline Flow Editor – Add LLM Node, Verify YAML, Save Pipeline, and Add to Conversation

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify that adding an LLM node to the Flow Editor, verifying its YAML representation, saving the pipeline, and closing the canvas correctly adds the pipeline as a participant in the conversation.

---

## Preconditions

- User is logged in to the Elitea platform.
- The "test-pipeline" Flow Editor is open with only the "End" node visible (following ELITEA-2078).

---

## Test Data

| Field | Value |
|-------|-------|
| Test message | hello |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Verify the Flow Editor is open with only the "End" node visible and "Flow" tab active | Flow editor initialized |
| 2 | Click "+ Add node" and select "LLM" | LLM node is added above the End node |
| 3 | Click the "Yaml" tab | YAML editor opens with pipeline configuration code |
| 4 | Verify line 1 shows "entry_point: LLM 1", line 2 shows "nodes:", line 3 shows "- id: LLM 1", line 4 shows "type: llm" | YAML code is correctly formatted |
| 5 | Verify YAML includes input_mapping, task, structured_output: false, and transition: END | All required properties present |
| 6 | Click back on the "Flow" tab | Visual editor shown; LLM node still present |
| 7 | Click the "Save" button | Pipeline saved successfully; success notification appears |
| 8 | Click the X button to close the canvas panel | Canvas closes; conversation view is fully displayed |
| 9 | Verify the "test-pipeline" chip shows "test-pipeline base" (without "Editing..." status) in the message input area | Pipeline chip updated |
| 10 | Verify a "PIPELINES" section now appears in the PARTICIPANTS panel with "test-pipeline base" listed | Pipeline is added as participant |
| 11 | Send a test message "hello" | Pipeline processes the message through the LLM node and generates a response |

---

## Expected Final State

The LLM node is added, YAML is valid, pipeline is saved and added as a participant to the conversation, and pipeline responds to messages.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- LLM node added, YAML valid, pipeline saved, added as participant, responds to messages.

**Fail:**
- Any step produces an error or unexpected result.
- YAML is invalid, pipeline fails to save, or pipeline does not appear in PARTICIPANTS.
