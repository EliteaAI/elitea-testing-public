---
id: ELITEA-2005
title: "Entry Point Node — Trigger Types (Chat Message, Schedule, Webhook)"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2005: Entry Point Node — Trigger Types (Chat Message, Schedule, Webhook)

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that the entry point node exposes all three trigger types (Chat Message, Schedule, Webhook) and that selecting each trigger type persists correctly after save and reload.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline exists with a single entry point node (no HITL/Printer/interrupts).

---

## Test Data

| Field | Value |
|-------|-------|
| Trigger options | Chat Message, Schedule, Webhook |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with a single entry point node (no HITL/Printer/interrupts) | Pipeline is created with one node |
| 2 | Click on the entry point node — locate "Trigger" dropdown (shows "Chat Message" by default) | Trigger dropdown is visible and defaults to "Chat Message" |
| 3 | Open Trigger dropdown — verify 3 options appear: "Chat Message", "Schedule", "Webhook" | All three options are listed in the dropdown |
| 4 | Select and Apply "Webhook" — verify dropdown updates to "Webhook" with default webhook settings | Dropdown shows "Webhook" and webhook settings appear |
| 5 | Save pipeline — reload — verify Trigger shows "Webhook" | Webhook trigger is persisted after reload |
| 6 | Select and Apply "Schedule" — verify dropdown updates to "Schedule" with default schedule settings | Dropdown shows "Schedule" and schedule settings appear |
| 7 | Save pipeline — reload — verify Trigger shows "Schedule" | Schedule trigger is persisted after reload |
| 8 | Switch back to "Chat Message" | Dropdown returns to "Chat Message" |
| 9 | Repeat with a different node type as entry point (e.g., Code node) — verify Trigger dropdown still appears with all 3 options | All 3 trigger types are available regardless of entry point node type |

---

## Expected Final State

The entry point node supports all three trigger types (Chat Message, Schedule, Webhook), each persists after save/reload, and the trigger dropdown is available for any node type used as entry point.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All three trigger types are selectable and persist correctly after save and reload.

**Fail:**
- Any step produces an error or unexpected result.
- A trigger type is missing, or the selected trigger does not persist after saving.
