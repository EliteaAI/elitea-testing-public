---
id: ELITEA-2046
title: "Pipeline — Structured Output Toggle Persistence"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2046: Pipeline — Structured Output Toggle Persistence

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Structured output toggle on a node correctly persists its enabled/disabled state after save and reload, and that the YAML reflects the toggle state.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with a node supporting structured output (LLM, Code, Toolkit, etc.) exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with a node supporting structured output (LLM, Code, Toolkit, etc.) | Pipeline is open with the node visible |
| 2 | Verify "Structured output" switch is disabled by default | Toggle shows disabled state |
| 3 | Toggle to enabled (checked) — save — reload — verify switch remains checked | After reload, Structured output switch is enabled |
| 4 | Toggle to disabled (unchecked) — save — reload — verify switch remains unchecked | After reload, Structured output switch is disabled |
| 5 | Verify in YAML: structured_output field toggles between true/false | YAML shows structured_output: true when enabled, false when disabled |

---

## Expected Final State

The Structured output toggle correctly persists its state (enabled/disabled) after save and reload, and the YAML field structured_output accurately reflects the toggle state.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Toggle state persists after each save/reload cycle and YAML matches.

**Fail:**
- Any step produces an error or unexpected result.
- Toggle state resets after reload, or YAML does not match the toggle state.
