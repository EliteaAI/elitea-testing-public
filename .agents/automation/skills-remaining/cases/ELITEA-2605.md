---
id: ELITEA-2605
title: "Skill Custom Icon Visibility Across UI"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:icon]
requirements: []
---

# ELITEA-2605: Skill Custom Icon Visibility Across UI

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that a custom skill icon is correctly displayed across all UI locations: Skills list page (CardList), Skill detail/edit page, Agent SKILLS section (SkillCard), SkillMenu dropdown (skill picker), and `~mention` autocomplete in Chat.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills and Agents sections are available in the project.
- A skill with a distinctive custom icon exists (created in prior test or setup).
- An agent exists that can have skills attached.

---

## Test Data

| Field | Value |
|-------|-------|
| Skill Name | `visible-icon-skill` |
| Custom Icon | Distinctive icon that is easily recognizable (not default) |
| Agent Name | `icon-test-agent` |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a skill with a distinctive custom icon and save it | Skill is created with custom icon |
| 2 | Navigate to the Skills list page | Skills list (CardList view) loads |
| 3 | Locate the skill in the list | Skill card is visible |
| 4 | Verify the custom icon is displayed on the skill card | Custom icon (not default) is shown on the card |
| 5 | Click on the skill to open the detail/edit page | Skill detail page loads |
| 6 | Verify the custom icon is displayed on the detail page | Custom icon is visible in the header/icon area |
| 7 | Navigate to Agents section and create or open an agent | Agent editor loads |
| 8 | Go to the SKILLS section of the agent | Skills attachment area is visible |
| 9 | Click to add/attach a skill | Skill picker/menu opens |
| 10 | Locate the skill in the SkillMenu dropdown | Skill appears in the list |
| 11 | Verify the custom icon is displayed in the SkillMenu | Custom icon is shown next to skill name in dropdown |
| 12 | Attach the skill to the agent | Skill is attached successfully |
| 13 | Verify the custom icon is displayed in the Agent's SKILLS section (SkillCard) | Custom icon is shown on the attached skill card |
| 14 | Save the agent | Agent is saved with skill attached |
| 15 | Open a chat conversation with the agent | Chat interface loads |
| 16 | Type `~` to trigger skill autocomplete | Autocomplete dropdown appears |
| 17 | Verify the custom icon is displayed in the `~mention` autocomplete | Custom icon is shown next to skill name in autocomplete |

---

## Expected Final State

The custom skill icon is consistently displayed across all UI locations where the skill appears:
- Skills list page (CardList)
- Skill detail/edit page
- Agent SKILLS section (SkillCard)
- SkillMenu dropdown (skill picker)
- `~mention` autocomplete in Chat

---

## Pass/Fail Criteria

**Pass:**
- Custom icon is visible on Skills list page cards.
- Custom icon is visible on Skill detail/edit page.
- Custom icon is visible in SkillMenu dropdown.
- Custom icon is visible in Agent's attached skills section.
- Custom icon is visible in `~mention` autocomplete.

**Fail:**
- Default icon is shown instead of custom icon in any location.
- Icon is missing entirely in any location.
- Icon appears distorted or incorrectly sized.
