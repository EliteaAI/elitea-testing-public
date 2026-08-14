---
id: ELITEA-2017
title: "Pipeline Execution — Long Response Streaming"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2017: Pipeline Execution — Long Response Streaming

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a pipeline with an LLM entry point streams long responses progressively in the chat panel without timeout or errors, and that the complete response exceeds a minimum character threshold.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with LLM node as entry point exists (TASK configured with F-String: "{input}").

---

## Test Data

| Field | Value |
|-------|-------|
| Model | GPT-5 mini (or equivalent) |
| User prompt | Write a 500-word essay on AI |
| Minimum response length | 200 characters |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with LLM node as entry point (configure TASK with F-String: "{input}") | Pipeline is created and ready for execution |
| 2 | In chat panel, select a model via Model Selector Menu (e.g., "GPT-5 mini") | Selected model is displayed in the model selector |
| 3 | Ask a question requiring lengthy answer: "Write a 500-word essay on AI" | Message is sent to the pipeline |
| 4 | Verify response streams progressively in chat (not all at once) | Tokens appear incrementally in the chat panel |
| 5 | Verify final response is complete and exceeds 200 characters | Response content length is greater than 200 characters |
| 6 | Verify no timeout or error during streaming | No error messages appear; streaming completes normally |

---

## Expected Final State

The pipeline streams a long response progressively in the chat, completing without errors or timeouts, and the final response exceeds 200 characters.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Response streams progressively, is complete, and exceeds 200 characters with no timeout.

**Fail:**
- Any step produces an error or unexpected result.
- Response does not stream, is incomplete, below 200 characters, or a timeout/error occurs.
