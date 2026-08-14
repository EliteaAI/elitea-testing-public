---
id: ELITEA-2008
title: "Entry Point Node — Trigger Restricted When HITL/Printer/Interrupts Present"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2008: Entry Point Node — Trigger Restricted When HITL/Printer/Interrupts Present

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that Schedule and Webhook trigger types are restricted (only Chat Message is available) when a pipeline contains HITL nodes, Printer nodes, or static interrupt configurations, and that all three trigger types become available again once those restrictions are removed.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline exists with an entry point node.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a pipeline with any entry point node and a Printer node connected after it | Pipeline has entry point node + Printer node |
| 2 | Click the entry point node | Node configuration panel opens |
| 3 | Open Trigger dropdown | Trigger dropdown opens |
| 4 | Verify only "Chat Message" is available (Schedule and Webhook do NOT appear) | Only "Chat Message" is listed in the Trigger dropdown |
| 5 | Remove Printer node, add HITL node instead — verify same restriction applies | With HITL node present, only "Chat Message" is available in Trigger dropdown |
| 6 | Remove HITL, enable "Interrupt after" on any node in pipeline — verify same restriction | With static interrupt enabled, only "Chat Message" is available |
| 7 | Remove all HITL/Printer/interrupt configurations — verify all 3 trigger types become available again | All three trigger types (Chat Message, Schedule, Webhook) are available |

---

## Expected Final State

When Printer, HITL, or static interrupts are present in a pipeline, only the "Chat Message" trigger is available on the entry point node. Removing all such configurations restores all three trigger type options.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Trigger dropdown correctly restricts to "Chat Message" when incompatible nodes/interrupts are present, and restores all options when they are removed.

**Fail:**
- Any step produces an error or unexpected result.
- Schedule/Webhook options appear when they should be restricted, or do not reappear after restrictions are removed.
