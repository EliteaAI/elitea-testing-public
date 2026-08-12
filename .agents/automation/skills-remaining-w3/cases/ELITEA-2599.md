---
id: ELITEA-2599
title: "Skill Unpublish and Republish Lifecycle"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:publishing]
requirements: []
---

# ELITEA-2599: Skill Unpublish and Republish Lifecycle

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify the complete unpublish and republish lifecycle: unpublishing removes the skill from the Catalog immediately, EntitySkillMapping is preserved (agents keep working), republishing works correctly, and up to 3 published versions can coexist with only the latest shown in Catalog.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills section is available in the project.
- An agent exists that can have skills attached.
- User has publishing permissions.

---

## Test Data

| Field | Value |
|-------|-------|
| Skill Name | `lifecycle-test-skill` |
| Version 1 Name | `v1.0` |
| Version 2 Name | `v2.0` |
| Version 3 Name | `v3.0` |
| Agent Name | `skill-consumer-agent` |

---

## Steps

### Part A: Unpublish Behavior

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a skill with valid content and publish it as v1.0 | Skill is published and appears in Catalog |
| 2 | Create an agent and attach the published skill to it | Skill is attached to agent successfully |
| 3 | Test the agent to verify the skill works | Agent uses the skill correctly |
| 4 | Navigate to the skill and click "Unpublish" | Unpublish confirmation dialog appears |
| 5 | Confirm unpublish action | Skill is unpublished successfully |
| 6 | Navigate to Skills Studio/Catalog | Skill is NO longer visible in the Catalog (removed immediately) |
| 7 | Navigate back to the agent that had the skill attached | Agent still has the skill attachment reference |
| 8 | Test the agent again | Agent still works with the skill (EntitySkillMapping preserved) |

### Part B: Republish and Version Coexistence

| # | Action | Expected Result |
|---|--------|-----------------|
| 9 | Navigate to the unpublished skill | Skill is accessible in project Skills section |
| 10 | Publish the skill again as v2.0 | Skill is published successfully as v2.0 |
| 11 | Verify v2.0 appears in Catalog | v2.0 is visible in Skills Studio/Catalog |
| 12 | Make minor changes to the skill and publish as v3.0 | Skill is published successfully as v3.0 |
| 13 | Navigate to the Catalog and search for the skill | Only the LATEST version (v3.0) is displayed |
| 14 | Verify that up to 3 versions can coexist internally | Version history shows v1.0, v2.0, v3.0 available |
| 15 | If a 4th version is published, verify oldest is handled appropriately | System handles version limit according to spec |

---

## Expected Final State

1. Unpublished skills are immediately removed from the Catalog.
2. Agents with attached skills continue to work after unpublish (EntitySkillMapping preserved).
3. Skills can be republished after unpublishing.
4. Up to 3 published versions coexist, but only the latest is shown in the Catalog.

---

## Pass/Fail Criteria

**Pass:**
- Unpublish removes skill from Catalog immediately.
- Agent continues working with attached skill after unpublish.
- Republish workflow completes successfully.
- Only latest version shown in Catalog.
- Version coexistence works as specified.

**Fail:**
- Skill remains visible in Catalog after unpublish.
- Agent breaks or loses skill attachment after unpublish.
- Republish fails or requires recreation of skill.
- Multiple versions incorrectly shown in Catalog.
