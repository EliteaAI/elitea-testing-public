---
id: ELITEA-2608
title: "Subagent Skills Isolation"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:subagents, feat:autonomous-invocation]
requirements: []
---

# ELITEA-2608: Subagent Skills Isolation

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that subagents use ONLY their own attached skills (no parent skill bleed), and subagents with no skills run skill-free.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills and Agents sections are available in the project.
- Subagent functionality is available.

---

## Test Data

| Field | Value |
|-------|-------|
| Master Agent Name | `master-agent` |
| Master Skill Name | `master-formatter` |
| Master Skill Instructions | Format all output in UPPERCASE |
| Subagent 1 Name | `subagent-with-skill` |
| Subagent 1 Skill Name | `sub-formatter` |
| Subagent 1 Skill Instructions | Format all output with bullet points |
| Subagent 2 Name | `subagent-no-skills` |
| Test Prompt | "List three colors" |

---

## Steps

### Part A: Subagent Uses Only Its Own Skills

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create skill `master-formatter` with UPPERCASE formatting instructions | Skill is created |
| 2 | Create skill `sub-formatter` with bullet point formatting instructions | Skill is created |
| 3 | Create `master-agent` and attach `master-formatter` skill | Master agent created with skill |
| 4 | Create `subagent-with-skill` and attach `sub-formatter` skill (NOT master-formatter) | Subagent created with different skill |
| 5 | Configure master agent to use `subagent-with-skill` as a subagent | Subagent is linked to master |
| 6 | Open chat with master agent | Chat loads |
| 7 | Send a prompt that triggers the subagent: "Ask the subagent to list three colors" | Subagent is invoked |
| 8 | Examine the subagent's response | Response uses bullet points (sub-formatter skill) |
| 9 | Verify response is NOT in UPPERCASE | Master's skill (UPPERCASE) was NOT applied to subagent |
| 10 | Check thought process for subagent execution | Only `sub-formatter` skill is shown for subagent, NOT `master-formatter` |

### Part B: Subagent with No Skills Runs Skill-Free

| # | Action | Expected Result |
|---|--------|-----------------|
| 11 | Create `subagent-no-skills` with NO skills attached | Subagent created without skills |
| 12 | Configure master agent to also use `subagent-no-skills` | Second subagent is linked |
| 13 | Send a prompt triggering the skill-free subagent: "Ask the no-skill subagent to list three animals" | Skill-free subagent is invoked |
| 14 | Examine the response from skill-free subagent | Response is plain text, no special formatting |
| 15 | Verify response is NOT in UPPERCASE (master's skill not inherited) | No skill formatting applied |
| 16 | Check thought process | No skill invocations shown for this subagent |

---

## Expected Final State

1. Subagents use ONLY their own attached skills.
2. Parent/master agent skills do NOT bleed into subagent execution.
3. Subagents with no skills run completely skill-free.

---

## Pass/Fail Criteria

**Pass:**
- Subagent uses only its own attached skill (`sub-formatter`).
- Master's skill (`master-formatter`) is NOT applied to subagent.
- Skill-free subagent executes without any skill behavior.
- Thought process correctly shows skill isolation.

**Fail:**
- Subagent uses parent's skills (skill bleed).
- Subagent's own skill is not applied.
- Skill-free subagent somehow has skill behavior.
- Thought process shows incorrect skill attributions.
