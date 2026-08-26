---
id: ELITEA-2027
title: "Pipeline — Verify Node Configuration via YAML (Automation Approach)"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2027: Pipeline — Verify Node Configuration via YAML (Automation Approach)

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that the YAML representation of an LLM node accurately reflects all configuration set via the Flow editor, and establish the automation approach of verifying node configuration by reading YAML rather than inspecting individual UI fields.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with access to the Pipelines feature.

---

## Test Data

| Field | Value |
|-------|-------|
| SYSTEM type/value | fixed / "Act as helper" |
| TASK type/value | fstring / contains "{input}" |
| CHAT HISTORY type/value | fixed / "[]" |
| Input variables | [input] |
| Output variables | [output1] |
| structured_output | false |
| transition | END |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with an LLM node configured via Flow view (SYSTEM: Fixed/"Act as helper", TASK: F-String/"{input}", CHAT HISTORY: Fixed/"[]", Input: [input], Output: [output1]) | LLM node is configured and pipeline is ready to save |
| 2 | Save pipeline | Pipeline saves without errors |
| 3 | Switch to "Yaml" view | YAML editor displays the pipeline definition |
| 4 | Parse YAML content and verify state section contains: input (type: str), messages (type: list), output1 (type: str) | State section matches expected variables and types |
| 5 | Verify entry_point matches the LLM node id | entry_point field references the correct node |
| 6 | Verify nodes array contains the LLM node with: id (node name), type: llm, input: [input], input_mapping.system (type: fixed, value: "Act as helper"), input_mapping.task (type: fstring, value containing "{input}"), input_mapping.chat_history (type: fixed, value: "[]"), output: [output1], structured_output: false, transition: END | All LLM node fields in YAML match the Flow editor configuration |
| 7 | Confirm that this YAML-based approach should be used for all node types in automation | YAML accurately represents all node configurations |

---

## Expected Final State

The YAML view accurately reflects the LLM node configuration set in the Flow editor. All state variables, node fields, input mappings, and transitions match expected values. This confirms YAML verification as the preferred automation approach for node config validation.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All YAML fields match the configured values exactly.

**Fail:**
- Any step produces an error or unexpected result.
- Any YAML field does not match the corresponding Flow editor configuration.
