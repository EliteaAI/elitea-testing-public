---
id: ELITEA-2036
title: "Pipeline — Custom Node Configuration"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2036: Pipeline — Custom Node Configuration

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that a Custom node can be added to a pipeline and configured with its available fields, and that all configuration persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with access to the Pipelines feature.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline and add a Custom node via "Add node" → "Custom" | Custom node appears on canvas |
| 2 | Verify Custom node appears on canvas — examine config panel structure | Custom node configuration panel opens |
| 3 | Configure the Custom node fields (Type + Value for input mapping, Input, Output) | Custom node fields accept configuration values |
| 4 | Set Input and Output comboboxes with state variables | Input and Output are configured |
| 5 | Save pipeline | Pipeline saves without errors |
| 6 | Reload — verify all Custom node fields persist | All Custom node configuration is correctly restored after reload |

---

## Expected Final State

The Custom node is configured with all available fields and all configuration persists after save and reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All Custom node configuration fields persist correctly after save and reload.

**Fail:**
- Any step produces an error or unexpected result.
- Any configuration field is lost after saving.
