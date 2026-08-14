---
id: ELITEA-2056
title: "Pipeline — Information Section"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2056: Pipeline — Information Section

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Information section displays the Pipeline ID, Version ID, Trigger, and Pipeline Show link, and that the copy buttons for ID and Version ID work correctly.

---

## Preconditions

- User is logged in to the Elitea platform.
- An existing pipeline is open.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open an existing pipeline | Pipeline is loaded in the editor |
| 2 | Expand "Information" section in left panel | Information section is visible |
| 3 | Verify "Pipeline ID:" is displayed with a numeric value as a "Copy ID" button | Pipeline ID is shown with a copy button |
| 4 | Verify "Version ID:" is displayed with a numeric value as a "Copy version ID" button | Version ID is shown with a copy button |
| 5 | Verify "Trigger:" shows the trigger type (e.g., "Chat Message") | Trigger type is correctly displayed |
| 6 | Verify "Pipeline:" shows a "Show" link | "Show" link is visible |
| 7 | Click "Copy ID" button — verify pipeline ID is copied to clipboard | Pipeline ID is copied (toast or clipboard confirmation) |
| 8 | Click "Copy version ID" button — verify version ID is copied to clipboard | Version ID is copied (toast or clipboard confirmation) |
| 9 | Click "Show" link — verify it navigates to pipeline YAML or visual representation | Navigation occurs to the pipeline representation |

---

## Expected Final State

The Information section correctly displays Pipeline ID, Version ID, Trigger type, and Show link. Copy buttons for ID and Version ID work and provide user feedback.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All Information section fields are present; Copy ID and Copy Version ID buttons work.

**Fail:**
- Any step produces an error or unexpected result.
- Fields are missing, copy buttons do not work, or Show link does not navigate.
