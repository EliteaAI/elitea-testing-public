---
id: ELITEA-2612
title: "Edit with AI — Skill Navigation and Error Handling"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:edit-with-ai]
requirements: []
---

# ELITEA-2612: Edit with AI — Skill Navigation and Error Handling

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify "Edit with AI" navigation flows (back button preserves prompt, cancel preserves original), and error handling (generation failure shows error with retry, empty prompt validation).

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
| Existing Skill Name | `nav-error-test-skill` |
| Original Description | Original description that should be preserved |
| Original Instructions | Original instructions that should be preserved |
| Valid Prompt | "Improve this skill with better structure" |
| Empty Prompt | "" (empty string) |
| Whitespace Prompt | "   " (spaces only) |

---

## Steps

### Part A: Back Button Preserves Prompt

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open an existing skill and click "Edit with AI" | Wizard opens on prompt input step |
| 2 | Enter a valid prompt | Prompt text is entered |
| 3 | Click "Generate" and wait for suggestions | Suggestions are generated, wizard advances |
| 4 | Click "Back to Enter request step" or equivalent | Wizard returns to prompt input step |
| 5 | Verify the original prompt text is preserved | Prompt field contains the previously entered text |
| 6 | Verify user can modify and regenerate | User can edit prompt and generate again |

### Part B: Cancel Preserves Original Configuration

| # | Action | Expected Result |
|---|--------|-----------------|
| 7 | Generate suggestions again | Suggestions are displayed |
| 8 | Navigate through wizard steps without applying | User is on a later step |
| 9 | Click "Cancel" or close the wizard | Wizard closes |
| 10 | Verify the skill's original values are unchanged | Description and instructions are original |
| 11 | Reopen the skill | Skill loads with original values |
| 12 | Verify no changes were saved | All fields match original values |

### Part C: Generation Failure Shows Error + Retry

| # | Action | Expected Result |
|---|--------|-----------------|
| 13 | Open "Edit with AI" wizard | Wizard opens |
| 14 | Enter a valid prompt | Prompt entered |
| 15 | Trigger or simulate AI generation failure (if possible via network/API error) | Generation fails |
| 16 | Verify error message is displayed | Clear error message about generation failure |
| 17 | Verify "Retry" option is available | Retry button or option is present |
| 18 | Click Retry | Generation is attempted again |
| 19 | Verify retry can succeed | Successful generation after retry |

### Part D: Empty/Whitespace Prompt Validation

| # | Action | Expected Result |
|---|--------|-----------------|
| 20 | Open "Edit with AI" wizard | Wizard opens |
| 21 | Leave prompt field empty and try to generate | Validation error is shown |
| 22 | Verify error message indicates prompt is required | "Prompt is required" or similar message |
| 23 | Verify "Generate" button is disabled or blocked | Cannot proceed without valid prompt |
| 24 | Enter whitespace-only prompt ("   ") | Whitespace is entered |
| 25 | Try to generate | Validation error is shown |
| 26 | Verify whitespace-only is treated as empty | Same validation error as empty prompt |

---

## Expected Final State

1. Back navigation preserves the user's prompt text.
2. Cancel/dismiss at any step preserves the original skill configuration.
3. Generation failures display clear errors with retry option.
4. Empty and whitespace-only prompts are validated and blocked.

---

## Pass/Fail Criteria

**Pass:**
- Back button preserves prompt text.
- Cancel preserves original skill values.
- Generation failure shows error with retry option.
- Retry works after failure.
- Empty prompt validation blocks generation.
- Whitespace-only prompt validation blocks generation.

**Fail:**
- Back button clears the prompt.
- Cancel applies partial changes or corrupts data.
- Generation failure has no error message or retry.
- Empty/whitespace prompts can trigger generation.
