---
id: ELITEA-2070
title: "Pipeline — Run History Panel"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2070: Pipeline — Run History Panel

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that the run history panel displays past execution entries with timestamps, allows viewing individual execution details, and can be closed.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline that has been executed at least once is open.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline that has been executed before | Pipeline is loaded |
| 2 | Click "view run history" button in chat panel header | Run history panel opens |
| 3 | Verify run history panel opens | Panel is visible |
| 4 | Verify it shows list of past executions with timestamps | Past executions are listed with timestamps |
| 5 | Click on a specific execution entry | Execution details are displayed |
| 6 | Verify execution details are shown (input message, output, status) | Input message, output response, and status are visible |
| 7 | Close run history panel | Panel closes |

---

## Expected Final State

The run history panel opens correctly, displays past executions with timestamps, shows full execution details when an entry is clicked, and can be closed.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Run history panel opens, shows executions with timestamps, details are displayed on click, and panel closes.

**Fail:**
- Any step produces an error or unexpected result.
- Panel does not open, shows no entries, details are missing, or panel cannot be closed.
