---
id: ELITEA-2038
title: "Pipeline — Agent Node Integration"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2038: Pipeline — Agent Node Integration

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that an agent can be attached to a pipeline, an Agent node added and fully configured with input/output and TASK input mapping, and that all configuration persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- An existing agent (e.g., "IssueTriageSpecialist") is available in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| Agent name | IssueTriageSpecialist |
| Input variables | normalized_issue, kb_results |
| Output variable | triage_summary |
| TASK Type | F-String |
| TASK Value | Triage this critical GitHub issue. Issue: {normalized_issue} |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline is open for editing |
| 2 | In the left panel "Tools" section, click "+ Agent" button | Agent picker opens |
| 3 | From the Agent picker, select an existing agent (e.g., "IssueTriageSpecialist") | Agent is selected |
| 4 | Verify agent appears in Tools list under Agent sub-tab | Agent is listed under the Agent sub-tab in Tools |
| 5 | Click "Add node" on canvas → select "Agent" | Agent node is added to the canvas |
| 6 | Verify Agent node panel shows: Agent dropdown, Input combobox, Output combobox, INPUT MAPPING (REQUIRED 1) with TASK section (Type+Value), Interrupt before/after switches | All listed sections are present |
| 7 | Select attached agent from "Agent" dropdown (e.g., "IssueTriageSpecialist") | Agent is selected in the dropdown |
| 8 | Set Input combobox — add state variables "normalized_issue", "kb_results" | Both variables are added to Input |
| 9 | Set Output combobox — add output variable "triage_summary" | "triage_summary" is added to Output |
| 10 | In INPUT MAPPING (REQUIRED 1) → TASK: set Type to "F-String", Value: "Triage this critical GitHub issue. Issue: {normalized_issue}" | TASK mapping is configured |
| 11 | Save pipeline | Pipeline saves without errors |
| 12 | Reload — verify Agent selection, Input, Output, and TASK mapping persist | All Agent node configuration persists after reload |

---

## Expected Final State

The Agent node is fully configured with Agent selection, Input/Output variables, and TASK input mapping, all persisting correctly after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Agent selection, Input, Output, and TASK mapping all persist after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Any Agent node field is lost after saving.
