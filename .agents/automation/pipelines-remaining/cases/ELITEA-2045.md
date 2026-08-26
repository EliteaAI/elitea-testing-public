---
id: ELITEA-2045
title: "Pipeline — Structured Output (Parse LLM Response into State Variables)"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2045: Pipeline — Structured Output (Parse LLM Response into State Variables)

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that enabling Structured output on an LLM node correctly parses the LLM response into multiple typed state variables, and that the configuration is accurately reflected in YAML.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with an LLM node exists.

---

## Test Data

| Field | Value |
|-------|-------|
| Output variable "name" | String type |
| Output variable "age" | Number type |
| Output variable "hobbies" | List type |
| Output variable "metadata" | Json type |
| SYSTEM prompt | Act as JSON Parser and parse user data into structured fields |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with an LLM node | Pipeline is created with LLM node |
| 2 | In State panel, add multiple output variables: "name" (String), "age" (Number), "hobbies" (List), "metadata" (Json) | All four variables are added to the State panel |
| 3 | In the LLM node, add all created variables to the Output combobox: "name", "age", "hobbies", "metadata" | All four variables are added to Output |
| 4 | Enable "Structured output" switch on the node | Structured output switch is enabled (checked) |
| 5 | Configure SYSTEM prompt: "Act as JSON Parser and parse user data into structured fields" | SYSTEM prompt is configured |
| 6 | Save pipeline | Pipeline saves without errors |
| 7 | Execute with input containing data matching the output schema | Pipeline execution completes |
| 8 | Verify response correctly parses values into each state variable | Each state variable is populated with the correctly parsed value |
| 9 | Verify in YAML: node has structured_output: true and output lists all variable names | YAML confirms structured_output: true and all output variable names |

---

## Expected Final State

The LLM node with Structured output enabled correctly parses a complex response into named typed state variables. YAML confirms structured_output: true and all output variable names.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- LLM parses response into all four state variables; YAML shows structured_output: true.

**Fail:**
- Any step produces an error or unexpected result.
- Structured output does not parse correctly, variables are not populated, or YAML is incorrect.
