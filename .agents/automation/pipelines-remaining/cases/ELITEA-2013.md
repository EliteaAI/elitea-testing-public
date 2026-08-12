---
id: ELITEA-2013
title: "Pipeline Tags — Add and Filter"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2013: Pipeline Tags — Add and Filter

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that pipelines can be tagged during creation and that the Pipelines dashboard tag filter correctly narrows the list to only matching pipelines.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with access to the Pipelines feature.

---

## Test Data

| Field | Value |
|-------|-------|
| Pipeline 1 name | tagged_pipe_1 |
| Pipeline 1 tags | regression, smoke |
| Pipeline 2 name | tagged_pipe_2 |
| Pipeline 2 tags | regression, integration |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create pipeline "tagged_pipe_1" with tags ["regression", "smoke"] | Pipeline is created with both tags |
| 2 | Create pipeline "tagged_pipe_2" with tags ["regression", "integration"] | Pipeline is created with both tags |
| 3 | Navigate to Pipelines dashboard | Dashboard loads with all pipelines visible |
| 4 | Filter by tag "smoke" — verify only "tagged_pipe_1" appears | Only "tagged_pipe_1" is shown in the filtered results |
| 5 | Filter by tag "regression" — verify both pipelines appear | Both "tagged_pipe_1" and "tagged_pipe_2" are shown |
| 6 | Remove tag filter — verify all pipelines are listed | All pipelines are visible without filtering |

---

## Expected Final State

Tag filtering on the Pipelines dashboard correctly shows only pipelines matching the selected tag. Removing the filter restores the full pipeline list.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Tag filters correctly include/exclude pipelines based on their tags.

**Fail:**
- Any step produces an error or unexpected result.
- Tag filter shows incorrect pipelines or fails to filter the list.
