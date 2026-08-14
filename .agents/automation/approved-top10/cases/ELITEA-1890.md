---
id: ELITEA-1890
title: "Switching between versions updates form fields correctly"
priority: critical
type: functional
module: agents
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:agents]
requirements: []
---

# ELITEA-1890: Switching between versions updates form fields correctly

**Module:** agents · **Priority:** high · **Type:** functional

**Objective:** Verify that switching between agent versions updates the form fields (in particular Instructions) to reflect the selected version's content, and that switching back restores the original content.

---

## Preconditions

- User is logged in to the Elitea platform.
- An agent with at least 2 versions (base + named version) exists, with distinct Instructions in each version.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to an agent that has at least 2 versions (base + named version) with distinct instructions | The agent detail page loads |
| 2 | Note the active version and its Instructions content | The current version name and Instructions text are recorded |
| 3 | Open the version dropdown and select the other version | The version is switched |
| 4 | Verify the Instructions field updates to reflect the selected version's content | The Instructions field shows the content of the newly selected version |
| 5 | Switch back to the original version | The original version is re-selected |
| 6 | Verify the Instructions field returns to the original version's content | The Instructions field shows the original version's content |

---

## Expected Final State

Switching versions correctly updates form fields to match each version's content; switching back restores the previous version's content.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The Instructions field updates correctly when switching between versions in both directions.

**Fail:**
- Any step produces an error or unexpected result.
- The Instructions field does not update when switching versions, or shows incorrect content.
