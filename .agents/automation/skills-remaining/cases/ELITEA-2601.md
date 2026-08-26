---
id: ELITEA-2601
title: "Agent with Skills — Validation Attribution and Token Invalidation"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:agents, feat:publishing, feat:validation]
requirements: []
---

# ELITEA-2601: Agent with Skills — Validation Attribution and Token Invalidation

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that when publishing an agent with attached skills: (1) validation findings are correctly attributed to the specific skill context, and (2) the publishing token is invalidated when skills are added or removed from the agent.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills and Agents sections are available in the project.
- User has publishing permissions for agents.
- Two browser tabs/windows available for testing.

---

## Test Data

| Field | Value |
|-------|-------|
| Agent Name | `validation-test-agent` |
| Valid Skill Name | `valid-skill` |
| Valid Skill Content | Description and instructions with 100+ characters each |
| Invalid Skill Name | `invalid-skill` |
| Invalid Skill Content | Short description, placeholder text like `[TODO]` |
| Additional Skill Name | `extra-skill` |

---

## Steps

### Part A: Validation Attribution to Skill Context

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a valid skill with proper content (100+ chars, no placeholders) | Skill is created successfully |
| 2 | Create an invalid skill with validation issues (short content, placeholders) | Skill is created successfully |
| 3 | Create an agent and attach both the valid and invalid skills | Agent is created with 2 skills attached |
| 4 | Open the agent publish wizard and proceed to Validation step | Validation runs on agent and all attached skills |
| 5 | Review the validation findings | Validation shows FAIL status |
| 6 | Verify the error is attributed to the specific skill with issues | Error message includes context like "skill: invalid-skill" or similar attribution |
| 7 | Verify the valid skill does not show validation errors | No errors attributed to `valid-skill` |
| 8 | Remove the invalid skill from the agent | Skill is detached from agent |
| 9 | Re-run validation | Validation now passes (only valid skill attached) |

### Part B: Token Invalidation on Skill Changes

| # | Action | Expected Result |
|---|--------|-----------------|
| 10 | With the agent having only valid skill(s), proceed through validation | Validation passes |
| 11 | Keep the publish wizard open on post-validation step | Wizard remains open |
| 12 | In a new browser tab, open the same agent | Agent editor opens |
| 13 | Add a new skill to the agent (attach `extra-skill`) | Skill is attached successfully |
| 14 | Return to the first tab with publish wizard open | Wizard is still showing |
| 15 | Attempt to proceed with publishing | Error indicates token is invalid due to skill attachment change |
| 16 | Restart validation process | New validation runs |
| 17 | After validation passes, in second tab REMOVE a skill from agent | Skill is detached |
| 18 | Attempt to publish from first tab | Error indicates token is invalid due to skill removal |

---

## Expected Final State

1. Validation errors clearly identify which skill has issues (proper attribution).
2. Publishing token is invalidated whenever skills are added or removed from the agent.
3. Users must re-validate after any skill attachment changes.

---

## Pass/Fail Criteria

**Pass:**
- Validation errors show correct skill attribution (context: skill: <name>).
- Token invalidation triggers on skill addition.
- Token invalidation triggers on skill removal.
- Re-validation is required after skill changes.

**Fail:**
- Validation errors don't identify the problematic skill.
- Publishing succeeds despite skill changes after validation.
- Token remains valid after skill attachment modifications.
