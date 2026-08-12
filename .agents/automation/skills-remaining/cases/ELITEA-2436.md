---
id: ELITEA-2436
title: "LLM model settings are configurable"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2436: LLM model settings are configurable

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that LLM model settings are configurable. Success is confirmed when switch to a reasoning model (if available) and verify reasoning effort options appear (low / medium / high).

---

## Preconditions

- User is logged in to the Elitea platform.


---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open any Skill and locate model settings in the test panel (⚙️ icon or similar) | Target page/section loads successfully. |
| 2 | Select a standard model (e.g., gpt5-mini) and adjust the reasoning slider | Control responds; expected next state is shown. |
| 3 | Run a test — verify no error occurs | Action completes without error and produces the expected UI state. |
| 4 | Switch to a reasoning model (if available) and verify reasoning effort options appear (Low / Medium / High) | Action completes without error and produces the expected UI state. |

---

## Expected Final State

Switch to a reasoning model (if available) and verify reasoning effort options appear (Low / Medium / High).

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: LLM model settings are configurable.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.
