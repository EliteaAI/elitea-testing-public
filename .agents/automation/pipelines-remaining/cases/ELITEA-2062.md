---
id: ELITEA-2062
title: "Pipeline — Multiple Tabs"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2062: Pipeline — Multiple Tabs

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that multiple pipelines can be open simultaneously as tabs, that switching between tabs correctly restores each pipeline, and that individual tabs can be closed without affecting others.

---

## Preconditions

- User is logged in to the Elitea platform.
- At least two different pipelines are available in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| Pipeline 2 name | MCPNode (or any second pipeline) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline — verify tab shows "Pipeline: <PipelineName> - <Project Name>" in the tablist | Tab is labeled with pipeline name and project name |
| 2 | Navigate back to dashboard without closing the tab | Dashboard loads; pipeline tab remains in tablist |
| 3 | Open a different pipeline (e.g., "MCPNode") | Second pipeline opens |
| 4 | Verify second tab appears in the tablist alongside first | Both pipeline tabs are visible in the tablist |
| 5 | Click the first tab — verify it switches back to that pipeline | First pipeline is loaded when its tab is clicked |
| 6 | Click the close button (X) on one tab — verify it closes and the other remains | Closed tab is removed; the other tab remains open |

---

## Expected Final State

Multiple pipeline tabs coexist in the tablist. Switching between tabs correctly loads each pipeline. Closing a tab removes only that tab while others remain.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Multiple tabs work correctly: switching loads correct pipeline, closing removes only that tab.

**Fail:**
- Any step produces an error or unexpected result.
- Tabs do not switch correctly, or closing one tab affects others.
