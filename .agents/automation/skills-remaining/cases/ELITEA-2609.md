---
id: ELITEA-2609
title: "Skill Explicit and Autonomous Invocation Coexistence"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:autonomous-invocation, feat:backward-compatibility]
requirements: []
---

# ELITEA-2609: Skill Explicit and Autonomous Invocation Coexistence

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that explicit `~skill-name` invocation still works alongside autonomous invocation (backward compatibility), and that there is no double-injection when both explicit and contextual match occur simultaneously.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills and Agents sections are available in the project.

---

## Test Data

| Field | Value |
|-------|-------|
| Agent Name | `coexistence-test-agent` |
| Skill Name | `markdown-formatter` |
| Skill Instructions | Convert the user's text into properly formatted Markdown with headers and lists |
| Explicit invocation prompt | `~markdown-formatter Convert this to markdown: Title, item1, item2, item3` |
| Context-matching prompt | "Please format this as markdown: Title, item1, item2, item3" |
| Combined prompt | `~markdown-formatter Format as markdown: Title, item1, item2, item3` (explicit + context match) |

---

## Steps

### Part A: Explicit `~skill-name` Still Works (Backward Compatibility)

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create skill `markdown-formatter` with markdown formatting instructions | Skill is created |
| 2 | Create agent and attach the skill | Agent created with skill attached |
| 3 | Open chat with the agent | Chat loads |
| 4 | Send message with explicit `~markdown-formatter` syntax | Message is sent |
| 5 | Verify the skill is invoked and response is formatted as markdown | Response shows markdown formatting |
| 6 | Check thought process | `markdown-formatter` skill invocation is visible |

### Part B: No Double-Injection

| # | Action | Expected Result |
|---|--------|-----------------|
| 7 | Send a message that matches skill context AND uses explicit `~skill-name`: `~markdown-formatter Format as markdown: Title, item1, item2, item3` | Message is sent |
| 8 | Verify the response is formatted as markdown (skill applied) | Response shows proper markdown formatting |
| 9 | Check thought process for skill invocations | Skill is invoked only ONCE (not double-injected) |
| 10 | Verify the output is not duplicated or malformed | Single, clean markdown output |

### Part C: Both Methods Produce Equivalent Results

| # | Action | Expected Result |
|---|--------|-----------------|
| 11 | Send autonomous prompt (no `~`): "Please format this as markdown: Title, item1, item2, item3" | Message is sent |
| 12 | Verify skill is invoked autonomously | Response shows markdown formatting |
| 13 | Compare with explicit invocation result | Results are equivalent in quality |
| 14 | Verify both methods are valid ways to invoke skills | Both explicit and autonomous work correctly |

---

## Expected Final State

1. Explicit `~skill-name` syntax continues to work (backward compatibility maintained).
2. When both explicit invocation and context match occur, the skill is invoked only once (no double-injection).
3. Both invocation methods produce equivalent, correct results.

---

## Pass/Fail Criteria

**Pass:**
- Explicit `~skill-name` invocation works correctly.
- No double-injection when explicit + context match.
- Skill invocation count is exactly 1 in thought process for combined case.
- Both methods produce proper formatted output.

**Fail:**
- Explicit `~skill-name` syntax no longer works.
- Double-injection occurs (skill applied twice).
- Output is duplicated, malformed, or missing.
- Thought process shows multiple invocations for single request.
