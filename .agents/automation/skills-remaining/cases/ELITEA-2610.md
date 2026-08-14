---
id: ELITEA-2610
title: "Skill Version Selection Behavior"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:versioning, feat:autonomous-invocation]
requirements: []
---

# ELITEA-2610: Skill Version Selection Behavior

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that when a specific non-base skill version is attached to an agent, that version's behavior is used during invocation, and changing the attached version updates the behavior immediately.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills and Agents sections are available in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| Agent Name | `version-behavior-agent` |
| Skill Name | `response-style` |
| Base Version Instructions | Respond in a formal, professional tone |
| V2 Version Name | `casual` |
| V2 Version Instructions | Respond in a casual, friendly tone with emojis |
| V3 Version Name | `technical` |
| V3 Version Instructions | Respond with technical details and code examples |
| Test Prompt | "Explain what an API is" |

---

## Steps

### Part A: Specific Version Behavior Is Used

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create skill `response-style` with base version (formal tone) | Skill created with base version |
| 2 | Create version `casual` with casual/emoji instructions | v2 version created |
| 3 | Create version `technical` with technical instructions | v3 version created |
| 4 | Create agent `version-behavior-agent` | Agent created |
| 5 | Attach skill with `casual` version specifically selected | Skill attached with v2 (casual) version |
| 6 | Save the agent | Agent saved |
| 7 | Open chat with the agent | Chat loads |
| 8 | Send test prompt: "Explain what an API is" | Message sent |
| 9 | Verify response uses casual tone with emojis | Response matches casual version behavior |
| 10 | Verify response is NOT formal (base version behavior) | Base version behavior not applied |

### Part B: Changing Version Updates Behavior Immediately

| # | Action | Expected Result |
|---|--------|-----------------|
| 11 | Go back to agent settings | Agent settings page loads |
| 12 | Change attached skill version from `casual` to `technical` | Version selection updated |
| 13 | Save the agent | Agent saved |
| 14 | Return to chat (or start new chat) with the agent | Chat is ready |
| 15 | Send the same prompt: "Explain what an API is" | Message sent |
| 16 | Verify response now uses technical tone with code examples | Response matches technical version behavior |
| 17 | Verify response is NOT casual (previous version behavior) | Previous version behavior not applied |

### Part C: Revert to Base Version

| # | Action | Expected Result |
|---|--------|-----------------|
| 18 | Change attached skill version to `base` | Base version selected |
| 19 | Save and test again | Agent saved |
| 20 | Send the same prompt | Message sent |
| 21 | Verify response uses formal, professional tone | Response matches base version behavior |

---

## Expected Final State

1. The specific attached skill version's behavior is used during invocation.
2. Changing the attached version immediately updates the agent's behavior.
3. Version selection is respected for both autonomous and explicit invocations.

---

## Pass/Fail Criteria

**Pass:**
- Agent uses the specific attached version's behavior.
- Changing version updates behavior without requiring agent recreation.
- All version changes (casual → technical → base) work correctly.
- Version behavior is distinct and identifiable.

**Fail:**
- Agent ignores version selection and uses base/default.
- Version change requires agent recreation to take effect.
- Wrong version's behavior is applied.
- Behavior doesn't match the selected version's instructions.
