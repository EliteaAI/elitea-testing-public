---
id: ELITEA-2047
title: "Pipeline — Interrupt Before/After Toggles"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2047: Pipeline — Interrupt Before/After Toggles

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Interrupt before/after toggles on a node correctly pause pipeline execution at the configured point, and that execution can be resumed after the interrupt.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with a node (e.g., Code node) exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline with a node (e.g., Code node) | Pipeline is open with the node visible |
| 2 | In node config, locate "Interrupt before" switch | Interrupt before switch is visible |
| 3 | Locate "Interrupt after" switch | Interrupt after switch is visible |
| 4 | Toggle "Interrupt after" to enabled | Interrupt after switch is enabled |
| 5 | Save pipeline | Pipeline saves without errors |
| 6 | Execute the pipeline — verify execution pauses after that node | Execution pauses after the node with interrupt enabled |
| 7 | Verify interrupt state shown in UI | UI indicates pipeline is paused at the interrupt point |
| 8 | Resume execution — verify pipeline completes | Pipeline resumes and completes execution |

---

## Expected Final State

The Interrupt after toggle correctly pauses pipeline execution after the configured node. The UI shows the interrupt state and execution resumes when triggered.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Interrupt after toggle pauses execution, UI shows interrupt state, and execution resumes successfully.

**Fail:**
- Any step produces an error or unexpected result.
- Execution does not pause, interrupt state is not shown, or execution cannot resume.
