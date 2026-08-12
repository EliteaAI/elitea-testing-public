---
id: ELITEA-2006
title: "Entry Point Node — Webhook Trigger Settings Modal"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2006: Entry Point Node — Webhook Trigger Settings Modal

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Webhook trigger settings modal contains all required fields and controls, that switching webhook types updates the URL and description, and that the selected configuration persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline exists with an entry point node and no HITL/Printer/interrupts.

---

## Test Data

| Field | Value |
|-------|-------|
| Webhook types | GitHub, GitLab, Custom |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with entry point node, no HITL/Printer/interrupts | Pipeline is ready with a single entry point node |
| 2 | Select "Webhook" from Trigger dropdown | Trigger dropdown updates to "Webhook" |
| 3 | Verify "Webhook settings" modal opens with: Webhook Type radio buttons (GitHub, GitLab, Custom) — GitHub selected by default; Description text; Webhook URL read-only field with copy button; Secret Value masked field with eye/copy/refresh buttons and helper text; Payload Format description; Example Request code block with copy button; Cancel/Apply buttons | All listed elements are present and correctly displayed |
| 4 | Switch Webhook Type to "GitLab" — verify URL and description text update | URL and description change to reflect GitLab-specific values |
| 5 | Switch to "Custom" — verify URL updates | URL updates to reflect Custom webhook format |
| 6 | Click "Apply" — verify modal closes, Trigger shows "Webhook" | Modal closes and entry point shows "Webhook" trigger |
| 7 | Save pipeline — reload — verify Webhook trigger persists | Webhook trigger is present after page reload |

---

## Expected Final State

The Webhook settings modal is fully functional: all UI elements are present, switching webhook types updates the URL/description, and the Webhook trigger setting persists after save/reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The modal contains all required elements, webhook type switching updates URLs, and the trigger persists after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Modal elements are missing, or the Webhook trigger does not persist after saving.
