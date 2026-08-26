---
id: ELITEA-2003
title: "Delete Pipeline Version"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2003: Delete Pipeline Version

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that a non-base pipeline version can be deleted via the three-dot menu and that the pipeline correctly falls back to the base version after deletion.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline exists with at least one non-base saved version.

---

## Test Data

| Field | Value |
|-------|-------|
| Version name to delete | ver_to_delete |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline and save a non-base version "ver_to_delete" | Version "ver_to_delete" appears in the VERSION dropdown |
| 2 | Switch to "ver_to_delete" version | Canvas updates to show "ver_to_delete" content |
| 3 | Open three-dot menu and click "Delete version" | Delete version confirmation dialog opens |
| 4 | Confirm deletion in the dialog | Deletion request is submitted |
| 5 | Verify version is removed from dropdown | "ver_to_delete" no longer appears in the VERSION dropdown |
| 6 | Verify pipeline falls back to "base" version | VERSION dropdown shows "base" and canvas displays base state |

---

## Expected Final State

The "ver_to_delete" version is permanently removed from the pipeline. The pipeline reverts to and displays the "base" version.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- "ver_to_delete" is removed from the dropdown and the pipeline falls back to "base" version.

**Fail:**
- Any step produces an error or unexpected result.
- The version is not removed from the dropdown, or the pipeline does not fall back to "base".
