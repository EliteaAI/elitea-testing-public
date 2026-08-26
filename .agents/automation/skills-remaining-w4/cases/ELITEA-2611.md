---
id: ELITEA-2611
title: "Edit with AI — Skill Happy Path"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:edit-with-ai]
requirements: []
---

# ELITEA-2611: Edit with AI — Skill Happy Path

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify the complete "Edit with AI" workflow for skills: CTA visibility, prompt input, loading state, multi-step wizard (General → Instructions → Summary), Current vs Suggested comparison with diff highlighting, checkbox selection, and applying only accepted suggestions.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills section is available in the project.
- An existing skill exists that can be edited.

---

## Test Data

| Field | Value |
|-------|-------|
| Existing Skill Name | `edit-ai-test-skill` |
| Existing Description | Basic description for testing |
| Existing Instructions | Simple instructions to be enhanced |
| Edit Prompt | "Make this skill more detailed and professional. Add better structure to the instructions." |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to an existing skill's detail/edit page | Skill detail page loads |
| 2 | Verify "Edit with AI" CTA/button is visible | Button with magic-wand icon is present |
| 3 | Click "Edit with AI" | Edit with AI modal/wizard opens |
| 4 | Verify prompt input field is displayed | Text area for entering request is visible |
| 5 | Enter the edit prompt: "Make this skill more detailed and professional..." | Prompt text is entered |
| 6 | Click "Generate" or equivalent button | Generation starts |
| 7 | Verify loading state is displayed: "Generating skill draft…" | Loading indicator with message is shown |
| 8 | Wait for generation to complete | Suggestions are generated |
| 9 | Verify multi-step wizard appears showing first step (General: Name, Description) | Step 1 is displayed with Name and Description fields |
| 10 | Verify "Current" value is displayed (read-only) | Original values shown as non-editable |
| 11 | Verify "Suggested" value is displayed (editable) | AI suggestions shown as editable fields |
| 12 | Verify diff highlighting shows changes (added content highlighted) | Visual diff between current and suggested |
| 13 | Verify checkboxes are present and default to checked | Checkboxes are checked by default |
| 14 | Navigate to next step (Instructions) | Step 2 loads with instructions comparison |
| 15 | Verify Current vs Suggested for Instructions | Both values displayed with diff highlighting |
| 16 | UNCHECK one of the suggestions (e.g., keep original description) | Checkbox is unchecked |
| 17 | Navigate to Summary step | Summary of changes is displayed |
| 18 | Verify summary shows which changes will be applied | Only checked items are listed for application |
| 19 | Click "Apply" or "Finalize" | Changes are applied |
| 20 | Verify only the CHECKED suggestions were applied | Unchecked fields retain original values |
| 21 | Verify the skill is saved with the applied changes | Skill shows updated values |
| 22 | Reopen the skill and verify persisted changes | Changes are saved correctly |

---

## Expected Final State

1. "Edit with AI" wizard completes successfully.
2. Only accepted (checked) suggestions are applied to the skill.
3. Unchecked suggestions preserve the original values.
4. Changes are persisted after saving.

---

## Pass/Fail Criteria

**Pass:**
- "Edit with AI" CTA is visible and functional.
- Loading state displays correctly during generation.
- Multi-step wizard shows all steps (General, Instructions, Summary).
- Current vs Suggested comparison works with diff highlighting.
- Checkboxes control which suggestions are applied.
- Only checked suggestions are saved; unchecked preserve original.

**Fail:**
- "Edit with AI" CTA is missing or non-functional.
- Loading state is missing or unclear.
- Wizard steps are missing or out of order.
- Diff highlighting doesn't work.
- Unchecked suggestions are applied anyway.
- Changes are not persisted after saving.
