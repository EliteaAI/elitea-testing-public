---
id: ELITEA-2051
title: "Pipeline — Fork"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2051: Pipeline — Fork

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a pipeline from another project can be forked into the user's own project, creating a copy with a new unique ID and a "Forked from" attribution on the dashboard card.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline from a different project is accessible (e.g., via Agent HUB or shared link).

---

## Test Data

| Field | Value |
|-------|-------|
| Target project | User's private project |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to a pipeline from a different project (e.g., via Agent HUB or shared link) | Pipeline from another project is displayed |
| 2 | Click three-dot menu → "Fork" | Fork modal opens |
| 3 | Verify a fork modal opens and fork parameters are displaying | Fork modal shows project selection and fork options |
| 4 | Select a target project (e.g., private project) and click "Fork" | Fork request is submitted |
| 5 | Verify a forked copy is created in user's own project | Forked pipeline appears in the user's project |
| 6 | Verify forked pipeline shows "Forked from" link on the dashboard card | Dashboard card shows attribution to the original pipeline |
| 7 | Verify forked pipeline has a new unique Pipeline ID | Forked pipeline ID is different from the original |

---

## Expected Final State

The pipeline is successfully forked into the user's project with a new unique ID and "Forked from" attribution displayed on the dashboard card.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Forked pipeline has a new unique ID and shows "Forked from" attribution.

**Fail:**
- Any step produces an error or unexpected result.
- Fork fails, ID is not unique, or "Forked from" attribution is missing.
