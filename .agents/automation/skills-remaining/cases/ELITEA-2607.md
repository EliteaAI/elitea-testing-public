---
id: ELITEA-2607
title: "Skill Autonomous Invocation — Core Functionality"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:autonomous-invocation]
requirements: []
---

# ELITEA-2607: Skill Autonomous Invocation — Core Functionality

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that skills attached to an agent are invoked automatically based on context (without explicit `~skill-name` syntax), the invocation is visible in the thought process, and unattached skills are NEVER invoked (security invariant).

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills and Agents sections are available in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| Agent Name | `autonomous-test-agent` |
| Agent Instructions | You are a helpful assistant. Use your skills when appropriate. |
| Attached Skill Name | `code-formatter` |
| Attached Skill Instructions | When asked to format code, apply proper indentation and syntax highlighting conventions |
| Unattached Skill Name | `translator-skill` |
| Unattached Skill Instructions | Translate text to Spanish |
| Context-matching prompt | "Please format this Python code: def hello(): print('hi')" |
| Non-matching prompt | "What is the capital of France?" |

---

## Steps

### Part A: Autonomous Invocation Works

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a skill named `code-formatter` with formatting instructions | Skill is created successfully |
| 2 | Create a skill named `translator-skill` with translation instructions | Skill is created successfully |
| 3 | Create an agent and attach ONLY the `code-formatter` skill | Agent is created with one skill attached |
| 4 | Do NOT attach the `translator-skill` | Translator skill remains unattached |
| 5 | Open a chat with the agent | Chat interface loads |
| 6 | Send a message matching the attached skill's context: "Please format this Python code: def hello(): print('hi')" | Agent processes the message |
| 7 | Verify the response shows formatted code (skill was invoked) | Response demonstrates code formatting was applied |
| 8 | Open/expand the thought process panel | Thought process is visible |
| 9 | Verify the `code-formatter` skill invocation is visible in thought process | Skill invocation is logged/shown |

### Part B: Non-matching Context Does Not Invoke

| # | Action | Expected Result |
|---|--------|-----------------|
| 10 | Send a general message that doesn't match the skill context: "What is the capital of France?" | Agent processes the message |
| 11 | Verify the response is a normal answer (not code formatting related) | Response is about France's capital |
| 12 | Check thought process | No skill invocation shown for this message |

### Part C: Unattached Skills Are NEVER Invoked (Security)

| # | Action | Expected Result |
|---|--------|-----------------|
| 13 | Send a message that would match the unattached translator skill: "Translate 'hello' to Spanish" | Agent processes the message |
| 14 | Verify the response does NOT use the translator skill's behavior | Response may attempt translation but NOT using the unattached skill's specific instructions |
| 15 | Check thought process | `translator-skill` is NOT shown as invoked |
| 16 | Verify only attached skills can ever be invoked | No evidence of unattached skill usage |

---

## Expected Final State

1. Attached skills are invoked automatically when the message context matches.
2. Skill invocations are visible in the thought process for observability.
3. Unattached skills are NEVER invoked, regardless of context match (security invariant).

---

## Pass/Fail Criteria

**Pass:**
- Attached skill is invoked automatically on context match.
- Skill invocation is visible in thought process.
- Unattached skills are never invoked (security verified).
- Non-matching prompts don't trigger skill invocation.

**Fail:**
- Attached skill is not invoked despite matching context.
- Skill invocation is not visible in thought process.
- Unattached skill is invoked (security violation).
- Skills invoked inappropriately for non-matching prompts.
