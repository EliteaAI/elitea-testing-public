---
id: ELITEA-2063
title: "Pipeline — Version Dropdown and Switch"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2063: Pipeline — Version Dropdown and Switch

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the version dropdown allows switching between saved pipeline versions, that each version restores the correct node topology, and that the Version ID in the Information section updates accordingly.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with multiple saved versions (including "base") exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline that has multiple versions | Pipeline is loaded with the version selector visible |
| 2 | Locate "VERSION:" label and the version combobox (e.g., showing "base") | Version combobox is visible showing "base" |
| 3 | Click the version combobox to open dropdown | Dropdown opens with all available versions listed |
| 4 | Select a different version | Selected version name appears in the combobox |
| 5 | Verify canvas updates to show the node topology of the selected version | Canvas displays the nodes/edges for the selected version |
| 6 | Verify version ID in Information section updates | Information section shows the new version's ID |
| 7 | Switch back to "base" — verify original topology is restored | Canvas restores the base version node topology |

---

## Expected Final State

Switching versions via the dropdown correctly updates the canvas to show the selected version's topology and the Version ID in the Information section updates accordingly.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Version switching updates canvas topology and Information section Version ID correctly.

**Fail:**
- Any step produces an error or unexpected result.
- Canvas does not update on version switch, or Version ID is not updated.
