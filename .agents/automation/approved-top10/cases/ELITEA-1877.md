---
id: ELITEA-1877
title: "Selecting a past run from history loads its messages in the chat panel"
priority: high
type: functional
module: agents
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:agents]
requirements: []
---

# ELITEA-1877: Selecting a past run from history loads its messages in the chat panel

**Module:** agents · **Priority:** high · **Type:** functional

**Objective:** Verify that clicking a past run entry in the history panel loads the correct messages for that session in the chat panel, distinct from the current/active run.

---

## Preconditions

- User is logged in to the Elitea platform.
- An agent with at least 2 distinct run history entries is available.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to an agent that has at least 2 distinct run history entries | The agent detail page loads |
| 2 | Open the run history panel | The run history panel opens with at least 2 entries listed |
| 3 | Click on a specific past run entry (not the most recent) | The selected run entry is highlighted |
| 4 | Verify the chat panel updates to show the messages from that selected run | The chat panel displays messages from the selected historical session |
| 5 | Verify the messages match the content from that historical session | The displayed messages correspond to the selected past run |
| 6 | Verify this is distinct from the current/active run | The loaded messages differ from the current/active run content |

---

## Expected Final State

The chat panel displays the messages of the selected historical run, which is visually distinct from the current active run.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Clicking a past run loads its messages correctly in the chat panel.

**Fail:**
- Any step produces an error or unexpected result.
- The chat panel does not update, shows incorrect messages, or shows the current run instead of the selected historical run.
