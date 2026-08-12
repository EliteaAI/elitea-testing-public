---
id: ELITEA-2614
title: "Published Agent Version Cannot Be Modified"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:agents, feat:publishing, feat:immutability]
requirements: []
---

# ELITEA-2614: Published Agent Version Cannot Be Modified

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that published agent versions are immutable: modifications to name, description, instructions, tags, and skill attachments are blocked with appropriate error messages. Unpublishing restores the ability to edit.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills and Agents sections are available in the project.
- User has publishing permissions.

---

## Test Data

| Field | Value |
|-------|-------|
| Agent Name | `immutable-test-agent` |
| Agent Description | Original description for immutability testing |
| Agent Instructions | Original instructions |
| Agent Tags | `test-tag` |
| Attached Skill Name | `immutable-skill` |
| Modified Description | Attempted modification to description |
| Modified Instructions | Attempted modification to instructions |
| Error Message | "Version is published and cannot be updated" |
| Tooltip Message | "This agent version is published and can not be modified" |

---

## Steps

### Part A: Setup — Publish Agent with Skill

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a skill (`immutable-skill`) | Skill created |
| 2 | Create an agent with name, description, instructions, and tags | Agent created |
| 3 | Attach the skill to the agent | Skill attached |
| 4 | Publish the agent | Agent is published successfully |
| 5 | Verify the agent shows as published | Published badge/indicator visible |

### Part B: Attempt to Modify Published Version

| # | Action | Expected Result |
|---|--------|-----------------|
| 6 | Attempt to edit the agent's name | Edit is blocked or shows error |
| 7 | Verify error toast: "Version is published and cannot be updated" | Error toast appears |
| 8 | Attempt to edit the agent's description | Edit is blocked or shows error |
| 9 | Verify same error message | Error toast appears |
| 10 | Attempt to edit the agent's instructions | Edit is blocked or shows error |
| 11 | Verify same error message | Error toast appears |
| 12 | Attempt to modify tags (add or remove) | Edit is blocked or shows error |
| 13 | Verify same error message | Error toast appears |

### Part C: Attempt to Modify Skill Attachments

| # | Action | Expected Result |
|---|--------|-----------------|
| 14 | Attempt to add a new skill to the published agent | Action is blocked |
| 15 | Verify error message or disabled state | Error or button disabled |
| 16 | Attempt to remove the attached skill | Action is blocked |
| 17 | Verify error message or disabled state | Error or button disabled |
| 18 | Attempt to change the attached skill's version | Action is blocked |
| 19 | Verify error message or disabled state | Error or button disabled |
| 20 | Hover over disabled controls | Tooltip shows: "This agent version is published and can not be modified" |

### Part D: Unpublish Restores Editability

| # | Action | Expected Result |
|---|--------|-----------------|
| 21 | Unpublish the agent | Agent is unpublished successfully |
| 22 | Attempt to edit the agent's name | Edit is now allowed |
| 23 | Attempt to edit description | Edit is now allowed |
| 24 | Attempt to add/remove skills | Skill modifications are now allowed |
| 25 | Save changes | Changes are saved successfully |

---

## Expected Final State

1. Published agent versions are fully immutable (name, description, instructions, tags, skills).
2. All modification attempts show clear error messages.
3. Disabled controls show explanatory tooltips.
4. Unpublishing restores full editability.

---

## Pass/Fail Criteria

**Pass:**
- All modification attempts on published version are blocked.
- Error toast "Version is published and cannot be updated" appears.
- Tooltip explains immutability on disabled controls.
- Unpublishing restores all edit capabilities.

**Fail:**
- Any modification succeeds on a published version.
- Error messages are missing or unclear.
- Tooltips are missing on disabled controls.
- Unpublishing doesn't restore editability.
