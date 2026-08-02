---
id: ELITEA-1999
title: "Build with AI from Agent — created Skill is auto-attached and user is redirected back to Agent"
priority: high
type: functional
module: agents
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:agents]
requirements: []
---

# ELITEA-1999: Build with AI from Agent — created Skill is auto-attached and user is redirected back to Agent

**Module:** agents · **Priority:** high · **Type:** functional

**Objective:** Verify that when a Skill is created via "Build with AI" from within the Agent editor, the user is redirected back to the Agent editor (not the Skill details page), the new Skill is automatically attached to the Agent, and the attachment persists after saving and re-opening the Agent.

---

## Preconditions

- User is logged in to the Elitea platform with admin or editor role.
- At least one existing Agent is available for editing.
- The Build with AI feature is accessible.

---

## Test Data

| Field | Value |
|-------|-------|
| Natural-language description | A valid description for the new Skill |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open an existing Agent for editing | The Agent editor is displayed |
| 2 | In the SKILLS section, click "+ Skill" | The skill selection dropdown or dialog opens |
| 3 | In the dropdown, select "+ Create New" | The Create New option is selected |
| 4 | Choose "Build with AI" | The Build with AI modal opens |
| 5 | Enter a natural-language description and click "Generate" | Generation is initiated and a draft is produced |
| 6 | Review the generated Name, Description, and Instructions | The review/edit form shows generated values |
| 7 | Click "Create Skill" | Skill creation is initiated |
| 8 | Verify the user is redirected back to the originating Agent editor (not to the Skill details page) | The Agent editor is displayed, not the Skill details page |
| 9 | Verify the newly created Skill is automatically attached to the Agent in the SKILLS section | The new Skill appears in the Agent's SKILLS section |
| 10 | Save the Agent and re-open it | The Agent is saved and re-opened successfully |
| 11 | Verify the attached Skill is still present and correctly linked | The Skill remains attached to the Agent after save and re-open |

---

## Expected Final State

The new Skill is created, automatically attached to the Agent, and the attachment persists after saving and re-opening the Agent. The user is on the Agent editor, not the Skill details page.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- User is redirected to Agent editor, Skill is auto-attached, and attachment persists after save.

**Fail:**
- Any step produces an error or unexpected result.
- User is redirected to Skill details page instead of Agent editor, Skill is not auto-attached, or attachment is lost after save.
