---
id: ELITEA-2065
title: "Pipeline — Tools Section — MCP Sub-tab with Tool Selection"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2065: Pipeline — Tools Section — MCP Sub-tab with Tool Selection

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that an MCP can be added to and removed from a pipeline's Tools section via the MCP sub-tab, and that the removal persists after save.

---

## Preconditions

- User is logged in to the Elitea platform.
- An existing MCP (e.g., "WebSearch") is available in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| MCP name | WebSearch |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline | Pipeline is loaded in the editor |
| 2 | In Tools section, click "+ MCP" button | MCP picker opens |
| 3 | Select an MCP from the picker (e.g., "WebSearch") | MCP is selected |
| 4 | Verify MCP appears under the "MCP" sub-tab in Tools | "WebSearch" is listed under the MCP sub-tab |
| 5 | Verify MCP shows its name and tools count or list | MCP entry displays name and tool information |
| 6 | Click on the attached MCP entry to see its tools/details | MCP details or tools list is shown |
| 7 | Remove the MCP (click X or delete icon) | MCP is removed from the Tools list |
| 8 | Verify MCP is removed from the Tools list | "WebSearch" no longer appears in the MCP sub-tab |
| 9 | Save — verify removal persists | MCP is absent from the Tools list after save |

---

## Expected Final State

An MCP can be added to the Tools section MCP sub-tab, its details viewed, and removed. The removal persists after saving.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- MCP is added to Tools, details are viewable, and removal persists after save.

**Fail:**
- Any step produces an error or unexpected result.
- MCP cannot be added, details are not shown, or removal is not saved.
