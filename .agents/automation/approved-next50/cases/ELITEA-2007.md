---
id: ELITEA-2007
title: "Entry Point Node — Schedule Trigger Settings Modal"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2007: Entry Point Node — Schedule Trigger Settings Modal

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the Schedule trigger settings modal provides Default and Advanced modes with correct schedule configuration controls, that the summary updates dynamically, and that the schedule setting persists after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline exists with an entry point node and no HITL/Printer/interrupts.

---

## Test Data

| Field | Value |
|-------|-------|
| Hour | 09 |
| Minute | 30 |
| Expected summary (daily) | At 09:30, every day |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with entry point node, no HITL/Printer/interrupts | Pipeline is ready with a single entry point node |
| 2 | Select "Schedule" from Trigger dropdown | Trigger dropdown updates to "Schedule" |
| 3 | Verify "Schedule settings" modal opens with: Summary line, Mode radio (Default/Advanced), Default mode fields (Every dropdown, on dropdown, at hour:minute), Helper text, Cancel/Apply buttons | All listed elements are present and correctly displayed |
| 4 | Change "Every" to "day" — verify "on" field hides (not applicable for daily) | The "on" day-of-week field is hidden when "day" is selected |
| 5 | Change hour to "09", minute to "30" — verify summary updates (e.g., "At 09:30, every day") | Summary line updates dynamically to reflect the new schedule |
| 6 | Switch to "Advanced" mode — verify cron expression input appears | Cron expression text input is shown |
| 7 | Switch back to "Default" — verify dropdowns return | Default mode dropdowns are restored |
| 8 | Click "Apply" — verify modal closes, Trigger shows "Schedule" | Modal closes and entry point shows "Schedule" trigger |
| 9 | Save pipeline — reload — verify Schedule trigger persists | Schedule trigger is present after page reload |

---

## Expected Final State

The Schedule settings modal is fully functional: Default and Advanced modes work correctly, the summary updates dynamically, and the Schedule trigger persists after save/reload.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All schedule modal elements are present, dynamic summary updates correctly, and the trigger persists after reload.

**Fail:**
- Any step produces an error or unexpected result.
- Modal elements are missing, summary does not update, or the Schedule trigger does not persist.
