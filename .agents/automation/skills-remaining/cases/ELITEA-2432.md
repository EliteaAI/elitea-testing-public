---
id: ELITEA-2432
title: "Skill instructions — Markdown edit and preview toggle"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills]
requirements: []
---

# ELITEA-2432: Skill instructions — Markdown edit and preview toggle

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that Skill instructions — Markdown edit and preview toggle. Success is confirmed when save and re-open — verify updated instructions persist.

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
| 1 | Open an existing Skill | Target page/section loads successfully. |
| 2 | In the Instructions section, switch to Edit mode and modify the Markdown body | Action completes without error and produces the expected UI state. |
| 3 | Switch to Preview mode — verify the rendered Markdown output is correct | Action completes without error and produces the expected UI state. |
| 4 | Switch back to Edit mode — verify the raw Markdown matches what was typed | Action completes without error and produces the expected UI state. |
| 5 | Save and re-open — verify updated instructions persist | Operation completes successfully; state updates and confirmation is shown. |

---

## Expected Final State

Save and re-open — verify updated instructions persist.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- The condition described in the title holds: Skill instructions — Markdown edit and preview toggle.

**Fail:**
- Any step produces an error or unexpected result.
- Any of the expected UI states, validations, or side effects is not observed.
